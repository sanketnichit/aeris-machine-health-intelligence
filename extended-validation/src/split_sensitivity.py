from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .models import build_calibrated_hgb
    from .load_data import load_raw
except ImportError:  # direct script execution from extended-validation/src/
    from features import MODEL_FEATURES, add_engineered_features
    from models import build_calibrated_hgb
    from load_data import load_raw


ROOT = PROJECT_ROOT
REPORT = ROOT / "extended-validation" / "reports" / "split_sensitivity.md"

FEATURES = MODEL_FEATURES
SEEDS = [42, 7, 21, 84, 123]
THRESHOLD = 0.50


build_model = build_calibrated_hgb

def main() -> None:
    df = add_engineered_features(load_raw())
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
