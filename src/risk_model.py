"""
AERIS - calibrated machine-failure risk model.

The risk score is a calibrated estimate from 0 to 1, not a physical-health
measurement. It is evaluated on a final held-out test set.
"""
from pathlib import Path

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from features import MODEL_FEATURES, add_engineered_features
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

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["type"],
            ),
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )

    base_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                HistGradientBoostingClassifier(
                    max_iter=300,
                    learning_rate=0.06,
                    max_leaf_nodes=31,
                    l2_regularization=1.0,
                    random_state=42,
                ),
            ),
        ]
    )

    calibrated = CalibratedClassifierCV(
        base_model,
        method="sigmoid",
        cv=5,
        n_jobs=-1,
    )

    calibrated.fit(X_train, y_train)

    risk = calibrated.predict_proba(X_test)[:, 1]
    predicted_failure = (risk >= 0.50).astype(int)

    precision = precision_score(
        y_test, predicted_failure, zero_division=0
    )
    recall = recall_score(y_test, predicted_failure, zero_division=0)
    f1 = f1_score(y_test, predicted_failure, zero_division=0)
    pr_auc = average_precision_score(y_test, risk)
    brier = brier_score_loss(y_test, risk)

    lines = [
        "# AERIS Risk Model\n\n",
        "## Model\n",
        "HistGradientBoostingClassifier with deterministic engineering-derived " 
        "features and sigmoid probability calibration "
        "using 5-fold cross-validation on the training set.\n\n",
        "## Held-out test results\n",
        f"- Precision @ 0.50: **{precision:.3f}**\n",
        f"- Recall @ 0.50: **{recall:.3f}**\n",
        f"- F1 @ 0.50: **{f1:.3f}**\n",
        f"- PR-AUC: **{pr_auc:.3f}**\n",
        f"- Brier score: **{brier:.4f}** (lower is better)\n\n",
        "## How to interpret the AERIS risk score\n",
        "The score is a calibrated model probability estimate for the positive "
        "failure label under this benchmark. It is not a physical measurement "
        "of machine health and should not be presented as a guaranteed failure "
        "probability in a production setting.\n\n",
        "## Why calibration\n",
        "A risk score is more useful than a raw class label when the application "
        "needs a graded level of concern. Calibration is therefore evaluated "
        "separately from ranking metrics such as PR-AUC.\n",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
