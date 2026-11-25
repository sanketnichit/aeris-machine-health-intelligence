"""Retrospective measurement-width sweep, not hardware qualification."""
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

WIDTHS = (.001, .0025, .005, .01, .02, .05)


def profile(widths, suggestions, error, truth):
    """Describe observed grid behavior without interpolating a safe width."""
    if len(widths) != len(suggestions) or not widths or any(a >= b for a,b in zip(widths,widths[1:])):
        raise ValueError("Expected an increasing width grid")
    accepted = [(w,s) for w,s in zip(widths,suggestions) if s is not None]
    if len({s for _,s in accepted}) > 1:
        raise ValueError("Conflicting stable labels on nested intervals")
    correct = [w for w,s in accepted if s == truth]
    incorrect = [w for w,s in accepted if s != truth]
    return {"largest_tested_accepted_width": max((w for w,_ in accepted), default=None),
            "largest_tested_correct_width": max(correct, default=None),
            "accepted_without_reference": sum(abs(error)>w for w,_ in accepted),
            "incorrect_accepted_widths": incorrect,
            "narrower_unresolved": sum(s is None and any(v>w for v,_ in accepted) for w,s in zip(widths,suggestions))}



def run(directory):
    entries = {r["file"]:r for r in verify(ROOT)}
    source = entries["mfpt_transfer_summary.json"]
    previous = entries["mfpt_order_uncertainty_summary.json"]
    possibility = entries["mfpt_possibility_summary.json"]
    possibility_ref = json.loads((ROOT/possibility["file"]).read_text(encoding="utf-8"))
    if possibility_ref["previous_audit_blob_sha"] != previous["blob_sha"]:
        raise ValueError("Possibility evidence provenance mismatch")
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
    profiles=[]
    for error in ERRORS:
        history = {name: [] for name,kind in FILES}
        for width in WIDTHS:
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
                history[name].append(refined["suggestion"])
                rows.append({**row,"refined":refined})
            point,global_bound,refined=(summarize(rows,m) for m in ("ungated","gated","refined"))
            if width in UNCERTAINTIES:
                old=next(s for s in prior["scenarios"] if s["declared_speed_error"]==error and s["declared_uncertainty"]==width)
                frozen=next(s for s in possibility_ref["scenarios"] if s["declared_speed_error"]==error and s["declared_uncertainty"]==width)
                if point!=old["point"] or global_bound!=old["interval"] or refined!=frozen["refined"]:
                    raise ValueError("Prior scenario did not reproduce")
            scenarios.append({"declared_speed_error":error,"declared_uncertainty":width,
                              "reference_in_interval":abs(error)<=width,"point":point,
                              "global_bound":global_bound,"refined":refined,
                              "recovered_correct":refined["correct_accepted"]-global_bound["correct_accepted"],
                              "new_incorrect":refined["incorrect_accepted"]+refined["normal_incorrect_accepted"]-global_bound["incorrect_accepted"]-global_bound["normal_incorrect_accepted"],
                              "max_cells_checked":max(r["refined"]["cells_checked"] for r in rows),
                              "budget_abstentions":sum(r["refined"]["reason"]=="partition_budget_exceeded" for r in rows),
                              "records":rows})
        records = [{"file_id":name,"truth":kind,**profile(WIDTHS,history[name],error,kind)} for name,kind in FILES]
        profiles.append({"declared_speed_error":error,"records":records,
                         "accepted_without_reference":sum(r["accepted_without_reference"] for r in records),
                         "narrower_unresolved":sum(r["narrower_unresolved"] for r in records)})
    return {"scope":"retrospective_measurement_width_grid_not_hardware_qualification",
            "possibility_audit_blob_sha":possibility["blob_sha"],"width_grid":list(WIDTHS),"profiles":profiles,
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"reference_blob_sha":source["blob_sha"],
            "previous_audit_blob_sha":previous["blob_sha"],"source_license":"CC BY-NC-SA 4.0",
            "score_floor":FLOOR,"margin_threshold":MARGIN,"scenario_count":len(scenarios),
            "record_count":len(signals),"record_scenario_count":len(scenarios)*len(signals),"scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"profiles":[{k:v for k,v in r.items() if k!="records"} for r in report["profiles"]],"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
