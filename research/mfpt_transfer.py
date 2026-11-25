"""Independent rig transfer of CWRU's frozen research-only rejection rule."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import loadmat
from scipy.signal import butter, hilbert, resample_poly, sosfiltfilt

from research.cwru_spectral_audit import RATE, WINDOW, normalize
from research.cwru_selective import assess, decide
from research.verify_evidence import ROOT, verify, blob_sha
from src.vibration_spectrum import spectral_summary

SOURCE_REV = "d3efefb6ce84fa1ee6c0311f80f7c89cf903ad1d"
BASE = f"https://raw.githubusercontent.com/mathworks/RollingElementBearingFaultDiagnosis-Data/{SOURCE_REV}/"
WINDOWS = 4
FLOOR = 0.00974446327636002
MARGIN = .8
FILES = tuple(
    (f"{'train_data' if i<=n else 'test_data'}/{prefix}_{i}.mat", kind)
    for prefix,kind,total,n in (("baseline","normal",3,2),("InnerRaceFault_vload","inner",7,5),
                                ("OuterRaceFault_vload","outer",7,5))
    for i in range(1,total+1))


def scalar(value):
    a = np.asarray(value)
    if a.size != 1 or np.iscomplexobj(a):
        raise ValueError("Expected scalar source metadata")
    v = float(a.item())
    if not math.isfinite(v):
        raise ValueError("Nonfinite source metadata")
    return v


def effective_signal(data, kind):
    bearing = data["bearing"]
    if not isinstance(bearing, dict):
        raise ValueError("Unexpected bearing structure")
    rate = scalar(bearing["sr"])
    expected = 97656 if kind == "normal" else 48828
    if rate != expected or scalar(bearing["rate"]) != 25:
        raise ValueError("Unexpected source sampling or shaft rate")
    centers = {}
    for name,field,target,multiplier in (("inner","BPFI",118.875,1),
                                         ("outer","BPFO",81.125,1),
                                         ("ball","BSF",63.91,2)):
        value = scalar(data[field])
        if abs(value-target) > .05:
            raise ValueError(f"Unexpected source frequency {field}")
        centers[name] = value * multiplier
    x = np.asarray(bearing["gs"])
    if x.ndim != 1 or np.iscomplexobj(x) or not np.isfinite(x).all():
        raise ValueError("Invalid source waveform")
    divisor = math.gcd(expected, RATE)
    y = resample_poly(x.astype(float), RATE//divisor, expected//divisor,
                      window=("kaiser",5.0),padtype="constant")
    if len(y) < WINDOW*WINDOWS:
        raise ValueError("Incomplete effective waveform")
    return y, centers, {"source_rate_hz":expected,"shaft_rate_hz":25,
                        "source_samples":len(x),"effective_samples":len(y),
                        "load":scalar(bearing["load"])}


def fractions(x, centers):
    spectrum = spectral_summary(normalize(x), RATE, include_bins=True)
    f = np.asarray(spectrum["frequency_bins_hz"])
    p = np.asarray(spectrum["bin_mean_square_m2_s4"])
    if not p.sum()>0:
        raise ValueError("Undefined spectral power")
    result = {}
    for name,center in centers.items():
        mask = np.zeros(len(f),dtype=bool)
        for harmonic in (1,2,3):
            mask |= np.abs(f-harmonic*center)<=2*RATE/WINDOW
        result[name] = float(p[mask].sum()/p.sum())
    return result


def compare(x, centers):
    raw = normalize(x)
    sos = butter(4,(2000,5000),btype="bandpass",fs=RATE,output="sos")
    envelope = np.abs(hilbert(sosfiltfilt(sos,raw)))
    return {"raw":fractions(raw,centers),"envelope":fractions(envelope,centers)}


def evaluate(directory, name, kind):
    path = directory/name
    payload = path.read_bytes()
    signal, centers, metadata = effective_signal(loadmat(path,simplify_cells=True),kind)
    windows = [compare(signal[i*WINDOW:(i+1)*WINDOW],centers) for i in range(WINDOWS)]
    medians = {method:{k:float(np.median([w[method][k] for w in windows]))
                       for k in centers} for method in ("raw","envelope")}
    return {"file_id":name,"fault":kind,"url":BASE+name,
            "sha256":hashlib.sha256(payload).hexdigest(),"source_git_blob":blob_sha(payload),
            "centers_hz":centers,**metadata,"analyzed_samples":WINDOW*WINDOWS,
            "median_fractions":medians,"windows":windows}


def run(directory):
    entry = next(r for r in verify(ROOT) if r["file"]=="cwru_selective_summary.json")
    policy = json.loads((ROOT/entry["file"]).read_text(encoding="utf-8"))["policy"]
    if policy["score_floor"]!=FLOOR or policy["margin_threshold"]!=MARGIN:
        raise ValueError("Frozen policy mismatch")
    rows = [evaluate(directory,name,kind) for name,kind in FILES]
    faults = [r for r in rows if r["fault"]!="normal"]
    normal = [{"file_id":r["file_id"],**decide(r["median_fractions"]["envelope"],FLOOR,MARGIN)}
              for r in rows if r["fault"]=="normal"]
    return {"scope":"independent_rig_transfer_research_only_not_operational_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"source_license":"CC BY-NC-SA 4.0",
            "policy_source_blob_sha":entry["blob_sha"],"score_floor":FLOOR,"margin_threshold":MARGIN,
            "sample_rate_hz":RATE,"window_samples":WINDOW,"windows_per_record":WINDOWS,
            "record_count":len(rows),"fault_assessment":assess(faults,FLOOR,MARGIN),
            "normal_assessment":normal,"normal_incorrect_accepted":sum(d["suggestion"] is not None for d in normal),
            "records":rows}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.directory)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**result,"records":[{k:v for k,v in r.items() if k!="windows"} for r in result["records"]]},
                     indent=2,allow_nan=False))
