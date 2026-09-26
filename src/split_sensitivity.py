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

from load_data import load_raw


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "split_sensitivity.md"

FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]
SEEDS = [42, 7, 21, 84, 123]
THRESHOLD = 0.50


def build_model() -> CalibratedClassifierCV:
    pre = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["type"],
            ),
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )
    base = Pipeline(
        [
            ("preprocessor", pre),
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
    return CalibratedClassifierCV(base, method="sigmoid", cv=5, n_jobs=-1)


def main() -> None:
    df = load_raw()
    X = df[FEATURES]
    y = df["machine_failure"]

    rows = []
    for seed in SEEDS:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            stratify=y,
            random_state=seed,
        )

        model = build_model()
        model.fit(X_train, y_train)
        prob = model.predict_proba(X_test)[:, 1]
        pred = (prob >= THRESHOLD).astype(int)

        rows.append(
            {
                "seed": seed,
                "pr_auc": average_precision_score(y_test, prob),
                "precision": precision_score(y_test, pred, zero_division=0),
                "recall": recall_score(y_test, pred, zero_division=0),
                "f1": f1_score(y_test, pred, zero_division=0),
                "brier": brier_score_loss(y_test, prob),
                "test_failures": int(y_test.sum()),
            }
        )

    result = pd.DataFrame(rows)
    metrics = ["pr_auc", "precision", "recall", "f1", "brier"]

    lines = [
        "# AERIS Split-Sensitivity Audit\n\n",
        "This audit evaluates the **fixed v1 calibrated HGB model** across five "
        "independent stratified 80/20 train/test splits. The model hyperparameters "
        "and 0.50 threshold are held fixed; the alternate splits are not used to "
        "tune the model or replace the primary held-out evaluation.\n\n",
        "## Results by split\n\n",
        "| Seed | Test failures | PR-AUC | Precision | Recall | F1 | Brier |\n",
        "|---:|---:|---:|---:|---:|---:|---:|\n",
    ]

    for _, row in result.iterrows():
        lines.append(
            f"| {int(row['seed'])} | {int(row['test_failures'])} | "
            f"{row['pr_auc']:.3f} | {row['precision']:.3f} | "
            f"{row['recall']:.3f} | {row['f1']:.3f} | {row['brier']:.4f} |\n"
        )

    lines.extend(
        [
            "\n## Fixed-model summary\n\n",
            "| Metric | Mean | Std | Min | Max |\n",
            "|---|---:|---:|---:|---:|\n",
        ]
    )

    for metric in metrics:
        values = result[metric]
        label = "PR-AUC" if metric == "pr_auc" else (
            "Precision" if metric == "precision" else (
                "Recall" if metric == "recall" else (
                    "F1" if metric == "f1" else "Brier"
                )
            )
        )
        lines.append(
            f"| {label} | {values.mean():.4f} | {values.std(ddof=1):.4f} | "
            f"{values.min():.4f} | {values.max():.4f} |\n"
        )

    lines.extend(
        [
            "\n## Interpretation\n",
            "The ranking and classification metrics move across splits, which is "
            "expected with a relatively small positive class. The point of this "
            "audit is not to manufacture a single more impressive score; it is to "
            "show that performance is sensitive to which observations land in the "
            "test partition. The seed-42 split remains the project's primary held-out "
            "evaluation for consistency with the model-selection record.\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
