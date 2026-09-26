"""
AERIS - Machine Health Intelligence
First working baseline: Random Forest binary failure detector.

The failure-mode flags are excluded from the feature set because they are
downstream labels, not legitimate prediction-time inputs.
"""
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from features import BASE_FEATURES
from load_data import load_raw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "baseline_metrics.md"


def main() -> None:
    df = load_raw()

    feature_cols = BASE_FEATURES

    X = df[feature_cols].copy()
    y = df["machine_failure"].copy()

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
                OneHotEncoder(handle_unknown="ignore"),
                ["type"],
            ),
            (
                "numeric",
                "passthrough",
                BASE_FEATURES[1:],
            ),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=400,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    pipeline.fit(X_train, y_train)

    probabilities = pipeline.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    pr_auc = average_precision_score(y_test, probabilities)
    roc_auc = roc_auc_score(y_test, probabilities)

    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()

    feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_

    importance_df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(10)
    )

    lines = [
        "# AERIS Baseline - Random Forest Failure Detector\n\n",
        "## Split\n",
        "- Stratified train/test split: 80/20\n",
        "- Random seed: 42\n",
        "- Features: machine type + five process variables\n",
        "- Excluded: UDI, Product ID, and failure-mode flags to avoid leakage\n\n",
        "## Test metrics\n",
        f"- Precision: **{precision:.3f}**\n",
        f"- Recall: **{recall:.3f}**\n",
        f"- F1: **{f1:.3f}**\n",
        f"- PR-AUC (average precision): **{pr_auc:.3f}**\n",
        f"- ROC-AUC (secondary): {roc_auc:.3f}\n\n",
        "## Confusion matrix\n",
        "Rows = actual, columns = predicted.\n\n",
        "Predicted 0 | Predicted 1\n",
        f"Actual 0      {tn:4d} | {fp:4d}\n",
        f"Actual 1      {fn:4d} | {tp:4d}\n\n",
        "## Top feature importances\n",
    ]

    for _, row in importance_df.iterrows():
        lines.append(f"- {row['feature']}: {row['importance']:.4f}\n")

    lines.append(
        "\n## Interpretation\n"
        "This is the first ugly-but-working baseline. It establishes a complete "
        "prediction path before model comparison, SHAP, or calibration. Metrics "
        "are evaluated with precision, recall, F1 and PR-AUC because failures "
        "are a small minority class.\n"
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
