"""Development-only landmark evaluation; no official test data accessed.

Each landmark is an observable operating age, not a fraction of future life.
One observation per surviving engine per landmark; no pooling for coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold

from research.cmapss_baseline import scores
from research.cmapss_stage_audit import age_conditioned, relative_features
from src.prognostics import load_trajectories, training_targets
from src.rul_uncertainty import conformal_radius, intervals, interval_metrics

LANDMARKS = (50, 100, 150, 200)


def landmark_indices(frame, units, age):
    return frame.index[frame.unit.isin(units) & frame.cycle.eq(age)].to_numpy()


def evaluate(frame, landmarks=LANDMARKS, alpha=.1):
    units = np.sort(frame.unit.unique())
    if len(units) < 45:
        raise ValueError("At least 45 engines required")
    x = relative_features(frame)
    y = training_targets(frame)
    reports = {str(age): [] for age in landmarks}
    # Outer evaluation engines never enter model fitting or interval calibration.
    for fold, (dev, test) in enumerate(KFold(5, shuffle=True, random_state=42).split(units)):
        shuffled = np.random.default_rng(100+fold).permutation(units[dev])
        boundary = int(.75 * len(shuffled))
        fit_units, cal_units, test_units = shuffled[:boundary], shuffled[boundary:], units[test]
        fit = frame.unit.isin(fit_units)
        lifetimes = frame.loc[fit].groupby("unit").cycle.max().to_numpy()
        model = HistGradientBoostingRegressor(max_iter=150, random_state=42,
                                              early_stopping=False)
        model.fit(x.loc[fit], y.loc[fit])
        for age in landmarks:
            cal = landmark_indices(frame, cal_units, age)
            ev = landmark_indices(frame, test_units, age)
            row = {"fold": fold, "fit_units": sorted(map(int, fit_units)),
                   "calibration_units": sorted(map(int, cal_units)),
                   "evaluation_units": sorted(map(int, test_units)),
                   "calibration_survivors": len(cal), "evaluation_survivors": len(ev)}
            if not len(ev):
                row["status"] = "no_evaluation_survivors"
                reports[str(age)].append(row)
                continue
            actual = y.loc[ev].to_numpy()
            predicted = np.maximum(0, model.predict(x.loc[ev]))
            baseline = age_conditioned(lifetimes, frame.loc[ev, "cycle"])
            row.update(status="evaluated", learned=scores(actual, predicted),
                       baseline=scores(actual, baseline))
            # A finite conformal radius requires ceil((n+1)*(1-alpha)) <= n.
            if len(cal) and np.ceil((len(cal)+1)*(1-alpha)) <= len(cal):
                cal_pred = np.maximum(0, model.predict(x.loc[cal]))
                radius = conformal_radius(y.loc[cal], cal_pred, alpha)
                lo, hi = intervals(predicted, radius)
                row.update(radius_cycles=radius, interval=interval_metrics(actual, lo, hi))
            else:
                row["interval_status"] = "insufficient_calibration_survivors"
            row["predictions"] = [
                {"unit": int(u), "actual": float(a), "predicted": float(p), "baseline": float(b)}
                for u,a,p,b in zip(frame.loc[ev,"unit"], actual, predicted, baseline)]
            reports[str(age)].append(row)
    summary = {}
    for age, folds in reports.items():
        points = [p for f in folds for p in f.get("predictions", [])]
        calibrated = [f["interval"] for f in folds if "interval" in f]
        count = sum(m["endpoints"] for m in calibrated)
        summary[age] = {"evaluated_engines": len(points), "interval_evaluated_engines": count}
        if points:
            truth = [p["actual"] for p in points]
            summary[age].update(learned=scores(truth, [p["predicted"] for p in points]),
                                baseline=scores(truth, [p["baseline"] for p in points]))
        if count:
            summary[age]["interval_coverage"] = sum(m["coverage"]*m["endpoints"] for m in calibrated)/count
            summary[age]["mean_interval_width"] = sum(m["mean_width"]*m["endpoints"] for m in calibrated)/count
    return {"alpha": alpha, "summary": summary, "folds": reports,
            "scope": "Development-only simulated survivors at fixed observable ages; fold-specific split conformal assumptions, no pooled coverage guarantee or safety claim."}


def run(data_dir):
    path = Path(data_dir) / "train_FD001.txt"
    return {"train_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            **evaluate(load_trajectories(path))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().data_dir), indent=2, allow_nan=False))
