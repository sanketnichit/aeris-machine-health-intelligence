"""Offline CSV acquisition adapter; declared sample clock, no hardware inference."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path

from src.edge_buffer import enqueue
from src.telemetry_contract import ASSET, validate_batch

MAX_CAPTURE_BYTES = 4 * 1024 * 1024
MAX_SAMPLES = 100_000
MAX_MAGNITUDE = 1e6  # numerical input bound, not a machine operating limit
UNIT_SCALE = {"m/s2": 1.0, "g": 9.80665}
AXES = ("horizontal", "vertical")


def read_capture(raw, unit):
    if not isinstance(raw, bytes) or len(raw) > MAX_CAPTURE_BYTES:
        raise ValueError("Expected bounded CSV bytes")
    if unit not in UNIT_SCALE:
        raise ValueError("Explicit acceleration unit required: m/s2 or g")
    try:
        rows = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        if next(rows, None) != list(AXES):
            raise ValueError("Expected CSV header horizontal,vertical")
        samples = []
        for line, row in enumerate(rows, start=2):
            if len(samples) >= MAX_SAMPLES or len(row) != 2:
                raise ValueError(f"Invalid or excessive sample rows at line {line}")
            values = tuple(float(value) * UNIT_SCALE[unit] for value in row)
            if any(not math.isfinite(v) or abs(v) > MAX_MAGNITUDE for v in values):
                raise ValueError(f"Nonfinite or excessive acceleration at line {line}")
            samples.append(values)
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("Invalid UTF-8 CSV capture") from exc
    return samples


def statistics(values, clipping_limit):
    n = len(values)
    mean = math.fsum(values) / n
    rms = math.sqrt(math.fsum(v * v for v in values) / n)
    ac_rms = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / n)
    peak = max(map(abs, values))
    flags = []
    if min(values) == max(values):
        flags.append("constant_axis")
    if clipping_limit is not None and peak >= clipping_limit:
        flags.append("declared_range_reached")
    return {"mean_m_s2": mean, "rms_m_s2": rms, "ac_rms_m_s2": ac_rms,
            "peak_m_s2": peak, "crest_factor": peak / rms if rms else None,
            "quality_flags": flags}


def analyze_capture(raw, *, asset_id, start, sample_rate_hz, window_samples, unit,
                    clipping_limit=None, spectrum=False):
    if not isinstance(asset_id, str) or not ASSET.fullmatch(asset_id):
        raise ValueError("Invalid asset identifier")
    if type(sample_rate_hz) is not int or not 1 <= sample_rate_hz <= 100_000:
        raise ValueError("Sample rate must be an integer from 1 to 100000 Hz")
    if type(window_samples) is not int or not 2 <= window_samples <= 8192:
        raise ValueError("Window size must be 2 to 8192 samples")
    if not isinstance(start, str) or "T" not in start or len(start) > 40:
        raise ValueError("Expected ISO timestamp of first sample")
    try:
        origin = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if origin.utcoffset() is None:
            raise ValueError("Timezone required")
        origin = origin.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ValueError("Invalid capture start timestamp") from exc
    if type(spectrum) is not bool or (spectrum and window_samples < 16):
        raise ValueError("Spectral analysis requires windows of at least 16 samples")
    samples = read_capture(raw, unit)
    if not samples or len(samples) % window_samples or len(samples) // window_samples > 1000:
        raise ValueError("Expected 1 to 1000 complete nonoverlapping windows; no partial discard")
    if clipping_limit is not None:
        if type(clipping_limit) not in (int, float):
            raise ValueError("Clipping limit must be a positive number in the declared unit")
        try:
            clipping_limit = float(clipping_limit) * UNIT_SCALE[unit]
        except OverflowError as exc:
            raise ValueError("Clipping limit too large") from exc
        if not math.isfinite(clipping_limit) or clipping_limit <= 0:
            raise ValueError("Invalid clipping limit")
    records, windows = [], []
    for offset in range(0, len(samples), window_samples):
        # Endpoint is the last observed sample, not a future window boundary.
        index = offset + window_samples - 1
        micros = (index * 1_000_000 + sample_rate_hz // 2) // sample_rate_hz
        try:
            timestamp = (origin + timedelta(microseconds=micros)).isoformat().replace("+00:00", "Z")
        except OverflowError as exc:
            raise ValueError("Capture timestamp exceeds supported range") from exc
        summary = {axis: statistics([r[j] for r in samples[offset:offset + window_samples]], clipping_limit)
                   for j, axis in enumerate(AXES)}
        if spectrum:
            from src.vibration_spectrum import spectral_summary
            for j, axis in enumerate(AXES):
                summary[axis]["spectrum"] = (None if summary[axis]["quality_flags"] else
                    spectral_summary([r[j] for r in samples[offset:offset + window_samples]], sample_rate_hz))
        windows.append({"first_sample_index": offset, "last_sample_index": index,
                        "timestamp": timestamp, "axes": summary})
        records.append({"asset_id": asset_id, "timestamp": timestamp, "measurements": {
            axis + "_vibration_rms": {"value": summary[axis]["rms_m_s2"], "unit": "m/s2"}
            for axis in AXES}})
    batch = {"schema_version": 1, "records": validate_batch({"schema_version": 1, "records": records})["records"]}
    flagged = sum(any(a["quality_flags"] for a in w["axes"].values()) for w in windows)
    return {"capture_sha256": hashlib.sha256(raw).hexdigest(), "asset_id": asset_id,
            "start_utc": origin.isoformat().replace("+00:00", "Z"),
            "input_unit": unit, "sample_rate_hz": sample_rate_hz, "window_samples": window_samples,
            "sample_count": len(samples), "window_count": len(windows), "flagged_windows": flagged,
            "declared_clipping_limit_m_s2": clipping_limit,
            "clock_basis": "declared_uniform_sampling_unverified", "rms_basis": "includes_dc",
            "eligible_for_queue": flagged == 0, "spectral_analysis_requested": spectrum,
            "windows": windows, "batch": batch}


def queue_capture(path, analysis):
    # This function takes the result of analyze_capture; it is not an untrusted API.
    if not analysis["eligible_for_queue"]:
        raise ValueError("Capture contains flagged windows; no observations queued")
    return enqueue(path, analysis["batch"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--rate", type=int, required=True)
    parser.add_argument("--window", type=int, required=True)
    parser.add_argument("--unit", choices=tuple(UNIT_SCALE), required=True)
    parser.add_argument("--clip-limit", type=float)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--spectrum", action="store_true", help="Include descriptive FFT features (at least 16 samples per window)")
    args = parser.parse_args()
    with args.capture.open("rb") as source:
        raw = source.read(MAX_CAPTURE_BYTES + 1)
    try:
        analysis = analyze_capture(raw, asset_id=args.asset, start=args.start,
                                   sample_rate_hz=args.rate, window_samples=args.window,
                                   unit=args.unit, clipping_limit=args.clip_limit, spectrum=args.spectrum)
        result = None
        if args.queue is not None and analysis["eligible_for_queue"]:
            result = queue_capture(args.queue, analysis)
        print(json.dumps({"analysis": analysis, "queue_result": result}, indent=2, allow_nan=False))
        return 0 if analysis["eligible_for_queue"] else 2
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
