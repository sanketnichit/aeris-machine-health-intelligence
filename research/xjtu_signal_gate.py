"""Exploratory signal-gated forecasting on already-observed XJTU development data.

The gate uses observed vibration only; lifetime fractions select scoring rows,
never predictions. Observable landmark comparisons are reported separately.
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
from research.xjtu_bearing_audit import load_features, prepare, metrics, STAGES

LANDMARKS = (20, 50, 100, 200, 500, 1000)
MODELS = ("age_reference", "learned", "switch_2x", "switch_4x", "ramp_2x_4x")


def vibration_ratio(frame):
    """Largest channel ratio: trailing 5 median / first 5 median.

    Before five observations are available return 1 (baseline only).
    The first five observations are used only from cycle five onward.
    """
    data = frame.sort_values(["bearing", "age"])
    ratios = pd.Series(1., index=data.index)
    for _, group in data.groupby("bearing", sort=False):
        channels = group[["horizontal_rms", "vertical_rms"]].to_numpy(dtype=float)
        if not np.isfinite(channels).all() or (channels < 0).any():
            raise ValueError("Expected finite nonnegative RMS")
        if len(group) < 5:
            continue
        baseline = np.maximum(np.median(channels[:5], axis=0), 1e-12)
        trailing = group[["horizontal_rms", "vertical_rms"]].rolling(5, min_periods=5).median()
        ratios.loc[group.index[4:]] = np.maximum(1., (trailing.iloc[4:].to_numpy()/baseline).max(axis=1))
    return ratios.reindex(frame.index)


def combine(reference, learned, ratio):
    a, b, r = (np.asarray(v, dtype=float) for v in (reference, learned, ratio))
    if a.ndim != 1 or a.shape != b.shape or a.shape != r.shape or not all(np.isfinite(v).all() for v in (a,b,r)) or (a<0).any() or (b<0).any() or (r<1).any():
        raise ValueError("Invalid gate inputs")
    w = np.clip((r-2)/2,0,1)
    return {"age_reference":a, "learned":b, "switch_2x":np.where(r>=2,b,a),
            "switch_4x":np.where(r>=4,b,a), "ramp_2x_4x":(1-w)*a+w*b}


def evaluate(frame, landmarks=LANDMARKS):
    data = prepare(frame)
    ratio = vibration_ratio(data)
    y = data.groupby("bearing").age.transform("max")-data.age
    x = data.drop(columns=["bearing","condition"])
    rows = []
    for split in ("bearing","condition"):
        for fit,ev in LeaveOneGroupOut().split(x,y,data[split]):
            fitted, held = data.iloc[fit], data.iloc[ev]
            life = fitted.groupby("bearing").age.max().to_numpy()
            weights = 1/fitted.groupby("bearing").age.transform("size").to_numpy()
            weights *= len(weights)/weights.sum()
            model = HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
            model.fit(x.iloc[fit],y.iloc[fit],sample_weight=weights)
            for bearing,g in held.groupby("bearing"):
                endpoints = [("stage",str(s),g.index[int(np.ceil(len(g)*s))-1]) for s in STAGES]
                # Exclude last recording from observable landmarks.
                endpoints += [("landmark",str(a),g.index[a-1]) for a in landmarks if 1<=a<len(g)]
                idx = [i for _,_,i in endpoints]
                r = ratio.loc[idx].to_numpy()
                p = np.maximum(0,model.predict(x.loc[idx]))
                ref = age_conditioned(life,data.loc[idx,"age"])
                forecasts = combine(ref,p,r)
                for k,(kind,point,i) in enumerate(endpoints):
                    rows.append(dict(split=split,bearing=bearing,kind=kind,point=point,
                                     age=int(data.loc[i,"age"]),actual=float(y.loc[i]),ratio=float(r[k]),
                                     fit_bearings=sorted(fitted.bearing.unique().tolist()),
                                     **{m:float(v[k]) for m,v in forecasts.items()}))
    table = pd.DataFrame(rows)
    summary = {}
    for split,g in table.groupby("split"):
        summary[split] = {}
        for kind,h in g.groupby("kind"):
            by_point = {}
            for point,j in h.groupby("point"):
                by_point[point] = {"bearings":int(j.bearing.nunique()),
                                   "gate_2x_fraction":float(j.ratio.ge(2).mean()),
                                   "gate_4x_fraction":float(j.ratio.ge(4).mean()),
                                   "metrics":{m:metrics(j.actual,j[m]) for m in MODELS}}
            item = {"by_point":by_point}
            if kind=="stage":
                item["all"] = {m:metrics(h.actual,h[m]) for m in MODELS}
            summary[split][kind] = item
    return {"summary":summary,"predictions":rows}


def run(path):
    digest = hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return {"archive_sha256":digest.hexdigest(), **evaluate(load_features(path)),
            "scope":"Exploratory development on previously observed XJTU data. Gates 2x/4x are heuristic, not optimized; no model selection, independent confirmation, or operational safety claim. Landmark populations differ by survival."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().archive),indent=2,allow_nan=False))
