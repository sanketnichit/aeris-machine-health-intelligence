"""Train outside a held-out regime; evaluate only inside it.

Run: python -m research.operating_regime_audit
The regimes are defined using observed features, never target labels.
This is an AI4I retrospective shift stress test, not external validation.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sklearn.metrics import average_precision_score, brier_score_loss, recall_score, precision_score

from src.features import MODEL_FEATURES, add_engineered_features
from src.load_data import RAW_PATH, load_raw
from src.models import build_calibrated_hgb


def regimes(frame):
    # Fixed physical bands, not outcome-optimized.
    return {
        "low_speed": frame["rot_speed_rpm"] < 1380,
        "high_torque": frame["torque_nm"] >= 50,
        "high_wear": frame["tool_wear_min"] >= 200,
        "low_temperature_delta": frame["temp_delta_k"] < 8.6,
        **{f"type_{kind}": frame["type"] == kind for kind in ("L", "M", "H")},
    }


def run(path=RAW_PATH):
    frame = add_engineered_features(load_raw(path))
    results = []
    for name, mask in regimes(frame).items():
        train, test = frame.loc[~mask], frame.loc[mask]
        y_train, y = train["machine_failure"], test["machine_failure"]
        counts = y_train.value_counts()
        result = dict(regime=name, train_rows=len(train), test_rows=len(test),
                      train_failures=int(y_train.sum()), test_failures=int(y.sum()))
        if len(counts) != 2 or counts.min() < 5 or y.nunique() != 2:
            result.update(status="insufficient_class_support")
        else:
            model = build_calibrated_hgb(cv=5, n_jobs=1)
            model.fit(train[MODEL_FEATURES], y_train)
            p = model.predict_proba(test[MODEL_FEATURES])[:, 1]
            result.update(status="evaluated", prevalence=float(y.mean()),
                          ap=float(average_precision_score(y,p)),
                          brier=float(brier_score_loss(y,p)),
                          recall=float(recall_score(y,p>=.5,zero_division=0)),
                          precision=float(precision_score(y,p>=.5,zero_division=0)))
        results.append(result)
    return dict(dataset_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                regimes=results, scope="Retrospective, overlapping regime stress tests; no tuning or external transfer claim.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=RAW_PATH)
    print(json.dumps(run(parser.parse_args().data), indent=2))
