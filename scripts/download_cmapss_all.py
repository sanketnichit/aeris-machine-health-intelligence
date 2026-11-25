"""Acquire all four NASA C-MAPSS subsets from the previously pinned archive."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

from scripts.download_cmapss import URL, MAX_BYTES
from research.cmapss_official import HASHES

ARCHIVE_SHA256 = "74bef434a34db25c7bf72e668ea4cd52afe5f2cf8e44367c55a82bfd91a5a34f"
SUBSETS = ("FD001","FD002","FD003","FD004")
NAMES = tuple(f"{prefix}_{subset}.txt" for subset in SUBSETS for prefix in ("train","test","RUL"))


def extract(raw):
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:
        raise ValueError("Invalid archive size")
    if hashlib.sha256(raw).hexdigest()!=ARCHIVE_SHA256:
        raise ValueError("NASA archive fingerprint mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files={}
        total=0
        for name in NAMES:
            members=[i for i in z.infolist() if not i.is_dir() and Path(i.filename).name==name]
            if len(members)!=1 or members[0].file_size>MAX_BYTES:
                raise ValueError(f"Missing, duplicate or oversized member: {name}")
            total+=members[0].file_size
            if total>MAX_BYTES:
                raise ValueError("Extracted payload exceeds size limit")
            files[name]=z.read(members[0])
    if any(hashlib.sha256(files[n]).hexdigest()!=digest for n,digest in HASHES.items()):
        raise ValueError("Frozen FD001 member mismatch")
    return files


def acquire(output):
    with urllib.request.urlopen(URL,timeout=90) as response:
        raw=response.read(MAX_BYTES+1)
    files=extract(raw)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in files.items():
        (output/name).write_bytes(data)
    manifest={"source":URL,"archive_sha256":ARCHIVE_SHA256,
              "files":{n:hashlib.sha256(data).hexdigest() for n,data in files.items()}}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    # Preserve exact archive for offline verification during evaluation.
    (output/"source.zip").write_bytes(raw)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(acquire(args.output),indent=2))
