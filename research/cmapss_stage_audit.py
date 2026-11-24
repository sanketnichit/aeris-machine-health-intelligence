"""Development-only unit-disjoint stage audit; never reads official test labels."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

from research.cmapss_baseline import scores
from src.prognostics import SENSORS, causal_features, load_trajectories, training_targets

STAGES = (.25, .50, .75, .90)


def age_conditioned(lifetimes, ages):
    """Empirical median residual life among training engines surviving to age."""
    life = np.asarray(lifetimes, dtype=float)
    age = np.asarray(ages, dtype=float)
    if life.ndim != 1 or age.ndim != 1 or not len(life) or not np.isfinite(life).all() or not np.isfinite(age).all() or (life < 1).any() or (age < 1).any():
        raise ValueError("Expected finite positive lifetimes and ages")
    return np.array([np.median(life[life >= a] - a) if (life >= a).any()
                     else 0.0 for a in age])


def relative_features(frame):
    """Per-unit first-observation reference, available at every prediction time."""
    x = causal_features(frame)
    # Input is canonical sorted data from load_trajectories.
    first = frame.groupby("unit")[SENSORS].transform("first")
    relative = frame[SENSORS] - first
    return pd.concat([x, relative.add_suffix("_relative")], axis=1)


def stage_rows(frame):
    """Retrospective stage sampling uses lifetime only to choose evaluation rows."""
    result = []
    for unit, group in frame.groupby("unit", sort=True):
        length = len(group)
        for stage in STAGES:
            idx = group.index[max(1, int(np.ceil(length * stage))) - 1]
            result.append((int(unit), stage, int(idx)))
    return pd.DataFrame(result, columns=["unit", "stage", "row"])


def run(data_dir, subset="FD001"):
    path = Path(data_dir) / f"train_{subset}.txt"
    frame = load_trajectories(path)
    x = relative_features(frame)
    y = training_targets(frame)
    stage = stage_rows(frame)
    candidates = {
        "age_only_hgb": ["cycle"],
        "snapshot_hgb": [c for c in x if not c.endswith(("_mean", "_delta", "_relative"))],
        "causal_hgb": [c for c in x if not c.endswith("_relative")],
        "relative_hgb": list(x.columns),
    }
    records = []
    for fold, (fit, val) in enumerate(GroupKFold(n_splits=5).split(x, y, frame.unit)):
        held = stage.loc[stage.unit.isin(frame.iloc[val].unit)].copy()
        idx = held.row.to_numpy()
        actual = y.loc[idx].to_numpy()
        lifetimes = frame.iloc[fit].groupby("unit").cycle.max().to_numpy()
        predictions = {
            "constant": np.full(len(idx), np.median(y.iloc[fit])),
            "age_conditioned": age_conditioned(lifetimes, frame.loc[idx, "cycle"]),
        }
        for name, cols in candidates.items():
            model = HistGradientBoostingRegressor(max_iter=150, random_state=42)
            model.fit(x.iloc[fit][cols], y.iloc[fit])
            predictions[name] = np.maximum(0, model.predict(x.loc[idx, cols]))
        for name, values in predictions.items():
            for unit, fraction, truth, estimate in zip(held.unit, held.stage, actual, values):
                records.append(dict(fold=fold, unit=int(unit), stage=float(fraction),
                                    model=name, actual=float(truth), predicted=float(estimate)))
    table = pd.DataFrame(records)
    summary = {}
    for name, group in table.groupby("model"):
        summary[name] = {
            "all": scores(group.actual, group.predicted),
            "by_stage": {str(f): scores(g.actual, g.predicted) for f, g in group.groupby("stage")},
        }
    return dict(subset=subset, train_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                folds=5, engines=int(frame.unit.nunique()), stages=list(STAGES),
                metrics=summary, predictions=records,
                scope="Development-only; stages use retrospective lifetime for sampling, never as model inputs. Multiple correlated endpoints per unit. No official test labels.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--subset", choices=["FD001","FD002","FD003","FD004"], default="FD001")
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir, args.subset), indent=2, allow_nan=False))
