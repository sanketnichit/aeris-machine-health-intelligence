"""Exploratory measured vibration-state forecasting, not physical damage calibration."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.pronostia_replication import FIT, TEST, load_features
from research.xjtu_bearing_audit import metrics
from research.xjtu_signal_gate import vibration_ratio

HORIZON=20
LANDMARKS=(50,100,200,500,1000,2000)


def weighted_quantile(values,weights,q):
    values=np.asarray(values,dtype=float)
    weights=np.asarray(weights,dtype=float)
    if values.ndim!=1 or values.shape!=weights.shape or not len(values) or not np.isfinite(values).all() or not np.isfinite(weights).all() or (weights<=0).any() or not 0<=q<=1:
        raise ValueError("Invalid weighted quantile")
    order=np.argsort(values,kind="stable")
    cdf=np.cumsum(weights[order])
    return float(values[order[min(np.searchsorted(cdf,q*cdf[-1]),len(order)-1)]])


def states(frame):
    data=frame.sort_values(["bearing","age"]).reset_index(drop=True).copy()
    for bearing,g in data.groupby("bearing"):
        if len(g)<5 or not np.array_equal(g.age.to_numpy(),np.arange(1,len(g)+1)):
            raise ValueError(f"Noncontiguous bearing history: {bearing}")
        if g.condition.nunique()!=1:
            raise ValueError("Unexpected condition change")
    data["state"]=np.log(vibration_ratio(data))
    return data


def fit_drift(transitions):
    weights=1/transitions.groupby("bearing").delta.transform("size").to_numpy()
    delta=transitions.delta.to_numpy()
    center=weighted_quantile(delta,weights,.5)
    return {"drift":center,"residual_p05":weighted_quantile(delta-center,weights,.05),
            "residual_p95":weighted_quantile(delta-center,weights,.95),
            "fit_bearings":sorted(transitions.bearing.unique().tolist()),
            "transitions":len(transitions)}


def summarize(rows):
    if not rows:
        return None
    data=pd.DataFrame(rows)
    y=data.actual.to_numpy()
    result={m:metrics(y,data[m]) for m in ("persistence","global_drift","condition_drift")}
    result["condition_band"]={"coverage":float(((data.lower<=y)&(y<=data.upper)).mean()),
                              "mean_width":float((data.upper-data.lower).mean())}
    result["bearings"]=int(data.bearing.nunique())
    return result


def evaluate(frame,landmarks=LANDMARKS):
    data=states(frame)
    if set(data.bearing)!=FIT|TEST:
        raise ValueError("Unexpected population")
    transitions=[]
    for bearing,g in data.loc[data.bearing.isin(FIT)].groupby("bearing"):
        x=g.state.to_numpy()
        for a in range(5,len(g)-HORIZON+1,HORIZON):
            transitions.append({"bearing":bearing,"condition":int(g.condition.iloc[0]),
                                "delta":float(x[a+HORIZON-1]-x[a-1])})
    t=pd.DataFrame(transitions)
    global_fit=fit_drift(t)
    fits={int(c):fit_drift(g) for c,g in t.groupby("condition")}
    rows=[]
    for bearing,g in data.loc[data.bearing.isin(TEST)].groupby("bearing"):
        x=g.state.to_numpy()
        condition=int(g.condition.iloc[0])
        model=fits[condition]
        for age in landmarks:
            if age<5 or age+HORIZON>len(g):
                continue
            current=float(x[age-1])
            actual=float(x[age+HORIZON-1])
            candidate=current+model["drift"]
            rows.append({"bearing":bearing,"condition":condition,"age":age,"actual":actual,
                         "persistence":current,"global_drift":max(0.,current+global_fit["drift"]),
                         "condition_drift":max(0.,candidate),
                         "lower":max(0.,candidate+model["residual_p05"]),
                         "upper":max(0.,candidate+model["residual_p95"])})
    if not rows:
        raise ValueError("No eligible evaluation endpoints")
    by_bearing={b:summarize([r for r in rows if r["bearing"]==b]) for b in sorted(TEST)}
    differences={b:v["condition_drift"]["mae"]-v["persistence"]["mae"]
                 for b,v in by_bearing.items() if v is not None}
    return {"fit":global_fit,"condition_fit":fits,"evaluation_bearings":sorted(TEST),
            "horizon_recordings":HORIZON,"primary":"condition_drift",
            "summary":{"all":summarize(rows),"by_bearing":by_bearing,
                       "by_landmark":{str(a):summarize([r for r in rows if r["age"]==a]) for a in landmarks},
                       "paired_bearing_mae_differences":differences,
                       "mean_paired_bearing_mae_difference":float(np.mean(list(differences.values())))},
            "predictions":rows}


def run(path):
    digest=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            digest.update(block)
    return {"archive_sha256":digest.hexdigest(),**evaluate(load_features(path)),
            "scope":"Exploratory held-out short-horizon vibration proxy prediction on previously observed PRONOSTIA populations. No calibrated damage state, RUL, physical twin or real-world coverage claim."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().archive),indent=2,allow_nan=False))
