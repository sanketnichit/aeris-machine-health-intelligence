from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

DATASET_URL = "https://archive.ics.uci.edu/static/public/601/ai4i2020.zip"
EXPECTED_FILENAME = "ai4i2020.csv"
EXPECTED_HEADER = [
    "UDI",
    "Product ID",
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the AI4I 2020 Predictive Maintenance CSV from UCI."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing data/ai4i2020.csv file.",
    )
    return parser.parse_args()


def validate_csv_bytes(csv_bytes: bytes) -> None:
    with io.TextIOWrapper(io.BytesIO(csv_bytes), encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, None)

    if header != EXPECTED_HEADER:
        raise RuntimeError(
            "Downloaded CSV header does not match the expected AI4I 2020 schema."
        )


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    output_path = data_dir / EXPECTED_FILENAME
    data_dir.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not args.force:
        print(f"{output_path} already exists; nothing to download.")
        return 0

    request = urllib.request.Request(
        DATASET_URL,
        headers={"User-Agent": "AERIS-dataset-setup/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            archive_bytes = response.read()
    except urllib.error.URLError as exc:
        print(
            f"Could not download the dataset from UCI: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            matches = [
                info
                for info in archive.infolist()
                if Path(info.filename).name.lower() == EXPECTED_FILENAME
            ]

            if len(matches) != 1:
                raise RuntimeError(
                    f"Expected exactly one {EXPECTED_FILENAME} in the UCI archive; "
                    f"found {len(matches)}."
                )

            csv_bytes = archive.read(matches[0])

        validate_csv_bytes(csv_bytes)
    except (zipfile.BadZipFile, KeyError, RuntimeError, StopIteration) as exc:
        print(f"Downloaded UCI archive is not the expected AI4I dataset: {exc}", file=sys.stderr)
        return 1

    temp_path = output_path.with_suffix(".csv.tmp")
    try:
        temp_path.write_bytes(csv_bytes)
        temp_path.replace(output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print(f"Downloaded AI4I 2020 dataset to {output_path}")
    print(f"Source: {DATASET_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
