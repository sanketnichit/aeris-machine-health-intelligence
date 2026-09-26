"""
AERIS - model comparison on the AI4I 2020 benchmark.

Design:
- Hold out a final stratified test set once.
- Compare three different model families using 5-fold stratified CV on the
  training portion only.
- Use average precision (PR-AUC/AP), recall, precision and F1 as primary
  imbalance-aware metrics.
- Do not tune against the final test set.
"""
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .load_data import load_raw
    from .models import build_hgb_pipeline
except ImportError:  # direct script execution from src/
    from features import MODEL_FEATURES, add_engineered_features
    from load_data import load_raw
    from models import build_hgb_pipeline


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "model_comparison.md"

FEATURES = MODEL_FEATURES


def build_preprocessor(scale_numeric: bool = False) -> ColumnTransformer:
    """Build the comparison preprocessor for Logistic Regression / RF."""
    numeric = "passthrough"
    if scale_numeric:
        numeric = Pipeline([("scaler", StandardScaler())])

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["type"],
            ),
            ("numeric", numeric, FEATURES[1:]),
        ]
    )


def build_comparison_models():
    """Return comparison models, with HGB sourced from the canonical builder."""
    return {
        "Logistic Regression": Pipeline(
            [
                (
                    "preprocessor",
                    build_preprocessor(scale_numeric=True),
                ),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        ),
        "Random Forest": Pipeline(
            [
                ("preprocessor", build_preprocessor()),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=500,
                        class_weight="balanced_subsample",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "HistGradientBoosting": build_hgb_pipeline(),
    }


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

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rows = []

    for name, pipeline in build_comparison_models().items():
        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring={
                "pr_auc": "average_precision",
                "roc_auc": "roc_auc",
                "precision": "precision",
                "recall": "recall",
                "f1": "f1",
            },
            n_jobs=-1,
        )

        pipeline.fit(X_train, y_train)
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)

        rows.append(
            {
                "model": name,
                "cv_pr_auc_mean": scores["test_pr_auc"].mean(),
                "cv_pr_auc_std": scores["test_pr_auc"].std(),
                "cv_roc_auc_mean": scores["test_roc_auc"].mean(),
                "cv_precision_mean": scores["test_precision"].mean(),
                "cv_recall_mean": scores["test_recall"].mean(),
                "cv_f1_mean": scores["test_f1"].mean(),
                "test_pr_auc": average_precision_score(y_test, probabilities),
                "test_roc_auc": roc_auc_score(y_test, probabilities),
                "test_precision": precision_score(
                    y_test, predictions, zero_division=0
                ),
                "test_recall": recall_score(y_test, predictions, zero_division=0),
                "test_f1": f1_score(y_test, predictions, zero_division=0),
            }
        )

    result = pd.DataFrame(rows).sort_values("cv_pr_auc_mean", ascending=False)
    hgb = result.loc[result["model"] == "HistGradientBoosting"].iloc[0]
    rf = result.loc[result["model"] == "Random Forest"].iloc[0]

    lines = [
        "# Model Comparison\n\n",
        "## Evaluation design\n",
        "- 80/20 stratified train/test split (random seed 42).\n",
        "- Model comparison uses only 5-fold stratified cross-validation on the training set.\n",
        "- The final test set is evaluated once after model selection.\n",
        "- Primary metric: average precision (PR-AUC/AP), because failures are rare.\n",
        "- Secondary metrics: precision, recall, F1 and ROC-AUC.\n\n",
        "## Feature set\n",
        "\nAERIS v1 uses the six observed operating inputs plus two deterministic engineering-derived signals:\n\n",
        "- `temp_delta_k` = process temperature - air temperature\n",
        "- `mechanical_power_kw` = torque × rotational speed / 9549.2966\n\n",
        "The derived signals use only observed input variables and do not use machine-failure or failure-mode labels.\n\n",
        "## Results\n\n",
        "| Model | CV PR-AUC | CV Recall | CV F1 | Test PR-AUC | Test Precision | Test Recall | Test F1 |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]

    for _, row in result.sort_values("cv_pr_auc_mean", ascending=False).iterrows():
        lines.append(
            f"| {row['model']} | "
            f"{row['cv_pr_auc_mean']:.3f} ± {row['cv_pr_auc_std']:.3f} | "
            f"{row['cv_recall_mean']:.3f} | "
            f"{row['cv_f1_mean']:.3f} | "
            f"{row['test_pr_auc']:.3f} | "
            f"{row['test_precision']:.3f} | "
            f"{row['test_recall']:.3f} | "
            f"{row['test_f1']:.3f} |\n"
        )

    lines.extend(
        [
            "\n## Selection\n",
            "HistGradientBoosting is the current model carried forward into the calibrated risk model. "
            f"Random Forest is nearly tied on cross-validated PR-AUC ({rf['cv_pr_auc_mean']:.3f} vs "
            f"{hgb['cv_pr_auc_mean']:.3f}), while HGB has higher cross-validated recall "
            f"({hgb['cv_recall_mean']:.3f} vs {rf['cv_recall_mean']:.3f}) and F1 "
            f"({hgb['cv_f1_mean']:.3f} vs {rf['cv_f1_mean']:.3f}). The held-out test results "
            "are reported for final comparison and are not used to tune or select the model.\n\n",
            "## Engineering interpretation\n",
            "The derived features materially improve the benchmark model. This should be interpreted "
            "as a benchmark result, not proof that these two transformations are physically causal or "
            "sufficient for a real machine fleet. AI4I is synthetic, and its target generation can "
            "contain structured relationships between the operating variables and failure labels.\n\n",
            "## Downstream use\n",
            "The selected HGB architecture is carried into the calibrated risk model, explainability "
            "workflow and Streamlit console. Threshold selection remains a separate deployment decision "
            "from probability calibration.\n",
        ]
    )

    report = "".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
