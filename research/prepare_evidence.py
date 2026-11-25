"""Prepare a new evidence report and matching manifest in a separate directory.

Review and commit both generated files atomically. Never changes registered evidence.
This validates publication structure, not the truth of the experimental claims.
"""
import argparse
import json
from pathlib import Path
import re

from research.verify_evidence import ROOT, SHA1, blob_sha, parse, verify

REPO = "https://github.com/sanketnichit/aeris-machine-health-intelligence"
DIGEST = re.compile(r"[a-f0-9]{64}")
NAME = re.compile(r"[a-z0-9_]+\.json")


def prepare(report_path, name, run_id, artifact_id, digest, attribution, output, root=ROOT):
    root, output = Path(root), Path(output)
    if not NAME.fullmatch(name) or name == "manifest.json":
        raise ValueError("Invalid evidence filename")
    if type(run_id) is not int or run_id <= 0 or type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("Invalid run or artifact ID")
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise ValueError("Invalid artifact SHA256")
    if not isinstance(attribution, str) or not attribution.strip():
        raise ValueError("Missing attribution")
    verify(root)
    manifest = parse((root / "manifest.json").read_bytes())
    if name in manifest["files"] or (root / name).exists():
        raise ValueError("Registered evidence cannot be overwritten")
    report = parse(Path(report_path).read_bytes())
    if not isinstance(report, dict) or not isinstance(report.get("revision"), str) or not SHA1.fullmatch(report["revision"]):
        raise ValueError("Missing or invalid revision")
    if not isinstance(report.get("scope"), str) or not report["scope"].strip():
        raise ValueError("Missing scope")
    run = f"{REPO}/actions/runs/{run_id}"
    metadata = {"run_url": run, "full_artifact_url": f"{run}/artifacts/{artifact_id}",
                "artifact_sha256": digest, "data_attribution": attribution}
    for key, value in metadata.items():
        if key in report and report[key] != value:
            raise ValueError(f"Conflicting metadata: {key}")
        report[key] = value
    payload = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode("utf-8")
    manifest["files"][name] = {"blob_sha": blob_sha(payload), "bytes": len(payload)}
    # Output must be new, so a failed or repeated invocation cannot replace an existing bundle.
    output.mkdir(parents=False, exist_ok=False)
    (output / name).write_bytes(payload)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest["files"][name]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-sha256", required=True)
    parser.add_argument("--attribution", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.report, args.name, args.run_id, args.artifact_id,
                             args.artifact_sha256, args.attribution, args.output), indent=2))
