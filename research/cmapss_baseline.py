"""Run: python -m research.cmapss_baseline --data-dir /path/to/C-MAPSS."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit

from src.prognostics import (load_trajectories, training_targets, causal_features,
                             endpoint_indices, endpoint_targets)


def scores(actual, predicted):
    error = np.asarray(predicted, dtype=float) - np.asarray(actual, dtype=float)
    return dict(mae=float(np.abs(error).mean()), rmse=float(np.sqrt(np.mean(error**2))),
                nasa_score=float(np.expm1(np.where(error < 0, -error / 13, error / 10)).sum()))


def run(data_dir, subset="FD001", official=False):
    root = Path(data_dir)
    train_path = root / f"train_{subset}.txt"
    train = load_trajectories(train_path)
    x = causal_features(train)
    y = training_targets(train)
    fit, val = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42)
                    .split(x, y, groups=train.unit))
    # Evaluate one deterministic truncated prefix per validation unit, not failure endpoints.
    rng = np.random.default_rng(42)
    endpoints = []
    for _, group in train.iloc[val].groupby("unit", sort=True):
        lo = max(1, len(group)//3)
        hi = max(lo, 2*len(group)//3)
        endpoints.append(group.index[int(rng.integers(lo, hi+1))-1])
    factories = {
        "ridge_snapshot": lambda: make_pipeline(StandardScaler(), Ridge(alpha=10)),
        "hgb_snapshot": lambda: HistGradientBoostingRegressor(max_iter=150, random_state=42),
        "hgb_causal": lambda: HistGradientBoostingRegressor(max_iter=150, random_state=42),
    }
    snapshot_cols = [c for c in x.columns if not c.endswith(("_mean", "_delta"))]
    features = {name: (list(x.columns) if name.endswith("causal") else snapshot_cols)
                for name in factories}
    median = float(np.median(y.iloc[fit]))
    results = {"constant": scores(y.loc[endpoints], np.full(len(endpoints), median))}
    for name, factory in factories.items():
        cols = features[name]
        model = factory().fit(x.iloc[fit][cols], y.iloc[fit])
        results[name] = scores(y.loc[endpoints], np.maximum(0, model.predict(x.loc[endpoints, cols])))
    selected = min(results, key=lambda name: (results[name]["rmse"], name))
    report = dict(subset=subset, seed=42, train_sha256=hashlib.sha256(train_path.read_bytes()).hexdigest(),
                  fit_units=sorted(map(int, train.iloc[fit].unit.unique())),
                  validation_units=sorted(map(int, train.iloc[val].unit.unique())),
                  validation_endpoints=[int(train.loc[i,"cycle"]) for i in endpoints],
                  validation=results, selected=selected,
                  scope="Simulated RUL cycles; no physical fleet validation.")
    if official:
        test_path = root / f"test_{subset}.txt"
        label_path = root / f"RUL_{subset}.txt"
        test = load_trajectories(test_path)
        test_x = causal_features(test)
        idx = endpoint_indices(test)
        actual = endpoint_targets(test, label_path).to_numpy()
        if selected == "constant":
            pred = np.full(len(idx), float(np.median(y)))
        else:
            cols = features[selected]
            model = factories[selected]().fit(x[cols], y)
            pred = np.maximum(0, model.predict(test_x.loc[idx, cols]))
        report.update(official_test=scores(actual, pred),
                      test_sha256=hashlib.sha256(test_path.read_bytes()).hexdigest(),
                      labels_sha256=hashlib.sha256(label_path.read_bytes()).hexdigest())
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--subset", choices=["FD001","FD002","FD003","FD004"], default="FD001")
    parser.add_argument("--official", action="store_true", help="Final evaluation only after protocol freeze")
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.subset, args.official), indent=2))
