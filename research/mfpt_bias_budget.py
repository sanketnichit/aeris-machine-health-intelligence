"""Retrospective declared systematic-bias budget audit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from scipy.io import loadmat

from research.mfpt_transfer import FILES, FLOOR, MARGIN, RATE, WINDOW, WINDOWS, SOURCE_REV, effective_signal
from research.mfpt_order_uncertainty import ERRORS, UNCERTAINTIES, TOL, envelope_bins, evaluate_record
from research.mfpt_robustness import summarize
from research.verify_evidence import ROOT, verify
from src.order_breakpoints import verify_breakpoints
from src.measurement_budget import calibration_guard, measurement_budget

REPEATABILITY = (.001, .005, .01)
BIAS_BOUNDS = (0., .01, .05)


def run(directory):
    entries = {r["file"]:r for r in verify(ROOT)}
    source = entries["mfpt_transfer_summary.json"]
    previous = entries["mfpt_order_uncertainty_summary.json"]
    measurement = entries["mfpt_measurement_width_summary.json"]
    frozen = json.loads((ROOT/measurement["file"]).read_text(encoding="utf-8"))
    if frozen["previous_audit_blob_sha"] != previous["blob_sha"] or frozen["reference_blob_sha"] != source["blob_sha"]:
        raise ValueError("Measurement evidence provenance mismatch")
    ref = json.loads((ROOT/source["file"]).read_text(encoding="utf-8"))
    prior = json.loads((ROOT/previous["file"]).read_text(encoding="utf-8"))
    if ref["score_floor"]!=FLOOR or ref["margin_threshold"]!=MARGIN or ref["source_revision"]!=SOURCE_REV:
        raise ValueError("Frozen reference mismatch")
    if prior["reference_blob_sha"]!=source["blob_sha"]:
        raise ValueError("Prior audit source mismatch")
    refs = {r["file_id"]:r for r in ref["records"]}
    if set(refs)!={name for name,_ in FILES}:
        raise ValueError("Source population mismatch")
    signals = []
    for name,kind in FILES:
        path = directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=refs[name]["sha256"] or kind!=refs[name]["fault"]:
            raise ValueError(f"Source fingerprint or label mismatch: {name}")
        x, centers, _ = effective_signal(loadmat(path,simplify_cells=True),kind)
        spectra = [envelope_bins(x[i*WINDOW:(i+1)*WINDOW]) for i in range(WINDOWS)]
        if not all((f==spectra[0][0]).all() for f,p in spectra):
            raise ValueError("Inconsistent frequency bins")
        signals.append((spectra,centers,name,kind))
    scenarios=[]
    for error in ERRORS:
        for repeatability in REPEATABILITY:
            for bias in BIAS_BOUNDS:
                rows=[]
                for spectra,centers,name,kind in signals:
                    row=evaluate_record(spectra,centers,error,repeatability,name,kind)
                    declared={k:c*(1+error) for k,c in centers.items()}
                    f=spectra[0][0]
                    powers=[p for _,p in spectra]
                    baseline=verify_breakpoints(f,powers,declared,tuple(row["scale_interval"]),TOL,FLOOR,MARGIN)
                    guarded=calibration_guard(f,powers,declared,repeatability,bias,TOL,FLOOR,MARGIN)
                    unknown=calibration_guard(f,powers,declared,repeatability,None,TOL,FLOOR,MARGIN)
                    if unknown["suggestion"] is not None:
                        raise ValueError("Missing bias bound authorized a suggestion")
                    if bias==0 and guarded["suggestion"]!=baseline["suggestion"]:
                        raise ValueError("Zero-bias control did not reproduce")
                    if guarded["suggestion"] is not None and guarded["suggestion"]!=row["ungated"]["suggestion"]:
                        raise ValueError("Composed guard contradicts nominal decision")
                    if guarded["suggestion"] is not None and baseline["suggestion"] is not None and guarded["suggestion"]!=baseline["suggestion"]:
                        raise ValueError("Conflicting stable labels on nested intervals")
                    rows.append({**row,"baseline":baseline,"guarded":guarded})
                baseline,guarded=(summarize(rows,m) for m in ("baseline","guarded"))
                old=next(s for s in frozen["scenarios"] if s["declared_speed_error"]==error and s["declared_uncertainty"]==repeatability)
                if baseline!=old["refined"]:
                    raise ValueError("Frozen repeatability-only result did not reproduce")
                budget=measurement_budget(repeatability,bias)
                width=budget["total_relative_bound"]
                scenarios.append({"declared_speed_error":error,"repeatability_bound":repeatability,
                                  "assumed_bias_bound":bias,"total_relative_bound":width,
                                  "synthetic_bias_within_assumption":abs(error)<=bias,
                                  "reference_in_interval":abs(error)<=width,
                                  "repeatability_only":baseline,"composed":guarded,
                                  "correct_withheld_by_composition":sum(r["baseline"]["suggestion"]==r["truth"] and r["guarded"]["suggestion"] is None for r in rows),
                                  "incorrect_withheld_by_composition":sum(r["baseline"]["suggestion"] is not None and r["baseline"]["suggestion"]!=r["truth"] and r["guarded"]["suggestion"] is None for r in rows),
                                  "newly_accepted_by_composition":sum(r["baseline"]["suggestion"] is None and r["guarded"]["suggestion"] is not None for r in rows),
                                  "unknown_bias_acceptances":0,
                                  "budget_abstentions":sum(r["guarded"]["reason"]=="partition_budget_exceeded" for r in rows),
                                  "records":rows})
    return {"scope":"retrospective_declared_bias_budget_not_sensor_calibration",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"reference_blob_sha":source["blob_sha"],
            "measurement_audit_blob_sha":measurement["blob_sha"],
            "previous_audit_blob_sha":previous["blob_sha"],"source_license":"CC BY-NC-SA 4.0",
            "score_floor":FLOOR,"margin_threshold":MARGIN,"scenario_count":len(scenarios),
            "record_count":len(signals),"record_scenario_count":len(scenarios)*len(signals),
            "scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
