"""
AERIS - threshold and calibration evaluation.

Thresholds are selected from out-of-fold training predictions only, then
evaluated on the untouched test partition. Calibration is evaluated separately.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .models import build_calibrated_hgb, build_hgb_pipeline
    from .load_data import load_raw
except ImportError:  # direct script execution from extended-validation/src/
    from features import MODEL_FEATURES, add_engineered_features
    from models import build_calibrated_hgb, build_hgb_pipeline
    from load_data import load_raw


ROOT = PROJECT_ROOT
FIGURES = ROOT / "figures"
REPORT = ROOT / "extended-validation" / "reports" / "threshold_analysis.md"
FEATURES = MODEL_FEATURES


build_base_model = build_hgb_pipeline

def main() -> None:
    df = add_engineered_features(load_raw())
    X = df[FEATURES]
    y = df["machine_failure"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    base = build_base_model()

    oof_prob = cross_val_predict(
        base,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=1,
    )[:, 1]

    precision, recall, thresholds = precision_recall_curve(y_train, oof_prob)
    candidates = []
    for beta in (0.5, 1.0, 2.0):
        f_beta = (
            (1 + beta**2) * precision * recall
            / (beta**2 * precision + recall + 1e-12)
        )
        idx = int(np.nanargmax(f_beta[:-1]))
        candidates.append((f"F{beta:g}", float(thresholds[idx])))

    fitted = build_base_model().fit(X_train, y_train)
    test_prob = fitted.predict_proba(X_test)[:, 1]

    rows = []
    for objective, threshold in candidates:
        pred = (test_prob >= threshold).astype(int)
        rows.append(
            (
                objective,
                threshold,
                precision_score(y_test, pred, zero_division=0),
                recall_score(y_test, pred, zero_division=0),
                f1_score(y_test, pred, zero_division=0),
            )
        )

    calibrated = build_calibrated_hgb(cv=5, n_jobs=1)
    calibrated.fit(X_train, y_train)
    calibrated_prob = calibrated.predict_proba(X_test)[:, 1]

    brier = brier_score_loss(y_test, calibrated_prob)
    ap = average_precision_score(y_test, calibrated_prob)
    pred50 = (calibrated_prob >= 0.50).astype(int)

    FIGURES.mkdir(parents=True, exist_ok=True)

    frac, mean = calibration_curve(
        y_test,
        calibrated_prob,
        n_bins=10,
        strategy="quantile",
    )

    plt.figure(figsize=(5, 5))
    plt.plot(mean, frac, "o-", label="AERIS")
    plt.plot([0, 1], [0, 1], "--", label="Perfect calibration")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Observed failure frequency")
    plt.title("AERIS risk-score calibration")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(FIGURES / "calibration_curve.png", dpi=180)
    plt.close()

    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("AERIS Precision-Recall Curve (OOF)")
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(FIGURES / "precision_recall_curve.png", dpi=180)
    plt.close()

    lines = [
        "# Threshold and Calibration Analysis\n\n",
        "Thresholds are selected using out-of-fold predictions from the training "
        "partition only, then evaluated once on the untouched test partition.\n\n",
        "| Objective | OOF threshold | Test precision | Test recall | Test F1 |\n",
        "|---|---:|---:|---:|---:|\n",
    ]

    for objective, threshold, p, r, f1 in rows:
        lines.append(
            f"| {objective} | {threshold:.3f} | {p:.3f} | {r:.3f} | {f1:.3f} |\n"
        )

    lines.extend(
        [
            "\n## Calibrated risk model\n",
            f"- PR-AUC: **{ap:.3f}**\n",
            f"- Precision @ 0.50: **{precision_score(y_test, pred50, zero_division=0):.3f}**\n",
            f"- Recall @ 0.50: **{recall_score(y_test, pred50, zero_division=0):.3f}**\n",
            f"- F1 @ 0.50: **{f1_score(y_test, pred50, zero_division=0):.3f}**\n",
            f"- Brier score: **{brier:.4f}**\n\n",
            "The visualization keeps 0.50 as the default calibrated risk threshold. "
            "Different operational costs would justify a different threshold.\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
