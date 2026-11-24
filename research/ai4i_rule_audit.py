"""Run from repository root: python -m research.ai4i_rule_audit."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from src.features import MODEL_FEATURES, add_engineered_features
from src.load_data import RAW_PATH, load_raw
from src.models import build_calibrated_hgb
from src.physics_rules import rule_predictions


def metrics(y, pred):
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    return {"precision": float(p), "recall": float(r), "f1": float(f),
            "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist()}


def audit(path=RAW_PATH):
    frame = add_engineered_features(load_raw(path))
    train, test = train_test_split(frame, test_size=.2, random_state=42,
                                  stratify=frame["machine_failure"])
    model = build_calibrated_hgb(cv=5, n_jobs=1)
    model.fit(train[MODEL_FEATURES], train["machine_failure"])
    prob = model.predict_proba(test[MODEL_FEATURES])[:, 1]
    y = test["machine_failure"]
    flags = rule_predictions(test)
    rule = flags["rule_failure"]
    pred = prob >= .5
    return {
        "dataset_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "test_udi_sha256": hashlib.sha256(",".join(map(str, test["udi"])).encode()).hexdigest(),
        "split_seed": 42, "test_rows": len(test), "test_failures": int(y.sum()),
        "rule_reference": metrics(y, rule),
        "calibrated_ml": {**metrics(y, pred), "average_precision": float(average_precision_score(y, prob))},
        "mode_agreement": {m: metrics(test[m], flags[m]) for m in ("hdf", "pwf", "osf")},
        "positive_disagreements": {
            "ml_only": int(((y == 1) & pred & ~rule).sum()),
            "rule_only": int(((y == 1) & ~pred & rule).sum()),
            "both_missed": int(((y == 1) & ~pred & ~rule).sum()),
        },
        "scope": "Retrospective synthetic benchmark; rules are generator-informed, not industrial limits.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=RAW_PATH)
    args = parser.parse_args()
    print(json.dumps(audit(args.data), indent=2, sort_keys=True))
