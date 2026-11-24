"""Exploratory FD001 risk audit. No official test labels are accessed.

Fixed observable ages, disjoint fitting/calibration/evaluation engines.
Age blending is motivated by previously inspected development findings;
this audit is not independent confirmation of the blend.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold

from research.cmapss_baseline import scores
from research.cmapss_landmark_audit import LANDMARKS, landmark_indices
from research.cmapss_stage_audit import age_conditioned, relative_features
from src.prognostics import load_trajectories, training_targets
from src.rul_uncertainty import interval_metrics


def age_blend(age, reference, learned):
    """Fixed ramp: age-only at 50 cycles, learned at 150 cycles."""
    w = np.clip((np.asarray(age, dtype=float) - 50) / 100, 0, 1)
    return (1-w)*np.asarray(reference) + w*np.asarray(learned)


def ordered_bounds(lower, upper):
    a, b = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Invalid quantile predictions")
    return np.maximum(0, np.minimum(a,b)), np.maximum(0, np.maximum(a,b))


def cqr_radius(actual, lower, upper, alpha=.1):
    """Nonnegative finite-sample conformal correction to quantile bounds."""
    y = np.asarray(actual, dtype=float)
    lo, hi = ordered_bounds(lower, upper)
    if y.shape != lo.shape or not len(y) or not np.isfinite(y).all() or (y < 0).any() or not 0 < alpha < 1:
        raise ValueError("Invalid calibration inputs")
    rank = math.ceil((len(y)+1)*(1-alpha))
    if rank > len(y):
        raise ValueError("Insufficient calibration engines")
    residual = np.maximum(lo-y, y-hi)
    return max(0., float(np.sort(residual)[rank-1]))


def risk_metrics(actual, predicted):
    y, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if y.ndim != 1 or y.shape != p.shape or not len(y) or not np.isfinite(y).all() or not np.isfinite(p).all() or (y < 0).any() or (p < 0).any():
        raise ValueError("Invalid paired forecasts")
    error = p-y
    return {**scores(y,p), "mean_signed_error": float(error.mean()),
            "overprediction_gt20_fraction": float((error > 20).mean()),
            "underprediction_gt20_fraction": float((error < -20).mean())}


def evaluate(frame, landmarks=LANDMARKS):
    units = np.sort(frame.unit.unique())
    if len(units) < 45:
        raise ValueError("At least 45 engines required")
    x, y = relative_features(frame), training_targets(frame)
    reports = {str(age): [] for age in landmarks}
    for fold, (dev, test) in enumerate(KFold(5, shuffle=True, random_state=42).split(units)):
        order = np.random.default_rng(100+fold).permutation(units[dev])
        split = int(.75*len(order))
        fit_units, cal_units, ev_units = order[:split], order[split:], units[test]
        fit = frame.unit.isin(fit_units)
        life = frame.loc[fit].groupby("unit").cycle.max().to_numpy()
        models = {"mean": HistGradientBoostingRegressor(max_iter=150, random_state=42, early_stopping=False)}
        for q in (.1, .25, .9):
            models[str(q)] = HistGradientBoostingRegressor(loss="quantile", quantile=q,
                max_iter=150, random_state=42, early_stopping=False)
        for model in models.values():
            model.fit(x.loc[fit], y.loc[fit])
        for age in landmarks:
            cal, ev = landmark_indices(frame, cal_units, age), landmark_indices(frame, ev_units, age)
            if not len(ev):
                continue
            actual = y.loc[ev].to_numpy()
            ref = age_conditioned(life, frame.loc[ev,"cycle"])
            estimates = {k: np.maximum(0,m.predict(x.loc[ev])) for k,m in models.items()}
            candidates = {"age_reference": ref, "learned_mean": estimates["mean"],
                          "adaptive_mean": age_blend(age,ref,estimates["mean"]),
                          "learned_q25": estimates["0.25"]}
            lo, hi = ordered_bounds(estimates["0.1"], estimates["0.9"])
            row = {"fold":fold, "calibration_survivors":len(cal),
                   "predictions":[{"unit":int(u),"actual":float(a),
                                   **{k:float(v[i]) for k,v in candidates.items()}}
                                  for i,(u,a) in enumerate(zip(frame.loc[ev,"unit"],actual))],
                   "raw_quantile_interval":interval_metrics(actual,lo,hi)}
            if len(cal) >= 9:
                cl,ch = ordered_bounds(models["0.1"].predict(x.loc[cal]), models["0.9"].predict(x.loc[cal]))
                radius = cqr_radius(y.loc[cal],cl,ch)
                row["cqr_radius"] = radius
                row["conformal_interval"] = interval_metrics(actual,np.maximum(0,lo-radius),hi+radius)
            else:
                row["interval_status"] = "insufficient_calibration_survivors"
            reports[str(age)].append(row)
    summary = {}
    for age, folds in reports.items():
        points = [p for f in folds for p in f["predictions"]]
        item = {"engines":len(points)}
        if points:
            truth = [p["actual"] for p in points]
            item["forecasts"] = {k:risk_metrics(truth,[p[k] for p in points])
                for k in ("age_reference","learned_mean","adaptive_mean","learned_q25")}
        for key in ("raw_quantile_interval","conformal_interval"):
            metrics = [f[key] for f in folds if key in f]
            count = sum(m["endpoints"] for m in metrics)
            if count:
                item[key] = {"endpoints":count, **{k:sum(m[k]*m["endpoints"] for m in metrics)/count
                    for k in ("coverage","mean_width")}}
        summary[age] = item
    return {"summary":summary,"folds":reports,
            "scope":"Exploratory simulated survivors; fixed age blend based on earlier development findings; fold-specific calibration; no independent confirmation, conditional coverage or safety claim."}


def run(data_dir):
    path = Path(data_dir)/"train_FD001.txt"
    return {"train_sha256":hashlib.sha256(path.read_bytes()).hexdigest(), **evaluate(load_trajectories(path))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().data_dir),indent=2,allow_nan=False))
