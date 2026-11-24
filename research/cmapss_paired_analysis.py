"""Descriptive paired engine bootstrap of fixed out-of-fold predictions.

Run python -m research.cmapss_paired_analysis evidence/stage_audit.json.
Does not refit models or access official test labels. Intervals are conditional
on the fitted cross-validation predictions, not full training uncertainty.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def paired_analysis(records, reference="age_conditioned", draws=5000, seed=42):
    frame = pd.DataFrame(records)
    required = {"unit", "stage", "fold", "model", "actual", "predicted"}
    if not required.issubset(frame) or frame.empty:
        raise ValueError("Missing prediction records")
    if frame[list(required)].isna().any().any() or not np.isfinite(frame[["actual", "predicted"]].to_numpy(dtype=float)).all():
        raise ValueError("Invalid prediction records")
    if (frame[["actual", "predicted"]] < 0).any().any():
        raise ValueError("Negative RUL")
    if frame.duplicated(["unit", "stage", "model"]).any():
        raise ValueError("Duplicate predictions")
    if not frame.groupby("unit").fold.nunique().eq(1).all():
        raise ValueError("An engine appears in multiple evaluation folds")
    if not frame.groupby(["unit", "stage"]).actual.nunique().eq(1).all():
        raise ValueError("Mismatched ground truth")
    if not isinstance(draws, int) or draws < 100:
        raise ValueError("At least 100 bootstrap draws required")
    frame["abs_error"] = (frame.predicted-frame.actual).abs()
    paired = frame.pivot(index=["unit","stage"], columns="model", values="abs_error")
    if reference not in paired or paired.isna().any().any():
        raise ValueError("Incomplete model pairing")
    engine = paired.groupby(level="unit").mean()
    if len(engine) < 2:
        raise ValueError("At least two engines required")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(engine), size=(draws, len(engine)))
    comparisons = {}
    for model in engine:
        if model == reference:
            continue
        delta = (engine[model]-engine[reference]).to_numpy()
        boot = delta[indices].mean(axis=1)
        comparisons[model] = {
            "engine_weighted_mae_delta": float(delta.mean()),
            "percentile_95_interval": np.quantile(boot, [.025,.975]).tolist(),
            "engine_win_fraction": float((delta < 0).mean()),
            "engine_tie_fraction": float((delta == 0).mean()),
            "by_stage_mae_delta": {str(stage): float(g[model].mean()-g[reference].mean())
                                   for stage,g in paired.groupby(level="stage")},
        }
    return {"reference": reference, "engines": len(engine), "draws": draws, "seed": seed,
            "comparisons": comparisons,
            "scope": "Exploratory paired bootstrap of fixed out-of-fold predictions; engines resampled as clusters; no multiplicity correction or full refit uncertainty. Negative delta favors candidate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    data = json.loads(args.report.read_text())
    print(json.dumps(paired_analysis(data["predictions"]), indent=2, allow_nan=False))
