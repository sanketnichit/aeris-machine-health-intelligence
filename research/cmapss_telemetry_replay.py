"""Development-only replay traces; fixed demo engines chosen by ID, not accuracy."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

from research.cmapss_stage_audit import age_conditioned, relative_features
from research.cmapss_risk_audit import age_blend
from src.prognostics import load_trajectories, training_targets

DEMO_UNITS = (1, 2, 3)
SENSOR_COLUMNS = ("sensor_2", "sensor_3", "sensor_4", "sensor_11")


def export_traces(frame, units=DEMO_UNITS):
    units = set(units)
    if not units or not units.issubset(set(frame.unit)):
        raise ValueError("Unknown or empty demo engine selection")
    x, y = relative_features(frame), training_targets(frame)
    traces = []
    for fold, (fit, ev) in enumerate(GroupKFold(5).split(x, y, frame.unit)):
        holdout = frame.iloc[ev]
        selected = holdout.loc[holdout.unit.isin(units)]
        if selected.empty:
            continue
        life = frame.iloc[fit].groupby("unit").cycle.max().to_numpy()
        model = HistGradientBoostingRegressor(max_iter=150, random_state=42, early_stopping=False)
        model.fit(x.iloc[fit], y.iloc[fit])
        for unit, group in selected.groupby("unit", sort=True):
            # The failure observation is excluded from the replay.
            g = group.iloc[:-1]
            if g.empty:
                raise ValueError("Replay requires pre-failure observations")
            age = g.cycle.to_numpy()
            learned = np.maximum(0, model.predict(x.loc[g.index]))
            ref = age_conditioned(life, age)
            adaptive = age_blend(age, ref, learned)
            traces.append({"unit": int(unit), "fold": fold,
                           "fit_units": sorted(map(int, frame.iloc[fit].unit.unique())),
                           "points": [{"cycle": int(c), "age_reference": float(ref[i]),
                                       "relative_hgb": float(learned[i]), "adaptive_mean": float(adaptive[i]),
                                       **{s: float(g.iloc[i][s]) for s in SENSOR_COLUMNS}}
                                      for i, c in enumerate(age)],
                           "failure_cycle": int(group.cycle.max())})
    return sorted(traces, key=lambda t: t["unit"])


def run(data_dir):
    path = Path(data_dir) / "train_FD001.txt"
    return {"schema_version": 1, "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "traces": export_traces(load_trajectories(path)),
            "scope": "Retrospective simulated training-engine replay, out-of-fold predictions; selected IDs 1–3, no official test targets. Failure cycle is retrospective truth, not an input. Not an operational control system."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().data_dir), indent=2, allow_nan=False))
