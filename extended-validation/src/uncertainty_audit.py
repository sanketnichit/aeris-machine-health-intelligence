from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import numpy as np
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
REPORT = ROOT / "extended-validation" / "reports" / "uncertainty_audit.md"

FEATURES = MODEL_FEATURES

RNG_SEED = 20260926
N_BOOTSTRAP = 3000


build_model = build_calibrated_hgb

def stratified_bootstrap(
    y: np.ndarray,
    p: np.ndarray,
    threshold: float,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y == 0)
    out: dict[str, list[float]] = {
        "pr_auc": [],
        "precision": [],
        "recall": [],
        "f1": [],
        "brier": [],
    }

    for _ in range(N_BOOTSTRAP):
        idx_pos = rng.choice(pos, size=len(pos), replace=True)
        idx_neg = rng.choice(neg, size=len(neg), replace=True)
        idx = np.concatenate([idx_pos, idx_neg])
        y_b = y[idx]
        p_b = p[idx]
        pred_b = (p_b >= threshold).astype(int)

        out["pr_auc"].append(average_precision_score(y_b, p_b))
        out["precision"].append(
            precision_score(y_b, pred_b, zero_division=0)
        )
        out["recall"].append(recall_score(y_b, pred_b, zero_division=0))
        out["f1"].append(f1_score(y_b, pred_b, zero_division=0))
        out["brier"].append(brier_score_loss(y_b, p_b))

    return {key: np.asarray(values) for key, values in out.items()}


def ci(values: np.ndarray) -> tuple[float, float]:
    return tuple(np.percentile(values, [2.5, 97.5]))


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

    model = build_model()
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.50).astype(int)

    rng = np.random.default_rng(RNG_SEED)
    boot = stratified_bootstrap(
        y_test.to_numpy(),
        prob,
        threshold=0.50,
        rng=rng,
    )

    cm = pd.crosstab(
        pd.Series(y_test.to_numpy(), name="actual"),
        pd.Series(pred, name="predicted"),
        dropna=False,
    )
    tn = int(cm.loc[0, 0])
    fp = int(cm.loc[0, 1])
    fn = int(cm.loc[1, 0])
    tp = int(cm.loc[1, 1])

    point_metrics = {
        "PR-AUC": average_precision_score(y_test, prob),
        "Precision": precision_score(y_test, pred, zero_division=0),
        "Recall": recall_score(y_test, pred, zero_division=0),
        "F1": f1_score(y_test, pred, zero_division=0),
        "Brier score": brier_score_loss(y_test, prob),
    }
    key_map = {
        "PR-AUC": "pr_auc",
        "Precision": "precision",
        "Recall": "recall",
        "F1": "f1",
        "Brier score": "brier",
    }

    lines = [
        "# Uncertainty Check\n\n",
        "This is an extra check. It does not change the model, "
        "threshold, or held-out test split. The final 20% test partition remains "
        "untouched during training and model selection.\n\n",
        "## Held-out test composition\n",
        f"- Test rows: **{len(y_test):,}**\n",
        f"- Failures: **{int(y_test.sum()):,}**\n",
        f"- Non-failures: **{int((y_test == 0).sum()):,}**\n\n",
        "## Point estimates at calibrated threshold 0.50\n",
        f"- PR-AUC: **{point_metrics['PR-AUC']:.3f}**\n",
        f"- Precision: **{point_metrics['Precision']:.3f}**\n",
        f"- Recall: **{point_metrics['Recall']:.3f}**\n",
        f"- F1: **{point_metrics['F1']:.3f}**\n",
        f"- Brier score: **{point_metrics['Brier score']:.4f}**\n\n",
        "## 95% stratified bootstrap intervals\n",
        "Bootstrap resamples preserve the observed number of positive and negative "
        "test examples in each resample. Intervals describe sampling uncertainty "
        "around this held-out evaluation; they are not guarantees of real-world "
        "performance.\n\n",
        "| Metric | Estimate | 95% interval |\n",
        "|---|---:|---:|\n",
    ]

    for name, estimate in point_metrics.items():
        lo, hi = ci(boot[key_map[name]])
        lines.append(
            f"| {name} | {estimate:.4f} | [{lo:.4f}, {hi:.4f}] |\n"
        )

    lines.extend(
        [
            "\n## Confusion matrix at 0.50\n\n",
            "| | Predicted 0 | Predicted 1 |\n",
            "|---|---:|---:|\n",
            f"| Actual 0 | {tn} | {fp} |\n",
            f"| Actual 1 | {fn} | {tp} |\n\n",
            "## Error profile\n",
            f"- False positives: **{fp}** — normal observations flagged above "
            "the current threshold.\n",
            f"- False negatives: **{fn}** — failures not flagged above the current "
            "threshold.\n",
            "- Threshold changes therefore represent an explicit precision/recall "
            "trade-off rather than a universally correct operating point.\n\n",
            "## What this means\n",
            "The headline risk-model metrics are useful, but the confidence intervals "
            "show that they should not be treated as exact constants. The positive "
            "class is small even in the held-out test set, so uncertainty matters. "
            "A real deployment would require prospective validation, drift monitoring, "
            "and threshold selection against explicit maintenance costs.\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
