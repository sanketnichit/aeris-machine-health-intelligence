"""Exploratory selective forecasting on previously observed XJTU bearings.

Fixed landmark-specific split conformal calibration; small calibration groups
cannot yield finite 90% intervals. Under condition shift no coverage guarantee.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut

from research.cmapss_stage_audit import age_conditioned
from research.xjtu_bearing_audit import load_features, prepare
from research.xjtu_signal_gate import vibration_ratio, combine, LANDMARKS
from src.forecast_reliability import assess_forecast, selective_metrics
from src.rul_uncertainty import conformal_radius


def calibration_partition(data, split, fold):
    ids=np.sort(data.bearing.unique())
    if split=="condition":
        groups=sorted(data.condition.unique())
        if len(groups)!=2:
            raise ValueError("Expected two remaining operating conditions")
        cal=np.sort(data.loc[data.condition.eq(groups[fold%2]),"bearing"].unique())
    else:
        if len(ids)<6:
            raise ValueError("Need at least six development bearings")
        cal=np.random.default_rng(100+fold).permutation(ids)[:5]
    return np.setdiff1d(ids,cal),np.sort(cal)


def evaluate(frame, landmarks=LANDMARKS):
    data=prepare(frame)
    x=data.drop(columns=["bearing","condition"])
    y=data.groupby("bearing").age.transform("max")-data.age
    ratio=vibration_ratio(data)
    rows=[]
    for split in ("bearing","condition"):
        for fold,(dev,ev) in enumerate(LeaveOneGroupOut().split(x,y,data[split])):
            fit_ids,cal_ids=calibration_partition(data.iloc[dev],split,fold)
            fit=data.bearing.isin(fit_ids)
            cal=data.bearing.isin(cal_ids)
            held=data.iloc[ev]
            life=data.loc[fit].groupby("bearing").age.max().to_numpy()
            scale=float(np.median(life))
            weights=1/data.loc[fit].groupby("bearing").age.transform("size").to_numpy()
            weights*=len(weights)/weights.sum()
            model=HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
            model.fit(x.loc[fit],y.loc[fit],sample_weight=weights)

            def predict(idx):
                ref=age_conditioned(life,data.loc[idx,"age"])
                learned=np.maximum(0,model.predict(x.loc[idx]))
                adaptive=combine(ref,learned,ratio.loc[idx].to_numpy())["ramp_2x_4x"]
                return ref,learned,adaptive

            for age in landmarks:
                ci=data.index[cal & data.age.eq(age) & y.gt(0)]
                ei=held.index[held.age.eq(age) & y.loc[held.index].gt(0)]
                if not len(ei):
                    continue
                ref,learned,pred=predict(ei)
                radii={}
                for alpha in (.1,.2):
                    radii[str(alpha)]=None
                    if len(ci) and np.ceil((len(ci)+1)*(1-alpha))<=len(ci):
                        radii[str(alpha)]=conformal_radius(y.loc[ci],predict(ci)[2],alpha)
                for i,r,l,p in zip(ei,ref,learned,pred):
                    decision=assess_forecast(r,l,p,radii["0.2"],observed=age,scale=scale)
                    rows.append(dict(split=split,fold=fold,bearing=data.loc[i,"bearing"],age=int(age),
                                     actual=float(y.loc[i]),reference=float(r),
                                     fit_bearings=fit_ids.tolist(),calibration_bearings=cal_ids.tolist(),
                                     calibration_survivors=len(ci),radii=radii,**decision))
    table=pd.DataFrame(rows)
    summary={}
    for (split,age),g in table.groupby(["split","age"]):
        accepted=g.status.eq("forecast_available")
        available=g.lower.notna()
        covered=(g.actual>=g.lower)&(g.actual<=g.upper) if available.any() else pd.Series(False,index=g.index)
        summary.setdefault(split,{})[str(age)]={
            **selective_metrics(g.actual,g.candidate,accepted),
            "reference_mae":float(np.abs(g.actual-g.reference).mean()),
            "interval_endpoints":int(available.sum()),
            "interval_coverage":float(covered[available].mean()) if available.any() else None,
            "finite_90_percent_intervals":sum(r["0.1"] is not None for r in g.radii),
            "reason_counts":{reason:int(sum(reason in x for x in g.reasons)) for reason in
                ("insufficient_history","insufficient_calibration","wide_interval","model_disagreement")}}
    return {"summary":summary,"predictions":rows}


def run(path):
    digest=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return {"archive_sha256":digest.hexdigest(),**evaluate(load_features(path)),
            "scope":"Exploratory selective forecasting, nominal 80% marginal intervals only under exchangeability; no coverage guarantee across conditions or after selection. No deployment safety claim."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().archive),indent=2,allow_nan=False))
