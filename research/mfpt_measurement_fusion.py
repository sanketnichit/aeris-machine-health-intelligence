"""Retrospective two-channel speed-bound intersection audit."""
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
from src.measurement_budget import calibration_guard
from src.measurement_fusion import fusion_guard
from research.mfpt_order_uncertainty import point_fractions
from research.cwru_selective import decide
import numpy as np

PRIMARY_REPEATABILITY = .001
PRIMARY_BIAS = (.01, .05)
SECONDARY_REPEATABILITY = .001
SECONDARY_BIAS = .004
MODES = ('reference_aligned', 'small_offset', 'shared_bias', 'opposed_bias')


def run(directory):
    entries = {r["file"]:r for r in verify(ROOT)}
    source = entries["mfpt_transfer_summary.json"]
    previous = entries["mfpt_order_uncertainty_summary.json"]
    measurement = entries["mfpt_measurement_width_summary.json"]
    budget = entries["mfpt_bias_budget_summary.json"]
    budget_ref = json.loads((ROOT/budget["file"]).read_text(encoding="utf-8"))
    if budget_ref["measurement_audit_blob_sha"] != measurement["blob_sha"]:
        raise ValueError("Bias evidence provenance mismatch")
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
        for bias in PRIMARY_BIAS:
            for mode in MODES:
                secondary_error = {"reference_aligned":0., "small_offset":.005,
                                   "shared_bias":error, "opposed_bias":-error}[mode]
                ratio=(1+secondary_error)/(1+error)
                reference=1/(1+error)
                rows=[]
                for spectra,centers,name,kind in signals:
                    row=evaluate_record(spectra,centers,error,PRIMARY_REPEATABILITY,name,kind)
                    declared={k:c*(1+error) for k,c in centers.items()}
                    f=spectra[0][0]
                    powers=[p for _,p in spectra]
                    baseline=calibration_guard(f,powers,declared,PRIMARY_REPEATABILITY,bias,TOL,FLOOR,MARGIN)
                    fused=fusion_guard(f,powers,declared,ratio,PRIMARY_REPEATABILITY,bias,
                                       SECONDARY_REPEATABILITY,SECONDARY_BIAS,TOL,FLOOR,MARGIN)
                    if fused["suggestion"] is not None:
                        anchor={k:c*fused["anchor_scale"] for k,c in declared.items()}
                        scores=[point_fractions(f,p,anchor) for f,p in spectra]
                        medians={k:float(np.median([s[k] for s in scores])) for k in anchor}
                        if fused["suggestion"]!=decide(medians,FLOOR,MARGIN)["suggestion"]:
                            raise ValueError("Fusion contradicts anchor decision")
                    if baseline["suggestion"] is not None and fused["suggestion"] is not None and baseline["suggestion"]!=fused["suggestion"]:
                        raise ValueError("Fusion contradicts primary stable decision")
                    intersection=fused["intersection"]
                    contained=intersection is not None and intersection[0]-1e-15<=reference<=intersection[1]+1e-15
                    rows.append({**row,"primary":baseline,"fused":fused,"reference_in_intersection":contained})
                primary,fused=(summarize(rows,m) for m in ("primary","fused"))
                old=next(s for s in budget_ref["scenarios"] if s["declared_speed_error"]==error
                         and s["repeatability_bound"]==PRIMARY_REPEATABILITY and s["assumed_bias_bound"]==bias)
                if primary!=old["composed"]:
                    raise ValueError("Frozen primary calibration guard did not reproduce")
                scenarios.append({"primary_speed_error":error,"primary_bias_bound":bias,
                                  "secondary_mode":mode,"secondary_speed_error":secondary_error,
                                  "primary":primary,"fused":fused,
                                  "both_total_bounds_cover_injected_error":abs(error)<=PRIMARY_REPEATABILITY+bias and abs(secondary_error)<=SECONDARY_REPEATABILITY+SECONDARY_BIAS,
                                  "conflicts":sum(r["fused"]["status"]=="measurement_conflict" for r in rows),
                                  "reference_contained":sum(r["reference_in_intersection"] for r in rows),
                                  "nonempty_without_reference":sum(r["fused"]["intersection"] is not None and not r["reference_in_intersection"] for r in rows),
                                  "accepted_without_reference":sum(r["fused"]["suggestion"] is not None and not r["reference_in_intersection"] for r in rows),
                                  "recovered_correct":sum(r["primary"]["suggestion"] is None and r["fused"]["suggestion"]==r["truth"] for r in rows),
                                  "lost_correct":sum(r["primary"]["suggestion"]==r["truth"] and r["fused"]["suggestion"] is None for r in rows),
                                  "records":rows})
    return {"scope":"retrospective_two_channel_declared_bounds_not_sensor_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"reference_blob_sha":source["blob_sha"],
            "bias_audit_blob_sha":budget["blob_sha"],"measurement_audit_blob_sha":measurement["blob_sha"],
            "source_license":"CC BY-NC-SA 4.0","score_floor":FLOOR,"margin_threshold":MARGIN,
            "primary_repeatability":PRIMARY_REPEATABILITY,"secondary_repeatability":SECONDARY_REPEATABILITY,
            "secondary_bias_bound":SECONDARY_BIAS,"scenario_count":len(scenarios),
            "record_count":len(signals),"record_scenario_count":len(scenarios)*len(signals),"scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
