"""XJTU-SY physical bearing development audit; no raw-data extraction."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut

from research.cmapss_stage_audit import age_conditioned

SAMPLES = 32768
EXPECTED = {f" Bearing{c}_{b}".strip() for c in range(1,4) for b in range(1,6)}
STAGES = (.25,.5,.75,.9)
MEMBER = re.compile(r"(?:^|/)Bearing([1-3])_([1-5])/(\d+)\.csv$", re.I)


def vibration_features(values, expected_samples=SAMPLES):
    a = np.asarray(values,dtype=float)
    if a.shape != (expected_samples,2) or not np.isfinite(a).all():
        raise ValueError("Expected finite two-channel vibration snapshot")
    features = {}
    for i,channel in enumerate(("horizontal","vertical")):
        x = a[:,i]
        rms = float(np.sqrt(np.mean(x*x)))
        peak = float(np.max(np.abs(x)))
        centered = x-x.mean()
        variance = float(np.mean(centered**2))
        spectrum = np.abs(np.fft.rfft(centered))**2
        power = float(spectrum.sum())
        features.update({f"{channel}_rms":rms, f"{channel}_peak":peak,
            f"{channel}_crest":peak/rms if rms else 0.,
            f"{channel}_kurtosis":float(np.mean(centered**4)/variance**2) if variance else 0.,
            f"{channel}_high_fraction":float(spectrum[len(spectrum)//2:].sum()/power) if power else 0.})
    return features


def archive_members(archive):
    found = {}
    for item in archive.infolist():
        match = MEMBER.search(item.filename.replace("\\","/"))
        if not match or item.is_dir():
            continue
        c,b,n = map(int,match.groups())
        key = (f"Bearing{c}_{b}",n)
        if n < 1 or key in found or item.file_size > 8*1024*1024:
            raise ValueError(f"Invalid/duplicate snapshot: {item.filename}")
        found[key] = item
    if {b for b,_ in found} != EXPECTED:
        raise ValueError("Expected all 15 bearings in the archive")
    for b in EXPECTED:
        ids = sorted(n for name,n in found if name==b)
        if ids != list(range(1,len(ids)+1)) or len(ids)<4:
            raise ValueError(f"Noncontiguous or too short: {b}")
    return found


def load_features(path):
    rows = []
    with zipfile.ZipFile(path) as archive:
        for (bearing,age), member in sorted(archive_members(archive).items()):
            with archive.open(member) as stream:
                raw = pd.read_csv(stream)
            rows.append(dict(bearing=bearing, condition=int(bearing[7]), age=age,
                             **vibration_features(raw.to_numpy(dtype=float))))
    return pd.DataFrame(rows)


def prepare(frame):
    data = frame.sort_values(["bearing","age"]).reset_index(drop=True).copy()
    for axis in ("horizontal","vertical"):
        name = f"{axis}_rms"
        initial = data.groupby("bearing")[name].transform("first")
        data[f"{axis}_relative_rms"] = (data[name]-initial)/np.maximum(initial,1e-12)
    return data


def metrics(actual,predicted):
    error = np.asarray(predicted)-np.asarray(actual)
    return {"mae":float(np.abs(error).mean()),"rmse":float(np.sqrt(np.mean(error**2))),"endpoints":len(error)}


def evaluate(frame):
    data = prepare(frame)
    life = data.groupby("bearing").age.transform("max")
    y = life-data.age
    cols = [c for c in data if c not in ("bearing","condition")]
    x = data[cols]
    rows=[]
    for split_key in ("bearing","condition"):
        for fit,test in LeaveOneGroupOut().split(x,y,data[split_key]):
            fitted = data.iloc[fit]
            held = data.iloc[test]
            train_life = fitted.groupby("bearing").age.max().to_numpy()
            weights = 1/fitted.groupby("bearing").age.transform("size").to_numpy()
            weights *= len(weights)/weights.sum()
            model = HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
            model.fit(x.iloc[fit],y.iloc[fit],sample_weight=weights)
            for bearing,group in held.groupby("bearing"):
                for stage in STAGES:
                    idx=group.index[int(np.ceil(len(group)*stage))-1]
                    ref=age_conditioned(train_life,[data.loc[idx,"age"]])[0]
                    pred=max(0.,float(model.predict(x.loc[[idx]])[0]))
                    rows.append(dict(split=split_key,bearing=bearing,stage=stage,age=int(data.loc[idx,"age"]),
                                     actual=float(y.loc[idx]),age_reference=float(ref),learned=pred,
                                     fit_bearings=sorted(fitted.bearing.unique().tolist())))
    table=pd.DataFrame(rows)
    summary={}
    for split,g in table.groupby("split"):
        summary[split]={name:{"all":metrics(g.actual,g[name]),
                                "by_stage":{str(s):metrics(h.actual,h[name]) for s,h in g.groupby("stage")},
                                "by_bearing":{str(b):metrics(h.actual,h[name]) for b,h in g.groupby("bearing")}}
                        for name in ("age_reference","learned")}
    return {"summary":summary,"predictions":rows}


def run(path):
    digest=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    data=load_features(path)
    return {"archive_sha256":digest.hexdigest(),"snapshot_counts":data.groupby("bearing").size().to_dict(),
            **evaluate(data),"scope":"Physical accelerated bearing development experiment; retrospective endpoint proxy, no field or safety claim."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().archive),indent=2,allow_nan=False))
