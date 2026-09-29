"""
AERIS - calibrated machine-failure risk model.

The risk score is a calibrated model output from 0 to 1. The final numbers are
measured on a held-out test set.
"""
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    precision_recall_curve,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .models import build_calibrated_hgb, build_hgb_pipeline
    from .load_data import load_raw
except ImportError:  # direct script execution from src/
    from features import MODEL_FEATURES, add_engineered_features
    from models import build_calibrated_hgb, build_hgb_pipeline
    from load_data import load_raw


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "risk_model.md"

FEATURES = MODEL_FEATURES


def main() -> None:
    df = add_engineered_features(load_raw())
    X = df[FEATURES]
    y = df["machine_failure"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    calibrated = build_calibrated_hgb(cv=5, n_jobs=-1)
    calibrated.fit(X_train, y_train)

    risk = calibrated.predict_proba(X_test)[:, 1]
    predicted_failure = (risk >= 0.50).astype(int)

    precision = precision_score(y_test, predicted_failure, zero_division=0)
    recall = recall_score(y_test, predicted_failure, zero_division=0)
    f1 = f1_score(y_test, predicted_failure, zero_division=0)
    pr_auc = average_precision_score(y_test, risk)
    brier = brier_score_loss(y_test, risk)

    sigmoid = build_calibrated_hgb(
        calibration_method="sigmoid",
        cv=5,
        n_jobs=-1,
    ).fit(X_train, y_train)
    isotonic = build_calibrated_hgb(
        calibration_method="isotonic",
        cv=5,
        n_jobs=-1,
    ).fit(X_train, y_train)

    sigmoid_brier = brier_score_loss(
        y_test,
        sigmoid.predict_proba(X_test)[:, 1],
    )
    isotonic_brier = brier_score_loss(
        y_test,
        isotonic.predict_proba(X_test)[:, 1],
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    base = build_hgb_pipeline()
    oof_prob = cross_val_predict(
        base,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=1,
    )[:, 1]

    pr, rc, thresholds = precision_recall_curve(y_train, oof_prob)
    candidates = []
    for beta in (0.5, 1.0, 2.0):
        f_beta = (
            (1 + beta**2) * pr * rc
            / (beta**2 * pr + rc + 1e-12)
        )
        index = int(np.nanargmax(f_beta[:-1]))
        candidates.append((f"F{beta:g}", float(thresholds[index])))

    base_test = build_hgb_pipeline().fit(X_train, y_train)
    raw_test_prob = base_test.predict_proba(X_test)[:, 1]

    threshold_rows = []
    for objective, threshold in candidates:
        pred = (raw_test_prob >= threshold).astype(int)
        threshold_rows.append(
            (
                objective,
                threshold,
                precision_score(y_test, pred, zero_division=0),
                recall_score(y_test, pred, zero_division=0),
                f1_score(y_test, pred, zero_division=0),
            )
        )

    lines = [
        "# AERIS Risk Model\n\n",
        "## Model\n",
        "HistGradientBoostingClassifier with deterministic engineering-derived features and sigmoid "
        "probability calibration using 5-fold cross-validation on the training partition.\n\n",
        "Derived features:\n",
        "- `temp_delta_k`: process temperature minus air temperature.\n",
        "- `mechanical_power_kw`: torque × rotational speed / 9549.2966.\n\n",
        "## Held-out test results\n\n",
        f"- Precision @ 0.50: **{precision:.3f}**\n",
        f"- Recall @ 0.50: **{recall:.3f}**\n",
        f"- F1 @ 0.50: **{f1:.3f}**\n",
        f"- PR-AUC: **{pr_auc:.3f}**\n",
        f"- Brier score: **{brier:.4f}**\n\n",
        "## Calibration choice\n\n",
        "For the same held-out test set:\n\n",
        f"- Sigmoid calibration Brier score: **{sigmoid_brier:.5f}**\n",
        f"- Isotonic calibration Brier score: **{isotonic_brier:.5f}**\n\n",
        "Sigmoid was retained for v1 because the mapping is simpler and less flexible for a small positive class.\n\n",
        "## Decision threshold\n\n",
        "The threshold is separate from the model score. Different uses can need different thresholds.\n\n",
        "Using out-of-fold predictions from the training partition, the raw-model thresholds below produced the following untouched-test results:\n\n",
        "| Objective | OOF threshold | Test precision | Test recall | Test F1 |\n",
        "|---|---:|---:|---:|---:|\n",
    ]

    for objective, threshold, p, r, threshold_f1 in threshold_rows:
        lines.append(
            f"| {objective} | {threshold:.3f} | {p:.3f} | {r:.3f} | {threshold_f1:.3f} |\n"
        )

    lines.extend(
        [
            "\nAERIS keeps **0.50 on the calibrated risk score** as the default UI decision threshold "
            "because it is simple to interpret and separates the continuous risk estimate from an "
            "application-specific alert policy.\n\n",
            "## Interpretation\n\n",
            "The displayed AERIS risk is a calibrated model estimate for the positive machine-failure "
            "label under this benchmark. It is not a physical measurement of machine health and should "
            "not be represented as a guaranteed production failure probability.\n\n",
            "The improvement from the engineered features is encouraging, but AI4I is synthetic. A real "
            "deployment would require prospective validation, calibration checks on the target population, "
            "drift monitoring, and threshold selection against explicit maintenance costs.\n",
        ]
    )

    report = "".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
