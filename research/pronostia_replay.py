"""Generate compact, measured vibration-feature replay; no raw waveform redistribution."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from research.pronostia_replication import FIT, TEST, load_features
from research.xjtu_bearing_audit import prepare
from research.xjtu_signal_gate import vibration_ratio, combine
from research.cmapss_stage_audit import age_conditioned

DEMO = ("Bearing1_3", "Bearing2_3", "Bearing3_3")
CADENCE = 20
FEATURES = ("horizontal_rms", "vertical_rms", "horizontal_crest", "vertical_crest")


def replay(frame, cadence=CADENCE):
    if not isinstance(cadence,int) or cadence<1:
        raise ValueError("Positive integer display cadence required")
    data=prepare(frame)
    if set(data.bearing)!=FIT|TEST:
        raise ValueError("Unexpected population")
    fit=data.bearing.isin(FIT)
    x=data.drop(columns=["bearing","condition"])
    training=data.loc[fit]
    life=training.groupby("bearing").age.max()
    y=training.bearing.map(life)-training.age
    weights=1/training.groupby("bearing").age.transform("size").to_numpy()
    weights*=len(weights)/weights.sum()
    model=HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
    model.fit(x.loc[fit],y,sample_weight=weights)
    ratio=vibration_ratio(data)
    traces=[]
    for bearing in DEMO:
        held=data.loc[data.bearing.eq(bearing)]
        end=int(held.age.max())
        # Display cadence only; the causal gate uses every recorded observation.
        shown=held.loc[(held.age<end)&((held.age<=5)|(held.age%cadence==0)|(held.age==end-1))]
        idx=shown.index
        ref=age_conditioned(life.to_numpy(),shown.age)
        learned=np.maximum(0,model.predict(x.loc[idx]))
        ratios=ratio.loc[idx].to_numpy()
        forecasts=combine(ref,learned,ratios)
        points=[]
        for k,(_,row) in enumerate(shown.iterrows()):
            points.append({"age":int(row.age), **{f:float(row[f]) for f in FEATURES if f in row},
                           "ratio":float(ratios[k]),
                           **{m:float(forecasts[m][k]) for m in ("age_reference","learned","switch_2x","ramp_2x_4x")}})
        traces.append({"bearing":bearing,"condition":int(held.condition.iloc[0]),
                       "last_recorded_age":end,"points":points})
    return {"fit_bearings":sorted(FIT),"display_cadence_snapshots":cadence,
            "recording_interval_seconds":10,"traces":traces}


def run(path):
    digest=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return {"archive_sha256":digest.hexdigest(), **replay(load_features(path)),
            "scope":"Illustrative replay of measured vibration-derived features from three previously evaluated PRONOSTIA laboratory bearings; no new validation, operational alert or raw waveform claim. Display subsampling is not the input cadence."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().archive),indent=2,allow_nan=False))
