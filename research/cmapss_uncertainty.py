"""Development-only uncertainty audit with independent engine populations.

Run python -m research.cmapss_uncertainty --data-dir /path/to/C-MAPSS
No official test targets are accessed.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from src.prognostics import load_trajectories, causal_features, training_targets
from src.rul_uncertainty import conformal_radius, intervals, interval_metrics
from research.cmapss_baseline import scores


def partition_units(units, seed=42):
    ids = np.unique(units)
    if len(ids) < 45:
        raise ValueError("Need at least 45 engines for independent evaluation")
    shuffled = np.random.default_rng(seed).permutation(ids)
    a = int(.6 * len(ids))
    b = int(.8 * len(ids))
    return tuple(np.sort(x) for x in (shuffled[:a], shuffled[a:b], shuffled[b:]))


def prefix_endpoints(frame, units, seed):
    rng = np.random.default_rng(seed)
    rows = []
    for _, group in frame.loc[frame.unit.isin(units)].groupby("unit", sort=True):
        lo = max(1, len(group)//3)
        hi = max(lo, 2*len(group)//3)
        rows.append(group.index[int(rng.integers(lo, hi+1))-1])
    return rows


def support_scores(training, evaluation):
    """Maximum standardized excursion outside training marginal bounds.

    This is a transparent support heuristic, not a probability of OOD.
    Constant features with departures are unsupported.
    """
    low, high = training.min(), training.max()
    scale = high - low
    excursion = np.maximum(low-evaluation, evaluation-high).clip(lower=0)
    positive = scale > 0
    normalized = excursion.loc[:, positive].div(scale[positive], axis=1)
    result = normalized.max(axis=1).fillna(0).to_numpy()
    if (~positive).any():
        result[(excursion.loc[:, ~positive] > 0).any(axis=1).to_numpy()] = np.inf
    return result


def selective_summary(actual, predicted, support, limit):
    keep = support <= limit
    return dict(retained_fraction=float(keep.mean()), retained=int(keep.sum()),
                rejected=int((~keep).sum()),
                retained_mae=float(np.abs(actual[keep]-predicted[keep]).mean()) if keep.any() else None)


def run(data_dir, subset="FD001"):
    path = Path(data_dir) / f"train_{subset}.txt"
    frame = load_trajectories(path)
    x = causal_features(frame)
    y = training_targets(frame)
    fit, calibration, evaluation = partition_units(frame.unit)
    train_mask = frame.unit.isin(fit)
    cal_idx = prefix_endpoints(frame, calibration, 17)
    eval_idx = prefix_endpoints(frame, evaluation, 23)
    model = HistGradientBoostingRegressor(max_iter=150, random_state=42)
    model.fit(x.loc[train_mask], y.loc[train_mask])
    cal_pred = np.maximum(0, model.predict(x.loc[cal_idx]))
    pred = np.maximum(0, model.predict(x.loc[eval_idx]))
    actual = y.loc[eval_idx].to_numpy()
    radius = conformal_radius(y.loc[cal_idx], cal_pred, alpha=.1)
    lo, hi = intervals(pred, radius)
    support = support_scores(x.loc[train_mask], x.loc[eval_idx])
    return {
        "subset": subset, "data_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "training_units": fit.tolist(), "calibration_units": calibration.tolist(),
        "evaluation_units": evaluation.tolist(), "alpha": .1, "radius_cycles": radius,
        "point_metrics": scores(actual, pred),
        "interval_metrics": interval_metrics(actual, lo, hi),
        "support_sensitivity": {str(limit): selective_summary(actual, pred, support, limit)
                                for limit in (0., .05, .1, .25)},
        "scope": "Development-only simulated endpoints; exchangeability required for marginal coverage; support heuristic is not a safety guarantee. No threshold selected."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--subset", choices=["FD001","FD002","FD003","FD004"], default="FD001")
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.subset), indent=2, allow_nan=False))
