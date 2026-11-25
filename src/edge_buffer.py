"""Local research edge queue; no hardware driver or production security."""
import argparse
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from src.telemetry_contract import validate_batch

MAX_BYTES = 1024 * 1024
MAX_PENDING = 1000


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS pending (id INTEGER PRIMARY KEY AUTOINCREMENT, digest TEXT NOT NULL UNIQUE, payload BLOB NOT NULL)")
        db.commit()
        return db
    except BaseException:
        db.close()
        raise


def canonical_batch(payload):
    clean = validate_batch(payload)
    data = json.dumps({"schema_version": 1, "records": clean["records"]},
                      sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if len(data) > MAX_BYTES:
        raise ValueError("Normalized batch exceeds API size limit")
    return data


def enqueue(path, payload):
    data = canonical_batch(payload)
    digest = hashlib.sha256(data).hexdigest()
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM pending WHERE digest=?", (digest,)).fetchone():
            return {"queued": False, "duplicate_pending": True, "digest": digest}
        if db.execute("SELECT COUNT(*) FROM pending").fetchone()[0] >= MAX_PENDING:
            raise ValueError("Queue full; no data discarded")
        db.execute("INSERT INTO pending(digest,payload) VALUES (?,?)", (digest, data))
    return {"queued": True, "duplicate_pending": False, "digest": digest}


def status(path):
    with closing(connect(path)) as db:
        count, size = db.execute("SELECT COUNT(*),COALESCE(SUM(length(payload)),0) FROM pending").fetchone()
    return {"pending_batches": count, "pending_bytes": size, "capacity_batches": MAX_PENDING}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def local_endpoint(base):
    parts = urlsplit(base)
    if (parts.scheme != "http" or parts.hostname not in {"127.0.0.1", "::1"}
            or parts.username is not None or parts.password is not None
            or parts.path not in {"", "/"} or parts.query or parts.fragment):
        raise ValueError("Only explicit loopback HTTP API endpoints are supported")
    if parts.port is None:
        raise ValueError("An explicit port is required")
    return base.rstrip("/") + "/v1/telemetry/ingest"


def drain(path, base="http://127.0.0.1:8080", limit=100):
    """Stop on first failed/ambiguous response; retry safely via server idempotency."""
    if type(limit) is not int or not 1 <= limit <= MAX_PENDING:
        raise ValueError("Invalid drain limit")
    url = local_endpoint(base)
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("AERIS_API_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    opener = build_opener(NoRedirect())
    delivered = 0
    blocked = None
    with closing(connect(path)) as db:
        for _ in range(limit):
            row = db.execute("SELECT id,payload FROM pending ORDER BY id LIMIT 1").fetchone()
            if row is None:
                break
            ident, data = row
            count = len(json.loads(data)["records"])
            try:
                req = Request(url, data=data, headers=headers, method="POST")
                with opener.open(req, timeout=10) as response:
                    raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise ValueError("Response exceeds limit")
                    result = json.loads(raw)
                if (not isinstance(result, dict) or result.get("status") != "stored"
                        or result.get("persisted") is not True
                        or type(result.get("inserted")) is not int
                        or type(result.get("duplicates")) is not int
                        or min(result["inserted"], result["duplicates"]) < 0
                        or result["inserted"] + result["duplicates"] != count):
                    raise ValueError("Unconfirmed ingestion")
            except HTTPError as exc:
                blocked = f"http_{exc.code}"
                exc.close()
                break
            except (URLError, OSError, ValueError):
                blocked = "unconfirmed_delivery"
                break
            with db:
                removed = db.execute("DELETE FROM pending WHERE id=?", (ident,)).rowcount
            delivered += removed
    return {"delivered_batches": delivered, "blocked": blocked, **status(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("enqueue")
    add.add_argument("file", type=Path)
    send = sub.add_parser("drain")
    send.add_argument("--url", default="http://127.0.0.1:8080")
    send.add_argument("--limit", type=int, default=100)
    sub.add_parser("status")
    args = parser.parse_args()
    if args.command == "enqueue":
        with args.file.open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            parser.error("Input exceeds size limit")
        result = enqueue(args.queue, json.loads(raw, object_pairs_hook=unique_keys))
    elif args.command == "drain":
        result = drain(args.queue, args.url, args.limit)
    else:
        result = status(args.queue)
    print(json.dumps(result, indent=2))
    return 1 if result.get("blocked") else 0


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


if __name__ == "__main__":
    raise SystemExit(main())
