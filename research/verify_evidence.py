"""Verify published evidence against the registered Git blob manifest."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "evidence"
RUN = re.compile(r"https://github\.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/[0-9]+")
SHA1 = re.compile(r"[a-f0-9]{40}")


def blob_sha(payload):
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Nonfinite JSON value: {value}")


def parse(payload):
    return json.loads(payload, object_pairs_hook=unique_object, parse_constant=reject_constant)


def verify(root=ROOT):
    root = Path(root)
    manifest = parse((root / "manifest.json").read_bytes())
    if manifest["schema_version"] != 1 or manifest["hash_algorithm"] != "git-blob-sha1":
        raise ValueError("Unsupported manifest")
    entries = manifest["files"]
    if not entries:
        raise ValueError("Empty evidence manifest")
    verified = []
    for name, expected in sorted(entries.items()):
        if Path(name).name != name or not name.endswith(".json") or name == "manifest.json":
            raise ValueError(f"Invalid evidence path: {name}")
        path = root / name
        if path.is_symlink():
            raise ValueError(f"Symlink not permitted: {name}")
        payload = path.read_bytes()
        if len(payload) != expected["bytes"] or blob_sha(payload) != expected["blob_sha"]:
            raise ValueError(f"Evidence fingerprint mismatch: {name}")
        report = parse(payload)
        if not RUN.fullmatch(report.get("run_url", "")) or not SHA1.fullmatch(report.get("revision", "")):
            raise ValueError(f"Missing run or revision provenance: {name}")
        if not isinstance(report.get("scope"), str) or not report["scope"].strip():
            raise ValueError(f"Missing scope: {name}")
        verified.append({"file": name, "blob_sha": expected["blob_sha"], "run_url": report["run_url"],
                         "revision": report["revision"]})
    unregistered = sorted(p.name for p in root.glob("*.json")
                          if p.name != "manifest.json" and p.name not in entries)
    if unregistered:
        raise ValueError(f"Unregistered evidence: {unregistered}")
    return verified


if __name__ == "__main__":
    print(json.dumps({"verified": verify()}, indent=2))
