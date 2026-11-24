"""Frozen v1 evaluation; see FD001_OFFICIAL_PROTOCOL.md."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from research.cmapss_stage_audit import age_conditioned, relative_features
from research.cmapss_risk_audit import age_blend, risk_metrics
from src.prognostics import load_trajectories, training_targets, endpoint_indices, endpoint_targets

HASHES = {
    "train_FD001.txt": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
    "test_FD001.txt": "3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851",
    "RUL_FD001.txt": "a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca",
}


def verify(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"Dataset fingerprint mismatch: {path.name}")
    return actual


def predict_endpoints(train, test):
    x, y = relative_features(train), training_targets(train)
    tx = relative_features(test)
    idx = endpoint_indices(test)
    age = test.loc[idx, "cycle"].to_numpy()
    life = train.groupby("unit").cycle.max().to_numpy()
    ref = age_conditioned(life, age)
    pred = {"age_reference": ref, "constant": np.full(len(idx), float(np.median(y)))}
    snapshot = [c for c in x if not c.endswith(("_mean", "_delta", "_relative"))]
    for name, cols in (("snapshot_hgb", snapshot), ("relative_hgb", list(x.columns))):
        model = HistGradientBoostingRegressor(max_iter=150, random_state=42, early_stopping=False)
        model.fit(x[cols], y)
        pred[name] = np.maximum(0, model.predict(tx.loc[idx, cols]))
    pred["adaptive_mean"] = age_blend(age, ref, pred["relative_hgb"])
    return test.loc[idx, "unit"].to_numpy(), age, pred


def paired_delta(actual, candidate, baseline):
    delta = np.abs(candidate-actual)-np.abs(baseline-actual)
    rng = np.random.default_rng(42)
    boot = delta[rng.integers(0, len(delta), size=(5000, len(delta)))].mean(axis=1)
    return {"mae_delta": float(delta.mean()), "percentile_95_interval": np.quantile(boot,[.025,.975]).tolist(),
            "win_fraction": float((delta<0).mean())}


def run(data_dir):
    root = Path(data_dir)
    for name in ("train_FD001.txt","test_FD001.txt"):
        verify(root/name,HASHES[name])
    train = load_trajectories(root/"train_FD001.txt")
    test = load_trajectories(root/"test_FD001.txt")
    if train.unit.nunique()!=100 or test.unit.nunique()!=100:
        raise ValueError("Unexpected engine population")
    units, ages, pred = predict_endpoints(train,test)
    # All candidate predictions are complete before official targets are read.
    verify(root/"RUL_FD001.txt",HASHES["RUL_FD001.txt"])
    actual = endpoint_targets(test,root/"RUL_FD001.txt").reindex(units).to_numpy()
    return {"protocol":"FD001 official endpoint frozen v1","dataset_sha256":HASHES,
            "primary":"relative_hgb","engines":len(units),
            "metrics":{k:risk_metrics(actual,v) for k,v in pred.items()},
            "paired_primary_vs_age":paired_delta(actual,pred["relative_hgb"],pred["age_reference"]),
            "predictions":[{"unit":int(u),"cycle":int(a),"actual":float(y),
                            **{k:float(v[i]) for k,v in pred.items()}}
                           for i,(u,a,y) in enumerate(zip(units,ages,actual))],
            "scope":"Official simulated FD001 endpoints; fixed candidates; no field or safety claims."}


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().data_dir),indent=2,allow_nan=False))
