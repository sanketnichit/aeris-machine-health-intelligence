"""Retrospective interval guard audit on fingerprint-verified MFPT signals."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import loadmat
from scipy.signal import butter, hilbert, sosfiltfilt

from research.mfpt_transfer import FILES, FLOOR, MARGIN, RATE, WINDOW, WINDOWS, SOURCE_REV, effective_signal
from research.cwru_spectral_audit import normalize
from research.cwru_selective import decide
from research.mfpt_robustness import summarize
from research.verify_evidence import ROOT, verify
from src.vibration_spectrum import spectral_summary
from src.order_uncertainty import interval_fractions, stable_suggestion

ERRORS = (-.05, -.01, 0, .01, .05)
UNCERTAINTIES = (.01, .05)
TOL = 2 * RATE / WINDOW


def envelope_bins(x):
    sos = butter(4, (2000,5000), btype="bandpass", fs=RATE, output="sos")
    env = np.abs(hilbert(sosfiltfilt(sos, normalize(x))))
    s = spectral_summary(normalize(env), RATE, include_bins=True)
    return np.asarray(s["frequency_bins_hz"]), np.asarray(s["bin_mean_square_m2_s4"])


def point_fractions(f, p, centers):
    result = {}
    for k, c in centers.items():
        mask = np.zeros(len(f),dtype=bool)
        for h in (1,2,3):
            mask |= abs(f-h*c)<=TOL
        result[k] = float(p[mask].sum()/p.sum())
    return result


def evaluate_record(spectra, centers, error, uncertainty, name, truth):
    declared = {k:c*(1+error) for k,c in centers.items()}
    interval = (1/(1+uncertainty),1/(1-uncertainty))
    points = [point_fractions(f,p,declared) for f,p in spectra]
    medians = {k:float(np.median([s[k] for s in points])) for k in centers}
    point = decide(medians,FLOOR,MARGIN)
    bounds = [interval_fractions(f,p,declared,interval,TOL) for f,p in spectra]
    guarded = stable_suggestion(bounds,FLOOR,MARGIN)
    if guarded["suggestion"] is not None and guarded["suggestion"] != point["suggestion"]:
        raise ValueError("Interval suggestion contradicts nominal decision")
    return {"file_id":name,"truth":truth,"ungated":point,"gated":guarded,
            "window_bounds":bounds,"scale_interval":list(interval)}


def run(directory):
    entry = next(r for r in verify(ROOT) if r["file"]=="mfpt_transfer_summary.json")
    ref = json.loads((ROOT/entry["file"]).read_text(encoding="utf-8"))
    if ref["score_floor"]!=FLOOR or ref["margin_threshold"]!=MARGIN or ref["source_revision"]!=SOURCE_REV:
        raise ValueError("Frozen reference mismatch")
    refs = {r["file_id"]:r for r in ref["records"]}
    if set(refs)!={name for name,_ in FILES}:
        raise ValueError("Source population mismatch")
    signals = []
    for name, kind in FILES:
        path = directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=refs[name]["sha256"] or kind!=refs[name]["fault"]:
            raise ValueError(f"Source fingerprint or label mismatch: {name}")
        x, centers, _ = effective_signal(loadmat(path,simplify_cells=True),kind)
        spectra = [envelope_bins(x[i*WINDOW:(i+1)*WINDOW]) for i in range(WINDOWS)]
        signals.append((spectra,centers,name,kind))
    scenarios = []
    for error in ERRORS:
        for uncertainty in UNCERTAINTIES:
            rows = [evaluate_record(s,c,error,uncertainty,n,k) for s,c,n,k in signals]
            point, guarded = (summarize(rows,m) for m in ("ungated","gated"))
            scenarios.append({"declared_speed_error":error,"declared_uncertainty":uncertainty,
                "reference_in_interval":abs(error)<=uncertainty,"point":point,"interval":guarded,
                "lost_correct":point["correct_accepted"]-guarded["correct_accepted"],
                "prevented_incorrect":point["incorrect_accepted"]+point["normal_incorrect_accepted"]-guarded["incorrect_accepted"]-guarded["normal_incorrect_accepted"],
                "records":rows})
    return {"scope":"retrospective_continuous_frequency_scale_bounds_not_independent_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"reference_blob_sha":entry["blob_sha"],
            "source_license":"CC BY-NC-SA 4.0","score_floor":FLOOR,"margin_threshold":MARGIN,
            "scenario_count":len(scenarios),"record_count":len(signals),
            "record_scenario_count":len(scenarios)*len(signals),
            "scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
