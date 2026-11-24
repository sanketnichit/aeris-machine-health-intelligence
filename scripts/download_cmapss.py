"""Download FD001 from the NASA catalog; never extract arbitrary archive paths."""
import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

URL = "https://data.nasa.gov/docs/legacy/CMAPSSData.zip"
NAMES = ("train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt")
MAX_BYTES = 100 * 1024 * 1024


def extract_fd001(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        result = {}
        for name in NAMES:
            matches = [i for i in archive.infolist() if not i.is_dir() and Path(i.filename).name == name]
            if len(matches) != 1 or matches[0].file_size > MAX_BYTES:
                raise ValueError(f"Missing, duplicate or oversized archive member: {name}")
            result[name] = archive.read(matches[0])
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with urllib.request.urlopen(URL, timeout=90) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Archive exceeds size limit")
    files = extract_fd001(raw)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (args.output / name).write_bytes(content)
    manifest = {"source": URL, "archive_sha256": hashlib.sha256(raw).hexdigest(),
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
