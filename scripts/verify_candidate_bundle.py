"""Offline verification of revision-scoped next-candidate package contents.

Checks byte integrity and internal provenance, not publication, authenticity,
successful workflow execution, or scientific correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

REVISION=re.compile(r"[0-9a-f]{40}")
SHA256=re.compile(r"[0-9a-f]{64}")
LIMIT=128*1024*1024
REQUIRED_SOURCE={"VERSION","app.py","research/evidence/manifest.json","research/technical_report.py"}


def sha256(path):
    h=hashlib.sha256()
    total=0
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):
            total+=len(chunk)
            if total>LIMIT:
                raise ValueError("Candidate payload exceeds size limit")
            h.update(chunk)
    return h.hexdigest()


def regular(root,name):
    path=root/name
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or nonregular candidate file: {name}")
    return path


def archive_members(path,prefix):
    names=set()
    total=0
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name=entry.filename
            p=PurePosixPath(name)
            mode=entry.external_attr>>16
            if (p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name
                    or not p.parts or p.parts[0]!=prefix
                    or stat.S_ISLNK(mode) or name in names):
                raise ValueError("Unsafe or duplicate candidate archive member")
            names.add(name)
            total+=entry.file_size
            if total>LIMIT:
                raise ValueError("Unpacked archive exceeds size limit")
        if any(f"{prefix}/{n}" not in names for n in REQUIRED_SOURCE):
            raise ValueError("Candidate archive missing required source")
        if archive.testzip() is not None:
            raise ValueError("Candidate archive CRC verification failed")
    return len(names)


def verify_bundle(directory,expected_revision=None):
    root=Path(directory)
    revision=regular(root,"revision.txt").read_text(encoding="ascii").strip()
    if not REVISION.fullmatch(revision) or (expected_revision is not None and revision!=expected_revision):
        raise ValueError("Candidate revision mismatch")
    name=f"aeris-candidate-{revision[:12]}.zip"
    required={name,"AERIS_technical_report.md","revision.txt","environment.txt","readiness.json"}
    checksum=regular(root,"SHA256SUMS")
    if checksum.stat().st_size>4096:
        raise ValueError("Invalid checksum manifest size")
    entries={}
    for line in checksum.read_text(encoding="ascii").splitlines():
        parts=line.split("  ")
        if len(parts)!=2 or not SHA256.fullmatch(parts[0]) or parts[1] not in required or parts[1] in entries:
            raise ValueError("Invalid checksum entry")
        entries[parts[1]]=parts[0]
    if set(entries)!=required:
        raise ValueError("Incomplete checksum manifest")
    if {p.name for p in root.iterdir()}!=required|{"SHA256SUMS"}:
        raise ValueError("Unexpected bundle contents")
    for file,digest in entries.items():
        if sha256(regular(root,file))!=digest:
            raise ValueError(f"Candidate checksum mismatch: {file}")
    readiness=json.loads(regular(root,"readiness.json").read_text(encoding="utf-8"))
    if (readiness.get("scope")!="preflight_only_not_release_acceptance"
            or readiness.get("revision")!=revision
            or readiness.get("publication_authorized") is not False
            or readiness.get("evidence_gate") is not True
            or readiness.get("report_sha256")!=entries["AERIS_technical_report.md"]):
        raise ValueError("Candidate readiness provenance mismatch")
    count=archive_members(root/name,f"aeris-candidate-{revision[:12]}")
    return {"scope":"offline_candidate_integrity_only_not_acceptance_or_authenticity",
            "revision":revision,"verified_files":len(entries),"source_archive_members":count,
            "source_zip_sha256":entries[name],"report_sha256":entries["AERIS_technical_report.md"],
            "registered_evidence":readiness["registered_evidence"],
            "publication_authorized":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory",type=Path)
    p.add_argument("--expected-revision")
    args=p.parse_args()
    print(json.dumps(verify_bundle(args.directory,args.expected_revision),indent=2))
