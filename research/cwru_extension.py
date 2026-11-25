"""Same-platform extension; no trained classifier or operational thresholds."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import loadmat
from scipy.signal import butter, hilbert, sosfiltfilt, resample_poly

from research.cwru_spectral_audit import RATE, WINDOW, SPEEDS, BASE, normalize
from src.vibration_spectrum import spectral_summary

ORDERS = {"inner": 5.4152, "outer": 3.5848, "ball": 4.7135}
WINDOWS = 6
FILES = tuple((base+load, kind, diameter, load) for base, kind, diameter in (
    (97, "normal", 0), (118, "ball", .007), (169, "inner", .014),
    (185, "ball", .014), (197, "outer", .014)) for load in range(4))


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
        result[name] = float(p[mask].sum()/total)
    return result


def compare(x, rpm):
    raw = normalize(x)
    sos = butter(4, (2000, 5000), btype="bandpass", fs=RATE, output="sos")
    envelope = np.abs(hilbert(sosfiltfilt(sos, raw)))
    return {"raw": fractions(raw, rpm), "envelope": fractions(envelope, rpm)}


def effective_signal(channel, kind):
    if channel.ndim != 2 or 1 not in channel.shape or np.iscomplexobj(channel):
        raise ValueError("Unexpected channel shape")
    channel = channel.reshape(-1)
    if not np.isfinite(channel).all():
        raise ValueError("Nonfinite signal")
    if kind == "normal":
        channel = resample_poly(channel, 1, 4, window=("kaiser", 5.0), padtype="constant")
    if len(channel) < WINDOWS * WINDOW:
        raise ValueError("Incomplete recording")
    return channel


def evaluate(path, ident, kind, diameter, load):
    payload = path.read_bytes()
    key = f"X{ident:03d}_DE_time"
    variables = loadmat(path)
    if key not in variables:
        raise ValueError(f"Missing exact channel {key}")
    source = np.asarray(variables[key])
    channel = effective_signal(source, kind)
    windows = [compare(channel[i*WINDOW:(i+1)*WINDOW], SPEEDS[load]) for i in range(WINDOWS)]
    medians = {method: {order: float(np.median([w[method][order] for w in windows]))
                        for order in ORDERS} for method in ("raw", "envelope")}
    return {"file_id": ident, "url": BASE + f"{ident}.mat", "sha256": hashlib.sha256(payload).hexdigest(),
            "channel": key, "fault": kind, "diameter_in": diameter, "load_hp": load,
            "nominal_rpm": SPEEDS[load], "source_rate_hz": 48000 if kind == "normal" else RATE,
            "recorded_samples": int(source.size), "effective_samples": len(channel),
            "analyzed_samples": WINDOWS * WINDOW, "median_fractions": medians, "windows": windows}


def summarize(rows):
    faults = [r for r in rows if r["fault"] != "normal"]
    normals = [r for r in rows if r["fault"] == "normal"]
    results = {}
    for method in ("raw", "envelope"):
        groups = {}
        for r in faults:
            f = r["median_fractions"][method]
            kind = r["fault"]
            correct = f[kind] > max(v for k,v in f.items() if k != kind)
            label = f"{kind}_{r['diameter_in']:.3f}"
            g = groups.setdefault(label, {"records": 0, "expected_first": 0})
            g["records"] += 1
            g["expected_first"] += int(correct)
        n = [max(r["median_fractions"][method].values()) for r in normals]
        p = [max(r["median_fractions"][method].values()) for r in faults]
        auc = sum(int(a>b)+.5*int(a==b) for a in p for b in n)/(len(p)*len(n))
        results[method] = {"expected_first_count": sum(g["expected_first"] for g in groups.values()),
                           "by_group": groups, "normal_maxima": n, "normal_fault_pairwise_auc": auc}
    improvement = {}
    for r in faults:
        kind = r["fault"]
        label = f"{kind}_{r['diameter_in']:.3f}"
        improvement[label] = improvement.get(label, 0) + int(
            r["median_fractions"]["envelope"][kind] > r["median_fractions"]["raw"][kind])
    return {"representations": results, "expected_fraction_improvements_by_group": improvement}


def run(directory):
    rows = [evaluate(directory / f"{ident}.mat", ident, kind, diameter, load)
            for ident, kind, diameter, load in FILES]
    return {"scope": "same_platform_seeded_fault_extension_not_independent_assets_or_RUL",
            "revision": subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "sample_rate_hz": RATE, "window_samples": WINDOW, "windows_per_record": WINDOWS,
            "record_count": len(rows), "fault_records": 16, "normal_records": 4,
            **summarize(rows), "records": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.directory)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**result,"records":[{k:v for k,v in r.items() if k!="windows"} for r in result["records"]]},indent=2,allow_nan=False))
