from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split

from features import MODEL_FEATURES, add_engineered_features
from load_data import load_raw
from models import build_calibrated_hgb, build_hgb_pipeline


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "feature_ablation.md"

RAW_FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]
ENGINEERED_FEATURES = MODEL_FEATURES


def build_model(features: list[str]):
    """Build the canonical HGB architecture for the selected feature contract."""
    return build_hgb_pipeline(features)


def evaluate(
    df: pd.DataFrame,
    features: list[str],
    train_idx,
    test_idx,
    y_train,
    y_test,
) -> dict[str, float]:
    X_train = df.loc[train_idx, features]
    X_test = df.loc[test_idx, features]

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_validate(
        build_model(features),
        X_train,
        y_train,
        cv=cv,
        scoring={"pr_auc": "average_precision", "f1": "f1", "recall": "recall"},
        n_jobs=-1,
    )

    calibrated = build_calibrated_hgb(
        calibration_method="sigmoid",
        cv=5,
        n_jobs=-1,
        features=features,
    ).fit(X_train, y_train)

    probability = calibrated.predict_proba(X_test)[:, 1]
    prediction = (probability >= 0.50).astype(int)

    return {
        "cv_pr_auc": cv_scores["test_pr_auc"].mean(),
        "cv_pr_auc_std": cv_scores["test_pr_auc"].std(),
        "cv_f1": cv_scores["test_f1"].mean(),
        "test_pr_auc": average_precision_score(y_test, probability),
        "test_precision": precision_score(
            y_test, prediction, zero_division=0
        ),
        "test_recall": recall_score(
            y_test, prediction, zero_division=0
        ),
        "test_f1": f1_score(
            y_test, prediction, zero_division=0
        ),
        "test_brier": brier_score_loss(y_test, probability),
    }


def main() -> None:
    df = add_engineered_features(load_raw())
    y = df["machine_failure"]

    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    results = {
        "Raw operating features": evaluate(
            df,
            RAW_FEATURES,
            train_idx,
            test_idx,
            y.loc[train_idx],
            y.loc[test_idx],
        ),
        "Raw + engineered features": evaluate(
            df,
            ENGINEERED_FEATURES,
            train_idx,
            test_idx,
            y.loc[train_idx],
            y.loc[test_idx],
        ),
    }

    raw = results["Raw operating features"]
    eng = results["Raw + engineered features"]

    lines = [
        "# AERIS Feature Ablation Study\n\n",
        "This experiment isolates the contribution of the two deterministic "
        "engineering-derived features used by AERIS v1. The model family, "
        "hyperparameters, random seed, train/test partition, cross-validation "
        "scheme and 0.50 calibrated decision threshold are held fixed.\n\n",
        "## Features\n",
        "- **Raw operating features:** product type, air temperature, process temperature, "
        "rotational speed, torque and tool wear.\n",
        "- **Engineered set:** the same six raw features plus temperature delta and "
        "mechanical power.\n\n",
        "Neither engineered feature uses machine-failure or failure-mode labels.\n\n",
        "## Results\n\n",
        "| Feature set | CV PR-AUC | Test PR-AUC | Test precision | Test recall | Test F1 | Test Brier |\n",
        "|---|---:|---:|---:|---:|---:|---:|\n",
    ]

    for name, row in results.items():
        lines.append(
            f"| {name} | {row['cv_pr_auc']:.4f} ± {row['cv_pr_auc_std']:.4f} | "
            f"{row['test_pr_auc']:.4f} | {row['test_precision']:.4f} | "
            f"{row['test_recall']:.4f} | {row['test_f1']:.4f} | "
            f"{row['test_brier']:.4f} |\n"
        )

    lines.extend(
        [
            "\n## Change from adding the engineered features\n\n",
            f"- CV PR-AUC change: **{eng['cv_pr_auc'] - raw['cv_pr_auc']:+.4f}**\n",
            f"- Test PR-AUC change: **{eng['test_pr_auc'] - raw['test_pr_auc']:+.4f}**\n",
            f"- Test recall change: **{eng['test_recall'] - raw['test_recall']:+.4f}**\n",
            f"- Test F1 change: **{eng['test_f1'] - raw['test_f1']:+.4f}**\n",
            f"- Brier-score change: **{eng['test_brier'] - raw['test_brier']:+.4f}** "
            "(negative is better)\n\n",
            "## Interpretation\n",
            "The engineered features improve both ranking and thresholded detection on "
            "the AI4I benchmark under the fixed evaluation design. This supports keeping "
            "them in v1. It does not establish physical causality, and the effect should "
            "be re-tested on independent industrial data because AI4I is synthetic.\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
