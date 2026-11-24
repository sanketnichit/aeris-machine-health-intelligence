"""Retrospective robustness audit on AI4I; run python -m research.sensor_stress."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, recall_score, precision_score
from sklearn.model_selection import train_test_split

from src.features import BASE_FEATURES, MODEL_FEATURES, add_engineered_features
from src.load_data import RAW_PATH, load_raw
from src.models import build_calibrated_hgb

SENSORS = BASE_FEATURES[1:]


def corrupt(frame, scales, *, level=0.0, missing=0.0, seed=42):
    """Perturb observed numeric inputs only; recompute derived features downstream."""
    if not np.isfinite(level) or level < 0 or not 0 <= missing <= 1:
        raise ValueError("Invalid corruption parameters")
    rng = np.random.default_rng(seed)
    out = frame[BASE_FEATURES].copy()
    for col in SENSORS:
        values = out[col].to_numpy(dtype=float, copy=True)
        values += rng.normal(0, level * scales[col], size=len(values))
        values[rng.random(len(values)) < missing] = np.nan
        out[col] = values
    return add_engineered_features(out)[MODEL_FEATURES]


def run(path=RAW_PATH):
    raw = load_raw(path)
    train, test = train_test_split(raw, test_size=.2, random_state=42,
                                  stratify=raw["machine_failure"])
    scales = train[SENSORS].std().to_dict()
    model = build_calibrated_hgb(cv=5, n_jobs=1)
    model.fit(add_engineered_features(train)[MODEL_FEATURES], train["machine_failure"])
    y = test["machine_failure"]
    results = []
    for level, missing in [(0,0),(.05,0),(.1,0),(.25,0),(0,.05),(0,.1),(0,.25),(.1,.1)]:
        for seed in (11, 23, 47):
            p = model.predict_proba(corrupt(test, scales, level=level, missing=missing, seed=seed))[:,1]
            results.append(dict(noise_sd_fraction=level, missing_rate=missing, seed=seed,
                                ap=float(average_precision_score(y,p)),
                                brier=float(brier_score_loss(y,p)),
                                recall=float(recall_score(y,p>=.5,zero_division=0)),
                                precision=float(precision_score(y,p>=.5,zero_division=0))))
    return dict(dataset_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                split_seed=42, test_rows=len(test), training_scales=scales, scenarios=results,
                scope="Synthetic retrospective perturbations; not calibrated sensor error or prospective field evidence.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=RAW_PATH)
    print(json.dumps(run(parser.parse_args().data), indent=2))
