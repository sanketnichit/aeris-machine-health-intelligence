"""Retrospective MFPT perturbation audit, not new independent validation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import loadmat

from research.mfpt_transfer import (FILES, FLOOR, MARGIN, RATE, WINDOW, WINDOWS,
                                    SOURCE_REV, BASE, effective_signal, compare)
from research.cwru_selective import decide
from research.verify_evidence import ROOT, verify

SCENARIOS = (("clean", 0), ("noise_db", 20), ("noise_db", 10), ("noise_db", 0),
             ("clip_rms", 2), ("clip_rms", .5),
             ("speed_error", -.05), ("speed_error", -.01),
             ("speed_error", .01), ("speed_error", .05),
             ("clock_error", -.01), ("clock_error", .01),
             ("missing", .01), ("missing", .1))


def perturb(x, centers, scenario, seed):
    x = np.asarray(x, dtype=float)
    if x.shape != (WINDOW,) or not np.isfinite(x).all():
        raise ValueError("Expected finite complete effective window")
    kind, value = scenario
    if scenario not in SCENARIOS:
        raise ValueError("Unregistered perturbation")
    mean = float(x.mean())
    rms = float(np.sqrt(np.mean((x-mean)**2)))
    if not rms > 0:
        raise ValueError("Constant effective window")
    y, f = x.copy(), dict(centers)
    flags, changed = [], 0
    if kind == "noise_db":
        noise = np.random.default_rng(seed).normal(size=WINDOW)
        noise -= noise.mean()
        noise /= np.sqrt(np.mean(noise**2))
        y += noise * rms * 10**(-value/20)
    elif kind == "clip_rms":
        low, high = mean-value*rms, mean+value*rms
        y = np.clip(x, low, high)
        changed = int(np.count_nonzero(y != x))
        if np.any((x <= low) | (x >= high)):
            flags.append("declared_clipping_limit_reached")
    elif kind == "speed_error":
        f = {k:v*(1+value) for k,v in centers.items()}
    elif kind == "clock_error":
        f = {k:v/(1+value) for k,v in centers.items()}
    elif kind == "missing":
        changed = int(WINDOW*value)
        y[WINDOW//4:WINDOW//4+changed] = 0
        flags.append("declared_missing_samples")
    return y, f, {"flags":flags, "affected_fraction":changed/WINDOW}


def evaluate_record(signal, centers, scenario, record_index, name, truth):
    windows = []
    for i in range(WINDOWS):
        x = signal[i*WINDOW:(i+1)*WINDOW]
        y, f, quality = perturb(x, centers, scenario, 42+100*record_index+i)
        scores = compare(y, f)
        windows.append({"window":i, "quality":quality, **scores})
    medians = {k:float(np.median([w["envelope"][k] for w in windows])) for k in centers}
    ungated = decide(medians, FLOOR, MARGIN)
    flags = sorted({f for w in windows for f in w["quality"]["flags"]})
    gated = dict(ungated)
    if flags:
        gated.update(suggestion=None, reason="explicit_quality_metadata")
    return {"file_id":name,"truth":truth,"median_fractions":medians,
            "quality_flags":flags,"ungated":ungated,"gated":gated,"windows":windows}


def summarize(rows, mode):
    faults = [r for r in rows if r["truth"] != "normal"]
    normals = [r for r in rows if r["truth"] == "normal"]
    accepted = [r for r in faults if r[mode]["suggestion"] is not None]
    errors = sum(r[mode]["suggestion"] != r["truth"] for r in accepted)
    return {"fault_records":len(faults),"accepted":len(accepted),
            "correct_accepted":len(accepted)-errors,"incorrect_accepted":errors,
            "abstained":len(faults)-len(accepted),
            "coverage":len(accepted)/len(faults) if faults else None,
            "retained_error":errors/len(accepted) if accepted else None,
            "forced_errors":sum(r["ungated"]["candidate"] != r["truth"] for r in faults),
            "normal_records":len(normals),
            "normal_incorrect_accepted":sum(r[mode]["suggestion"] is not None for r in normals)}


def run(directory):
    entry = next(r for r in verify(ROOT) if r["file"]=="mfpt_transfer_summary.json")
    reference = json.loads((ROOT/entry["file"]).read_text(encoding="utf-8"))
    if reference["score_floor"]!=FLOOR or reference["margin_threshold"]!=MARGIN or reference["source_revision"]!=SOURCE_REV:
        raise ValueError("Frozen reference mismatch")
    refs = {r["file_id"]:r for r in reference["records"]}
    if set(refs)!={name for name,_ in FILES}:
        raise ValueError("Frozen source population mismatch")
    signals = []
    for name,kind in FILES:
        path = directory/name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != refs[name]["sha256"] or kind != refs[name]["fault"]:
            raise ValueError(f"Source fingerprint or label mismatch: {name}")
        signal,centers,_ = effective_signal(loadmat(path,simplify_cells=True),kind)
        signals.append((signal,centers,name,kind))
    results = []
    for scenario in SCENARIOS:
        rows = [evaluate_record(x,f,scenario,i,name,kind)
                for i,(x,f,name,kind) in enumerate(signals)]
        ungated,gated = (summarize(rows,m) for m in ("ungated","gated"))
        results.append({"kind":scenario[0],"value":scenario[1],"ungated":ungated,"gated":gated,
                        "guard_lost_correct":ungated["correct_accepted"]-gated["correct_accepted"],
                        "guard_prevented_incorrect":ungated["incorrect_accepted"]+ungated["normal_incorrect_accepted"]-gated["incorrect_accepted"]-gated["normal_incorrect_accepted"],
                        "records":rows})
    clean = results[0]["ungated"]
    if clean["accepted"]!=reference["fault_assessment"]["accepted"] or clean["incorrect_accepted"]!=reference["fault_assessment"]["incorrect_accepted"] or clean["normal_incorrect_accepted"]!=reference["normal_incorrect_accepted"]:
        raise ValueError("Clean reference outcome did not reproduce")
    return {"scope":"paired_retrospective_mfpt_sensor_perturbations_not_independent_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"source_url":BASE,"source_license":"CC BY-NC-SA 4.0",
            "reference_blob_sha":entry["blob_sha"],"score_floor":FLOOR,"margin_threshold":MARGIN,
            "scenario_count":len(results),"record_count":len(signals),
            "record_scenario_count":len(results)*len(signals),
            "window_scenario_count":len(results)*len(signals)*WINDOWS,
            "source_sha256":{n:refs[n]["sha256"] for n,_ in FILES},"scenarios":results}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
