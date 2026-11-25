"""Frozen descriptive CWRU spectral audit; no classifier or RUL prediction."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import loadmat
from scipy.signal import butter, hilbert, sosfiltfilt

from src.vibration_spectrum import spectral_summary

RATE = 12000
WINDOW = 8192
WINDOWS = 12
SPEEDS = (1797, 1772, 1750, 1730)
ORDERS = {"inner": 5.4152, "outer": 3.5848}
FILES = tuple((base + load, kind, load) for base, kind in ((105, "inner"), (130, "outer")) for load in range(4))
BASE = "https://engineering.case.edu/sites/default/files/"


def normalize(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or len(x) != WINDOW or not np.isfinite(x).all():
        raise ValueError("Invalid complete signal window")
    # Scale before centering, protecting against extreme source values.
    scale = np.max(np.abs(x))
    if not scale:
        raise ValueError("Zero signal window")
    x = x / scale
    x = x - x.mean()
    scale = np.max(np.abs(x))
    if not scale:
        raise ValueError("Constant signal window")
    return x / scale


def fractions(x, rpm):
    spectrum = spectral_summary(normalize(x), RATE, include_bins=True)
    f = np.asarray(spectrum["frequency_bins_hz"])
    p = np.asarray(spectrum["bin_mean_square_m2_s4"])
    total = p.sum()
    if not total > 0:
        raise ValueError("Undefined spectral fractions")
    result = {}
    for name, order in ORDERS.items():
        mask = np.zeros(len(f), dtype=bool)
        for harmonic in (1, 2, 3):
            mask |= np.abs(f - harmonic * order * rpm / 60) <= 2 * RATE / WINDOW
        result[name] = float(p[mask].sum() / total)
    return result


def compare_window(x, rpm):
    raw = normalize(x)
    sos = butter(4, (2000, 5000), btype="bandpass", fs=RATE, output="sos")
    envelope = np.abs(hilbert(sosfiltfilt(sos, raw)))
    return {"raw": fractions(raw, rpm), "envelope": fractions(envelope, rpm)}


def evaluate(path, ident, kind, load):
    payload = path.read_bytes()
    variables = loadmat(path)
    keys = [k for k in variables if k.endswith("_DE_time")]
    if len(keys) != 1 or keys[0] != f"X{ident:03d}_DE_time":
        raise ValueError(f"Unexpected DE channel in {path.name}: {keys}")
    channel = np.asarray(variables[keys[0]])
    if channel.ndim != 2 or 1 not in channel.shape or np.iscomplexobj(channel):
        raise ValueError("Unexpected channel shape")
    channel = channel.reshape(-1)
    if len(channel) < WINDOW * WINDOWS or not np.isfinite(channel).all():
        raise ValueError("Incomplete or nonfinite recording")
    windows = [compare_window(channel[i * WINDOW:(i + 1) * WINDOW], SPEEDS[load])
               for i in range(WINDOWS)]
    medians = {method: {order: float(np.median([w[method][order] for w in windows]))
                        for order in ORDERS} for method in ("raw", "envelope")}
    alternative = "outer" if kind == "inner" else "inner"
    return {"file_id": ident, "url": BASE + f"{ident}.mat",
            "sha256": hashlib.sha256(payload).hexdigest(), "channel": keys[0],
            "recorded_samples": len(channel), "analyzed_samples": WINDOW * WINDOWS,
            "fault": kind, "load_hp": load, "nominal_rpm": SPEEDS[load],
            "median_fractions": medians, "windows": windows,
            "envelope_improves_expected": medians["envelope"][kind] > medians["raw"][kind],
            "expected_exceeds_alternative": {method: medians[method][kind] > medians[method][alternative]
                                              for method in medians}}


def run(directory):
    rows = [evaluate(directory / f"{ident}.mat", ident, kind, load) for ident, kind, load in FILES]
    return {"scope": "seeded_lab_fault_descriptive_not_independent_assets_or_RUL",
            "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "sample_rate_hz": RATE, "window_samples": WINDOW, "windows_per_record": WINDOWS,
            "record_count": len(rows),
            "envelope_improves_expected_count": sum(r["envelope_improves_expected"] for r in rows),
            "expected_exceeds_alternative_count": {method: sum(r["expected_exceeds_alternative"][method] for r in rows)
                                                   for method in ("raw", "envelope")},
            "records": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.directory)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({**result, "records": [{k: v for k, v in row.items() if k != "windows"} for row in result["records"]]},
                     indent=2, allow_nan=False))
