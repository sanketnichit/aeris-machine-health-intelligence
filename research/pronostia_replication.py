"""Independent physical method replication; no tuning on evaluation bearings."""
import argparse
import hashlib
import io
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from research.cmapss_stage_audit import age_conditioned
from research.xjtu_bearing_audit import vibration_features, prepare, metrics, STAGES
from research.xjtu_signal_gate import vibration_ratio, combine, LANDMARKS, MODELS

# Sensors 2021, 21, 6325, Table 2: complete recording counts.
COUNTS = {f"Bearing{c}_{b}": n for c, counts in enumerate(
    ((2803,871,2375,1428,2463,2448,2259),
     (911,797,1955,751,2311,701,230),
     (515,1637,434)),1) for b,n in enumerate(counts,1)}
FIT = {f"Bearing{c}_{b}" for c in range(1,4) for b in (1,2)}
TEST = set(COUNTS)-FIT
MEMBER = re.compile(r"(?:^|/)(Learning_set|Full_Test_Set)/Bearing([1-3])_([1-7])/acc_(\d+)\.csv$",re.I)


def decode_snapshot(raw):
    # Acceleration recordings have no header; first four columns are timestamps.
    sep = ";" if b";" in raw.splitlines()[0] else ","
    data = pd.read_csv(io.BytesIO(raw), sep=sep, header=None)
    if data.shape != (2560,6):
        raise ValueError(f"Unexpected recording shape: {data.shape}")
    return vibration_features(data.iloc[:,4:6].to_numpy(dtype=float), expected_samples=2560)


def extract_archive(archive, rows, seen, depth=0, prefix=""):
    """Carry nested archive names into the logical path, with bounded recursion."""
    for member in archive.infolist():
        if member.is_dir():
            continue
        name=prefix+member.filename.replace("\\","/")
        if name.lower().endswith(".zip"):
            if depth>=5 or member.file_size>8*1024**3:
                raise ValueError("Unexpected nested archive")
            # Stream nested archives to disk, not RAM; never extract arbitrary paths.
            with tempfile.TemporaryFile() as temp, archive.open(member) as source:
                shutil.copyfileobj(source,temp)
                temp.seek(0)
                with zipfile.ZipFile(temp) as nested:
                    extract_archive(nested,rows,seen,depth+1,name[:-4]+"/")
            continue
        match=MEMBER.search(name)
        if not match:
            continue
        partition,c,b,age=match.groups()
        bearing=f"Bearing{c}_{b}"
        age=int(age)
        expected=FIT if partition.lower()=="learning_set" else TEST
        if bearing not in expected or (bearing,age) in seen or age<1 or member.file_size>1024**2:
            raise ValueError(f"Unexpected or duplicate recording: {name}")
        seen.add((bearing,age))
        rows.append(dict(bearing=bearing,condition=int(c),age=age,
                         **decode_snapshot(archive.read(member))))


def load_features(path):
    rows,seen=[],set()
    with zipfile.ZipFile(path) as archive:
        extract_archive(archive,rows,seen)
    required={(b,a) for b,n in COUNTS.items() for a in range(1,n+1)}
    if seen!=required:
        observed={b:sum(1 for k,_ in seen if k==b) for b in COUNTS}
        raise ValueError(f"Full-life recording contract failed: {observed}")
    return pd.DataFrame(rows)


def evaluate(frame):
    data=prepare(frame)
    if set(data.bearing)!=FIT|TEST:
        raise ValueError("Unexpected population")
    fit=data.bearing.isin(FIT)
    x=data.drop(columns=["bearing","condition"])
    fit_rows=data.loc[fit]
    fit_life=fit_rows.groupby("bearing").age.max()
    y=fit_rows.bearing.map(fit_life)-fit_rows.age
    w=1/fit_rows.groupby("bearing").age.transform("size").to_numpy()
    w*=len(w)/w.sum()
    model=HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False)
    model.fit(x.loc[fit],y,sample_weight=w)
    ratio=vibration_ratio(data)
    rows=[]
    for bearing,g in data.loc[~fit].groupby("bearing"):
        points=[("stage",str(s),g.index[int(np.ceil(len(g)*s))-1]) for s in STAGES]
        points += [("landmark",str(a),g.index[a-1]) for a in LANDMARKS if a<len(g)]
        idx=[i for _,_,i in points]
        ref=age_conditioned(fit_life.to_numpy(),data.loc[idx,"age"])
        pred=np.maximum(0,model.predict(x.loc[idx]))
        forecasts=combine(ref,pred,ratio.loc[idx].to_numpy())
        for k,(kind,point,i) in enumerate(points):
            age=int(data.loc[i,"age"])
            rows.append(dict(bearing=bearing,kind=kind,point=point,age=age,
                actual=int(g.age.max())-age,ratio=float(ratio.loc[i]),
                **{m:float(v[k]) for m,v in forecasts.items()}))
    table=pd.DataFrame(rows)
    stages=table.loc[table.kind=="stage"]
    summary={"stage":{"all":{m:metrics(stages.actual,stages[m]) for m in MODELS},
             "by_bearing":{b:{m:metrics(g.actual,g[m]) for m in MODELS} for b,g in stages.groupby("bearing")}},
             "landmark":{}}
    for kind,g in table.groupby("kind"):
        summary[kind]["by_point"]={p:{"bearings":int(h.bearing.nunique()),
            "metrics":{m:metrics(h.actual,h[m]) for m in MODELS}} for p,h in g.groupby("point")}
    return {"fit_bearings":sorted(FIT),"evaluation_bearings":sorted(TEST),"primary":"switch_2x",
            "summary":summary,"predictions":rows}


def run(path):
    digest=hashlib.sha256()
    with open(path,"rb") as source:
        for block in iter(lambda:source.read(1024*1024),b""):
            digest.update(block)
    data=load_features(path)
    return {"archive_sha256":digest.hexdigest(),"snapshot_counts":data.groupby("bearing").size().to_dict(),
            **evaluate(data),"scope":"Independent physical platform, fixed method replication on complete held-out bearing histories; not official challenge scoring or field validation."}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().archive),indent=2,allow_nan=False))
