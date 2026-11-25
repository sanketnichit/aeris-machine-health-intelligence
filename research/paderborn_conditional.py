"""Frozen conditional physical transfer study, not calibrated validation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import subprocess

import numpy as np
import rarfile
from scipy.io import loadmat

from research.verify_evidence import ROOT,verify
from research.paderborn_cohort import acquire_pinned,load_registry
from research.paderborn_intake import inventory,member_bytes,CONDITIONS
from research.paderborn_documents import document_summary
from src.paderborn_preprocessing import linked_axis,conditional_paths,comparison_summary,effective_orders
from research.mfpt_transfer import FLOOR,MARGIN,RATE,WINDOW,WINDOWS
from research.mfpt_order_uncertainty import envelope_bins,point_fractions
from research.cwru_selective import decide

FIELDS=("rolling_elements","pitch_diameter_mm","element_diameter_mm","angle_deg")
MODES=("nominal","stored_time")


def geometry_candidate(raw,previous):
    fields=document_summary(raw,"fact_sheet")["geometry"]
    for k in FIELDS[1:]:
        if fields[k]["status"]!="unique_candidate" or fields[k]["value"]!=previous[k]["value"]:
            raise ValueError("Registered geometry candidate mismatch")
    if any(fields[k]["status"]!="unique_candidate" for k in FIELDS):
        return fields,None
    try:
        orders=effective_orders(*(fields[k]["value"] for k in FIELDS))
    except ValueError:
        return fields,None
    return fields,orders


def withheld(reason):
    return {"suggestion":None,"reason":reason}


def score(signal,orders,condition):
    if signal is None:
        return withheld("preprocessing_unavailable")
    speed=15. if condition.startswith("N09_") else 25.
    centers={k:v*speed for k,v in orders.items()}
    spectra=[envelope_bins(signal[i*WINDOW:(i+1)*WINDOW]) for i in range(WINDOWS)]
    fractions=[point_fractions(f,p,centers) for f,p in spectra]
    medians={k:float(np.median([p[k] for p in fractions])) for k in centers}
    return {**decide(medians,FLOOR,MARGIN),"median_fractions":medians}


def evaluate(raw,name,condition,orders):
    if orders is None:
        return {"nominal":withheld("geometry_candidate_unresolved"),
                "stored_time":withheld("geometry_candidate_unresolved"),
                "preprocessing":None}
    record=loadmat(io.BytesIO(raw),simplify_cells=True)[Path(name).stem]
    try:
        values,times=linked_axis(record,"vibration_1")
        paths=conditional_paths(values,times)
        comparison=comparison_summary(paths)
    except ValueError:
        return {"nominal":withheld("invalid_waveform_or_time_metadata"),
                "stored_time":withheld("invalid_waveform_or_time_metadata"),
                "preprocessing":None}
    result={}
    for mode in MODES:
        try:
            result[mode]=score(paths[mode],orders,condition)
        except ValueError:
            result[mode]=withheld("undefined_spectral_score")
    return {**result,"preprocessing":comparison}


def counts(rows,mode):
    faults=[r for r in rows if r["truth"]!="normal"]
    normals=[r for r in rows if r["truth"]=="normal"]
    correct=sum(r[mode]["suggestion"]==r["truth"] for r in faults)
    incorrect=sum(r[mode]["suggestion"] not in (None,r["truth"]) for r in faults)
    reasons={}
    for r in rows:
        reason=r[mode]["reason"]
        reasons[reason]=reasons.get(reason,0)+1
    return {"fault_records":len(faults),"correct_accepted":correct,
            "incorrect_accepted":incorrect,"fault_abstained":len(faults)-correct-incorrect,
            "normal_records":len(normals),
            "normal_incorrect_accepted":sum(r[mode]["suggestion"] is not None for r in normals),
            "reasons":reasons}


def summarize(rows):
    return {m:counts(rows,m) for m in MODES}


def run(directory):
    entries={x["file"]:x for x in verify(ROOT)}
    def registered(name):
        e=entries[name]
        return e,json.loads((ROOT/e["file"]).read_text(encoding="utf-8"))
    cohort,old=registered("paderborn_cohort_summary.json")
    docs,previous=registered("paderborn_documents_summary.json")
    intake,pilot=registered("paderborn_intake_summary.json")
    policy,ref=registered("mfpt_transfer_summary.json")
    if previous["cohort_blob_sha"]!=cohort["blob_sha"] or ref["score_floor"]!=FLOOR or ref["margin_threshold"]!=MARGIN:
        raise ValueError("Registered source or frozen rule mismatch")
    registry={r["specimen"]:r for r in load_registry()}
    pilots={x["filename"]:x["sha256"] for a in pilot["archives"] for x in a["selected_recordings"]}
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    def inspect(expected):
        specimen=expected["specimen"]
        row=registry[specimen]
        path,meta=acquire_pinned(row,directory)
        try:
            if meta["sha256"]!=expected["sha256"]:
                raise ValueError("Registered archive changed")
            doc=next(x for x in expected["non_mat_members"] if Path(x["name"]).name==specimen+".pdf")
            raw=member_bytes(path,doc["name"])
            if hashlib.sha256(raw).hexdigest()!=doc["sha256"]:
                raise ValueError("Registered fact sheet changed")
            prior=next(x for x in previous["specimen_records"] if x["specimen"]==specimen)
            prior=next(x for x in prior["documents"] if x["kind"]=="fact_sheet")
            fields,orders=geometry_candidate(raw,prior["geometry"])
            with rarfile.RarFile(path) as archive:
                found=inventory(specimen,[(i.filename,i.file_size) for i in archive.infolist() if not i.isdir()])
            records=[]
            for condition in CONDITIONS:
                name=f"{condition}_{specimen}_1.mat"
                raw=member_bytes(path,found[name])
                digest=hashlib.sha256(raw).hexdigest()
                if name in pilots and digest!=pilots[name]:
                    raise ValueError("Registered pilot waveform changed")
                result=evaluate(raw,name,condition,orders)
                records.append({"specimen":specimen,"filename":name,"condition":condition,
                                "sha256":digest,"structural_pilot":row["structural_pilot"],
                                **result,"truth":row["label"]})
            return {"specimen":specimen,"geometry_candidates":fields,"orders":orders,
                    "geometry_visually_verified":False,"records":records}
        finally:
            path.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        specimens=list(pool.map(inspect,old["archives"]))
    rows=[x for s in specimens for x in s["records"]]
    if len(rows)!=68 or len(specimens)!=17:
        raise ValueError("Frozen cohort mismatch")
    return {"scope":"paderborn_conditional_timing_transfer_not_calibrated_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "cohort_blob_sha":cohort["blob_sha"],"documents_blob_sha":docs["blob_sha"],
            "intake_blob_sha":intake["blob_sha"],"policy_blob_sha":policy["blob_sha"],
            "score_floor":FLOOR,"margin_threshold":MARGIN,"specimens":len(specimens),
            "recordings":len(rows),"nonpilot_recordings":sum(not r["structural_pilot"] for r in rows),
            "complete_geometry_candidates":sum(s["orders"] is not None for s in specimens),
            "geometry_visually_verified":False,"clock_verified":False,"operational_authorization":False,
            "overall":summarize(rows),
            "nonpilot":summarize([r for r in rows if not r["structural_pilot"]]),
            "by_condition":{c:summarize([r for r in rows if r["condition"]==c]) for c in CONDITIONS},
            "agreement":sum(r["nominal"]["suggestion"]==r["stored_time"]["suggestion"] for r in rows),
            "both_accept_same":sum(r["nominal"]["suggestion"] is not None and r["nominal"]["suggestion"]==r["stored_time"]["suggestion"] for r in rows),
            "specimen_summaries":[{"specimen":s["specimen"],"geometry_candidates":s["geometry_candidates"],
                                  "orders":s["orders"],"metrics":summarize(s["records"])} for s in specimens],
            "records":rows}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=run(args.directory)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="records"},indent=2,allow_nan=False))
