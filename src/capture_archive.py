"""Local capture provenance archive; hashes detect corruption, not authenticity."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from src.vibration_acquisition import analyze_capture, MAX_CAPTURE_BYTES, queue_capture

ARCHIVE_VERSION = 1
MAX_CAPTURES = 100
MAX_STORAGE_BYTES = 64 * 1024 * 1024
CAPTURE_ID = re.compile(r"[0-9a-f]{64}")


def connect(path):
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS captures (
            capture_id TEXT PRIMARY KEY, raw BLOB NOT NULL, report BLOB NOT NULL
        )""")
        db.commit()
        return db
    except BaseException:
        db.close()
        raise


def connect_readonly(path):
    """Open an existing archive without creating or modifying it."""
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=10)


def report_bytes(analysis):
    return json.dumps({"archive_version": ARCHIVE_VERSION, "analysis": analysis},
                      sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def identifier(raw, report):
    # Both immutable byte sequences participate in the identity; no filename or path.
    return hashlib.sha256(hashlib.sha256(raw).digest() + hashlib.sha256(report).digest()).hexdigest()


def verify_row(capture_id, raw, report):
    if identifier(raw, report) != capture_id:
        raise ValueError("Capture archive integrity check failed")
    envelope = json.loads(report)
    if not isinstance(envelope, dict) or envelope.get("archive_version") != ARCHIVE_VERSION:
        raise ValueError("Unsupported capture archive version")
    analysis = envelope["analysis"]
    if analysis["capture_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("Raw capture hash mismatch")
    return analysis


def archive_capture(path, raw, **settings):
    """Analyze original bytes, then atomically retain raw bytes and canonical report."""
    analysis = analyze_capture(raw, **settings)
    report = report_bytes(analysis)
    ident = identifier(raw, report)
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute("SELECT raw,report FROM captures WHERE capture_id=?", (ident,)).fetchone()
        if existing is not None:
            verify_row(ident, *existing)
            return {"capture_id": ident, "created": False, "analysis": analysis}
        count, used = db.execute("SELECT COUNT(*),COALESCE(SUM(length(raw)+length(report)),0) FROM captures").fetchone()
        if count >= MAX_CAPTURES or used + len(raw) + len(report) > MAX_STORAGE_BYTES:
            raise ValueError("Capture archive full; no existing captures deleted")
        db.execute("INSERT INTO captures(capture_id,raw,report) VALUES (?,?,?)", (ident, raw, report))
    return {"capture_id": ident, "created": True, "analysis": analysis}


def load_capture(path, capture_id):
    if not isinstance(capture_id, str) or not CAPTURE_ID.fullmatch(capture_id):
        raise ValueError("Invalid capture identifier")
    with closing(connect_readonly(path)) as db:
        row = db.execute("SELECT raw,report FROM captures WHERE capture_id=?", (capture_id,)).fetchone()
    if row is None:
        raise ValueError("Unknown capture identifier")
    raw, report = row
    return raw, verify_row(capture_id, raw, report)


def list_captures(path):
    with closing(connect_readonly(path)) as db:
        rows = db.execute("SELECT capture_id,raw,report FROM captures ORDER BY capture_id").fetchall()
    result = []
    for ident, raw, report in rows:
        analysis = verify_row(ident, raw, report)
        result.append({"capture_id": ident, "capture_sha256": analysis["capture_sha256"],
                       "asset_id": analysis["asset_id"], "start_utc": analysis["start_utc"],
                       "sample_count": analysis["sample_count"], "window_count": analysis["window_count"],
                       "flagged_windows": analysis["flagged_windows"],
                       "eligible_for_queue": analysis["eligible_for_queue"],
                       "payload_bytes": len(raw) + len(report)})
    return result


def stage_capture(path, capture_id, queue):
    if Path(path).resolve() == Path(queue).resolve():
        raise ValueError("Archive and edge queue must be separate files")
    raw, analysis = load_capture(path, capture_id)
    # A saved analysis is a historical artifact. Do not silently rerun it with
    # a later algorithm; queue the exact preserved batch after integrity checks.
    return {"capture_id": capture_id, "queue_result": queue_capture(queue, analysis)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("capture", type=Path)
    add.add_argument("--asset", required=True)
    add.add_argument("--start", required=True)
    add.add_argument("--rate", type=int, required=True)
    add.add_argument("--window", type=int, required=True)
    add.add_argument("--unit", choices=("m/s2", "g"), required=True)
    add.add_argument("--clip-limit", type=float)
    add.add_argument("--spectrum", action="store_true")
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("capture_id")
    stage = sub.add_parser("stage")
    stage.add_argument("capture_id")
    stage.add_argument("--queue", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "add":
            with args.capture.open("rb") as source:
                raw = source.read(MAX_CAPTURE_BYTES + 1)
            result = archive_capture(args.archive, raw, asset_id=args.asset, start=args.start,
                                     sample_rate_hz=args.rate, window_samples=args.window,
                                     unit=args.unit, clipping_limit=args.clip_limit, spectrum=args.spectrum)
        elif args.command == "list":
            result = list_captures(args.archive)
        elif args.command == "show":
            _, analysis = load_capture(args.archive, args.capture_id)
            result = {"capture_id": args.capture_id, "analysis": analysis}
        else:
            result = stage_capture(args.archive, args.capture_id, args.queue)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
