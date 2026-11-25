"""Training trajectories only: unit-disjoint regime and abstention development."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from src.prognostics import load_trajectories, training_targets
from src.regime_prognostics import RegimeFeatures, finite_radius, forecast_gate
from research.cmapss_stage_audit import relative_features, age_conditioned
from research.cmapss_risk_audit import risk_metrics
from research.verify_evidence import ROOT, verify

LANDMARKS=(50,100,150)
CLUSTERS={"FD001":1,"FD002":6,"FD003":1,"FD004":6}
WIDTH_LIMIT=80.
ALPHA=.1


def split_units(frame):
    units=np.sort(frame.unit.unique())
    if len(units)<45:
        raise ValueError("Insufficient training engines")
    order=np.random.default_rng(271).permutation(units)
    a,b=int(.6*len(order)),int(.8*len(order))
    return {k:sorted(map(int,v)) for k,v in zip(("fit","calibration","evaluation"),(order[:a],order[a:b],order[b:]))}


def fit(frame,clusters):
    features=RegimeFeatures(clusters).fit(frame)
    x,_=features.transform(frame)
    y=training_targets(frame)
    models={}
    for key,values in (("relative",relative_features(frame)),("regime",x)):
        m=HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
        m.fit(values,y)
        models[key]=m
    return features,models,frame.groupby("unit").cycle.max().to_numpy()


def predict(bundle,frame):
    f,models,lifetimes=bundle
    x,distance=f.transform(frame)
    return {"relative":np.maximum(0,models["relative"].predict(relative_features(frame))),
            "regime":np.maximum(0,models["regime"].predict(x)),
            "age":age_conditioned(lifetimes,frame.cycle.to_numpy()),"distance":distance}


def part(frame,units):
    return frame[frame.unit.isin(units)].reset_index(drop=True)


def summarize(rows):
    n=len(rows)
    if not n:
        return {"endpoints":0,"accepted":0,"coverage":None,"accepted_mae":None,
                "accepted_interval_coverage":None,"support_rejected":0,"reasons":{}}
    y=np.array([r["actual"] for r in rows])
    accepted=[r for r in rows if r["advisory"]["forecast"] is not None]
    reasons={}
    for r in rows:
        k=r["advisory"]["reason"] or "accepted"
        reasons[k]=reasons.get(k,0)+1
    interval_rows=[r for r in rows if r["interval_hit"] is not None]
    return {"endpoints":n,"accepted":len(accepted),"coverage":len(accepted)/n,
            "metrics":{k:risk_metrics(y,np.array([r[k] for r in rows])) for k in ("age","relative","regime")},
            "support_rejected":sum(not r["settings_supported"] for r in rows),
            "raw_interval_endpoints":len(interval_rows),
            "raw_interval_coverage":None if not interval_rows else sum(r["interval_hit"] for r in interval_rows)/len(interval_rows),
            "accepted_mae":None if not accepted else float(np.mean([abs(r["actual"]-r["regime"]) for r in accepted])),
            "accepted_interval_coverage":None if not accepted else sum(r["interval_hit"] for r in accepted)/len(accepted),
            "accepted_over20":sum(r["regime"]-r["actual"]>20 for r in accepted),"reasons":reasons}


def run(directory):
    entries={r["file"]:r for r in verify(ROOT)}
    prior=entries["cmapss_multiregime_summary.json"]
    registered=json.loads((ROOT/prior["file"]).read_text(encoding="utf-8"))
    frames={}; hashes={}; splits={}
    for subset in CLUSTERS:
        name=f"train_{subset}.txt"
        path=Path(directory)/name
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes[name]!=registered["dataset_sha256"][name]:
            raise ValueError("Training fingerprint mismatch")
        frames[subset]=load_trajectories(path)
        splits[subset]=split_units(frames[subset])
    bundles={s:fit(part(frames[s],splits[s]["fit"]),CLUSTERS[s]) for s in CLUSTERS}
    scenarios=[]
    for source,bundle in bundles.items():
        cal=part(frames[source],splits[source]["calibration"])
        cp=predict(bundle,cal)
        cy=training_targets(cal).to_numpy()
        radii={}
        for age in LANDMARKS:
            idx=np.flatnonzero(cal.cycle.to_numpy()==age)
            radii[age]=(finite_radius(cp["distance"][idx],ALPHA),
                        finite_radius(np.abs(cy[idx]-cp["regime"][idx]),ALPHA),len(idx))
        for target in CLUSTERS:
            if source!=target and source!="FD001":
                continue
            ev=part(frames[target],splits[target]["evaluation"])
            ep=predict(bundle,ev)
            ey=training_targets(ev).to_numpy()
            for age in LANDMARKS:
                sr,ir,ncal=radii[age]
                rows=[]
                for i in np.flatnonzero(ev.cycle.to_numpy()==age):
                    p=float(ep["regime"][i]); y=float(ey[i]); dist=float(ep["distance"][i])
                    advisory=forecast_gate(p,dist,sr,ir,domain_matches=source==target,width_limit=WIDTH_LIMIT)
                    rows.append({"unit":int(ev.unit.iloc[i]),"actual":y,"regime":p,
                                 "relative":float(ep["relative"][i]),"age":float(ep["age"][i]),
                                 "prefix_distance":dist,"settings_supported":sr is not None and dist<=sr,
                                 "interval_hit":None if ir is None else max(0,p-ir)<=y<=p+ir,
                                 "advisory":advisory})
                scenarios.append({"source":source,"target":target,"landmark":age,
                                  "calibration_survivors":ncal,"support_radius":sr,"interval_radius":ir,
                                  **summarize(rows),"records":rows})
    return {"scope":"training_only_unit_disjoint_regime_development_not_independent_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "multiregime_blob_sha":prior["blob_sha"],"training_sha256":hashes,
            "landmarks":list(LANDMARKS),"alpha":ALPHA,"width_limit_cycles":WIDTH_LIMIT,
            "splits":splits,"scenario_count":len(scenarios),"scenarios":scenarios}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.data_dir)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**report,"scenarios":[{k:v for k,v in s.items() if k!="records"} for s in report["scenarios"]]},indent=2,allow_nan=False))
