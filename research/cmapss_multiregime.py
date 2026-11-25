"""Frozen multi-regime NASA C-MAPSS endpoint transfer audit.

All point predictions for all subsets are generated before any official offsets
are parsed. This is simulator evaluation, not physical fleet validation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from research.cmapss_stage_audit import relative_features, age_conditioned
from research.cmapss_risk_audit import age_blend, risk_metrics
from research.cmapss_official import paired_delta
from research.verify_evidence import ROOT, verify
from scripts.download_cmapss_all import SUBSETS, ARCHIVE_SHA256, extract
from src.prognostics import load_trajectories, training_targets, endpoint_indices, endpoint_targets

POPULATIONS={"FD001":(100,100),"FD002":(260,259),"FD003":(100,100),"FD004":(249,248)}
PRIMARY="relative_hgb"


def fit_candidates(train):
    x,y=relative_features(train),training_targets(train)
    snapshot=[c for c in x if not c.endswith(("_mean","_delta","_relative"))]
    models={}
    for name,cols in (("snapshot_hgb",snapshot),("relative_hgb",list(x.columns))):
        model=HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
        model.fit(x[cols],y)
        models[name]=(model,cols)
    return {"models":models,"lifetimes":train.groupby("unit").cycle.max().to_numpy(),
            "constant":float(np.median(y))}


def predict(fitted,test):
    x=relative_features(test)
    idx=endpoint_indices(test)
    age=test.loc[idx,"cycle"].to_numpy()
    ref=age_conditioned(fitted["lifetimes"],age)
    predictions={"age_reference":ref,"constant":np.full(len(idx),fitted["constant"])}
    for name,(model,cols) in fitted["models"].items():
        predictions[name]=np.maximum(0,model.predict(x.loc[idx,cols]))
    predictions["adaptive_mean"]=age_blend(age,ref,predictions[PRIMARY])
    return test.loc[idx,"unit"].to_numpy(),age,predictions


def verified_files(root):
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    payload=(root/"source.zip").read_bytes()
    files=extract(payload)
    hashes={n:hashlib.sha256(data).hexdigest() for n,data in files.items()}
    if manifest.get("archive_sha256")!=ARCHIVE_SHA256 or manifest.get("files")!=hashes:
        raise ValueError("Dataset manifest mismatch")
    if any((root/n).read_bytes()!=data for n,data in files.items()):
        raise ValueError("Extracted member mismatch")
    return hashes


def run(root):
    root=Path(root)
    hashes=verified_files(root)
    registered={x["file"]:x for x in verify(ROOT)}
    original=registered["official_summary.json"]
    prior=json.loads((ROOT/original["file"]).read_text(encoding="utf-8"))
    if prior["primary"]!=PRIMARY:
        raise ValueError("Frozen primary mismatch")
    train={s:load_trajectories(root/f"train_{s}.txt") for s in SUBSETS}
    test={s:load_trajectories(root/f"test_{s}.txt") for s in SUBSETS}
    for s in SUBSETS:
        if (train[s].unit.nunique(),test[s].unit.nunique())!=POPULATIONS[s]:
            raise ValueError(f"Unexpected population: {s}")
    anchor=fit_candidates(train["FD001"])
    predictions={}
    for s in SUBSETS:
        predictions[(s,"fd001_transfer")]=predict(anchor,test[s])
        if s!="FD001":
            predictions[(s,"within_subset")]=predict(fit_candidates(train[s]),test[s])
    # Predictions are frozen in memory for every scenario before parsing labels.
    rows=[]
    for s in SUBSETS:
        actual=endpoint_targets(test[s],root/f"RUL_{s}.txt")
        for (subset,mode),(units,ages,pred) in predictions.items():
            if subset!=s:
                continue
            truth=actual.reindex(units).to_numpy()
            metrics={k:risk_metrics(truth,v) for k,v in pred.items()}
            rows.append({"subset":s,"mode":mode,
                         "training_subset":"FD001" if mode=="fd001_transfer" else s,
                         "train_engines":POPULATIONS["FD001" if mode=="fd001_transfer" else s][0],
                         "test_engines":len(units),"metrics":metrics,
                         "paired_primary_vs_age":paired_delta(truth,pred[PRIMARY],pred["age_reference"]),
                         "predictions":[{"unit":int(u),"cycle":int(a),"actual":float(y),
                                         **{k:float(v[i]) for k,v in pred.items()}}
                                        for i,(u,a,y) in enumerate(zip(units,ages,truth))]})
    fd001=rows[0]
    if fd001["subset"]!="FD001" or fd001["test_engines"]!=prior["engines"]:
        raise ValueError("FD001 control population mismatch")
    # Report version-related drift, never rewrite the historical official result.
    drift={k:fd001["metrics"][k]["mae"]-prior["metrics"][k]["mae"] for k in fd001["metrics"]}
    if any(abs(v)>1e-6 for v in drift.values()):
        raise ValueError(f"Frozen FD001 control failed to reproduce: {drift}")
    return {"scope":"official_simulated_cmapss_multiregime_endpoint_transfer_not_field_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "official_fd001_blob_sha":original["blob_sha"],"archive_sha256":ARCHIVE_SHA256,
            "dataset_sha256":hashes,"primary":PRIMARY,"fd001_mae_drift":drift,
            "unique_test_engines":sum(POPULATIONS[s][1] for s in SUBSETS),
            "new_subset_test_engines":sum(POPULATIONS[s][1] for s in SUBSETS if s!="FD001"),
            "endpoint_evaluations":sum(row["test_engines"] for row in rows),
            "scenarios":rows}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.data_dir)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in row.items() if k!="predictions"} for row in report["scenarios"]]},indent=2,allow_nan=False))
