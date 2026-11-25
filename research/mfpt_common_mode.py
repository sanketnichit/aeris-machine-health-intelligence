"""Retrospective common-mode error decomposition audit."""
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
from src.common_mode import common_mode_guard
from research.mfpt_order_uncertainty import point_fractions
from research.cwru_selective import decide
import numpy as np

PRIMARY_REPEATABILITY = .001
PRIMARY_BIAS = (.01, .05)
SECONDARY_REPEATABILITY = .001
SECONDARY_BIAS = .004
MODES = ('reference_aligned', 'small_offset', 'shared_bias', 'opposed_bias')
COMMON_BOUNDS = (0., .01, .05)


def run(directory):
    entries = {r["file"]:r for r in verify(ROOT)}
    source = entries["mfpt_transfer_summary.json"]
    previous = entries["mfpt_order_uncertainty_summary.json"]
    measurement = entries["mfpt_measurement_width_summary.json"]
    budget = entries["mfpt_bias_budget_summary.json"]
    fusion = entries["mfpt_measurement_fusion_summary.json"]
    fusion_ref = json.loads((ROOT/fusion["file"]).read_text(encoding="utf-8"))
    if fusion_ref["bias_audit_blob_sha"] != budget["blob_sha"]:
        raise ValueError("Fusion evidence provenance mismatch")
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
                actual_common = error if mode=="shared_bias" else 0.
                ratio=(1+secondary_error)/(1+error)
                reference=1/(1+error)
                a=PRIMARY_REPEATABILITY+bias
                b=SECONDARY_REPEATABILITY+SECONDARY_BIAS
                old=next(s for s in fusion_ref["scenarios"] if s["primary_speed_error"]==error
                         and s["primary_bias_bound"]==bias and s["secondary_mode"]==mode)
                for common in COMMON_BOUNDS:
                    rows=[]
                    valid=(abs(actual_common)<=common+1e-12 and abs(error-actual_common)<=a+1e-12
                           and abs(secondary_error-actual_common)<=b+1e-12)
                    for spectra,centers,name,kind in signals:
                        row=evaluate_record(spectra,centers,error,PRIMARY_REPEATABILITY,name,kind)
                        declared={k:c*(1+error) for k,c in centers.items()}
                        f=spectra[0][0]
                        powers=[p for _,p in spectra]
                        guarded=common_mode_guard(f,powers,declared,ratio,a,b,common,TOL,FLOOR,MARGIN)
                        interval=guarded["intersection"]
                        contained=interval is not None and interval[0]-1e-12<=reference<=interval[1]+1e-12
                        if valid and not contained:
                            raise ValueError("Valid declared decomposition excluded reference")
                        if guarded["suggestion"] is not None:
                            anchor={k:c*guarded["anchor_scale"] for k,c in declared.items()}
                            scores=[point_fractions(f,p,anchor) for f,p in spectra]
                            medians={k:float(np.median([s[k] for s in scores])) for k in anchor}
                            if guarded["suggestion"]!=decide(medians,FLOOR,MARGIN)["suggestion"]:
                                raise ValueError("Common-mode guard contradicts anchor decision")
                        rows.append({**row,"guarded":guarded,"reference_contained":contained})
                    outcome=summarize(rows,"guarded")
                    if common==0 and outcome!=old["fused"]:
                        raise ValueError("Frozen zero-common control did not reproduce")
                    scenarios.append({"primary_speed_error":error,"primary_bias_bound":bias,
                                      "secondary_mode":mode,"secondary_speed_error":secondary_error,
                                      "actual_common_error":actual_common,"assumed_common_bound":common,
                                      "declared_decomposition_valid":valid,"prior_fused":old["fused"],
                                      "common_guard":outcome,
                                      "reference_contained":sum(r["reference_contained"] for r in rows),
                                      "conflicts":sum(r["guarded"]["intersection"] is None for r in rows),
                                      "differential_conflicts":sum(r["guarded"]["status"]=="common_mode_conflict" for r in rows),
                                      "nonempty_without_reference":sum(r["guarded"]["intersection"] is not None and not r["reference_contained"] for r in rows),
                                      "accepted_without_reference":sum(r["guarded"]["suggestion"] is not None and not r["reference_contained"] for r in rows),
                                      "records":rows})
    return {"scope":"retrospective_common_mode_error_decomposition_not_sensor_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "source_revision":SOURCE_REV,"reference_blob_sha":source["blob_sha"],
            "fusion_audit_blob_sha":fusion["blob_sha"],"bias_audit_blob_sha":budget["blob_sha"],
            "source_license":"CC BY-NC-SA 4.0","score_floor":FLOOR,"margin_threshold":MARGIN,
            "common_bounds":list(COMMON_BOUNDS),"scenario_count":len(scenarios),
            "record_count":len(signals),"record_scenario_count":len(scenarios)*len(signals),"scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in r.items() if k!="records"} for r in report["scenarios"]]},indent=2,allow_nan=False))
