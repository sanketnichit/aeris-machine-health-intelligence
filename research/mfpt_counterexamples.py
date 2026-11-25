"""Retrospective MFPT falsification-only point-decision audit."""
import argparse
from collections import Counter
from research.order_counterexamples import search_counterexample
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


def run(directory):
    entries = {r["file"]:r for r in verify(ROOT)}
    source = entries["mfpt_transfer_summary.json"]
    previous = entries["mfpt_order_uncertainty_summary.json"]
    breakpoint = entries["mfpt_breakpoint_summary.json"]
    breakpoint_ref = json.loads((ROOT/breakpoint["file"]).read_text(encoding="utf-8"))
    if breakpoint_ref["previous_audit_blob_sha"] != previous["blob_sha"]:
        raise ValueError("Breakpoint provenance mismatch")
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
        for width in UNCERTAINTIES:
            rows=[]
            for spectra,centers,name,kind in signals:
                row=evaluate_record(spectra,centers,error,width,name,kind)
                declared={k:c*(1+error) for k,c in centers.items()}
                refined=verify_breakpoints(spectra[0][0],[p for f,p in spectra],declared,
                                           tuple(row["scale_interval"]),TOL,FLOOR,MARGIN)
                if row["gated"]["suggestion"] is not None and refined["suggestion"]!=row["gated"]["suggestion"]:
                    raise ValueError("Refinement lost global sufficient winner")
                if refined["suggestion"] is not None and refined["suggestion"]!=row["ungated"]["suggestion"]:
                    raise ValueError("Refinement contradicts nominal suggestion")
                witness = None
                if row["ungated"]["suggestion"] is not None and refined["suggestion"] is None:
                    witness = search_counterexample(spectra[0][0], [p for f,p in spectra], declared,
                                                    tuple(row["scale_interval"]), TOL, FLOOR, MARGIN)
                    if witness["nominal"]["suggestion"] != row["ungated"]["suggestion"]:
                        raise ValueError("Nominal point decision did not reproduce")
                rows.append({**row,"refined":refined,"counterexample":witness})
            point,global_bound,refined=(summarize(rows,m) for m in ("ungated","gated","refined"))
            old=next(s for s in prior["scenarios"] if s["declared_speed_error"]==error and s["declared_uncertainty"]==width)
            if point!=old["point"] or global_bound!=old["interval"]:
                raise ValueError("Prior scenario did not reproduce")
            prior_breakpoint = next(s for s in breakpoint_ref["scenarios"]
                                    if s["declared_speed_error"] == error and s["declared_uncertainty"] == width)
            if (point, global_bound, refined) != tuple(prior_breakpoint[k] for k in ("point","global_bound","refined")):
                raise ValueError("Breakpoint scenario did not reproduce")
            counts = {"nominal_correct": Counter(), "nominal_incorrect": Counter()}
            for row in rows:
                w = row["counterexample"]
                if w is None:
                    continue
                group = "nominal_correct" if row["ungated"]["suggestion"] == row["truth"] else "nominal_incorrect"
                key = w["witness_type"] if w["status"] == "point_counterexample" else w["status"]
                counts[group][key] += 1
            scenarios.append({"counterexample_counts": {k: dict(v) for k,v in counts.items()},
                              "point_evaluations": sum(r["counterexample"]["points_checked"] for r in rows if r["counterexample"] is not None),
                              "declared_speed_error":error,"declared_uncertainty":width,
                              "reference_in_interval":abs(error)<=width,"point":point,
                              "global_bound":global_bound,"refined":refined,
                              "recovered_correct":refined["correct_accepted"]-global_bound["correct_accepted"],
                              "new_incorrect":refined["incorrect_accepted"]+refined["normal_incorrect_accepted"]-global_bound["incorrect_accepted"]-global_bound["normal_incorrect_accepted"],
                              "max_cells_checked":max(r["refined"]["cells_checked"] for r in rows),
                              "budget_abstentions":sum(r["refined"]["reason"]=="partition_budget_exceeded" for r in rows),
                              "records":rows})
    return {"scope":"retrospective_point_counterexample_search_not_independent_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"reference_blob_sha":source["blob_sha"],
            "breakpoint_audit_blob_sha":breakpoint["blob_sha"],"previous_audit_blob_sha":previous["blob_sha"],"source_license":"CC BY-NC-SA 4.0",
            "score_floor":FLOOR,"margin_threshold":MARGIN,"scenario_count":len(scenarios),
            "record_count":len(signals),"record_scenario_count":len(scenarios)*len(signals),"scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
