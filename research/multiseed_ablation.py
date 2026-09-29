"""AERIS research experiment: multi-seed feature ablation.

This script intentionally reuses the repository's data loading, feature
engineering, and preprocessing definitions, while varying the train/test seed
and the HGB model seed. It compares the raw AERIS feature contract against the
raw + deterministic engineered feature contract.

No source labels or failure-mode columns are used as predictors.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
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

from src.features import BASE_FEATURES, MODEL_FEATURES, add_engineered_features
from src.load_data import load_raw
from src.models import HGB_PARAMS, build_preprocessor

SEEDS = [0, 1, 2, 3, 4, 42, 123, 456, 789, 999]


def build_calibrated_model(features: list[str], seed: int) -> CalibratedClassifierCV:
    params = dict(HGB_PARAMS)
    params["random_state"] = seed
    base = Pipeline(
        [
            ("preprocessor", build_preprocessor(features)),
            ("model", HistGradientBoostingClassifier(**params)),
        ]
    )
    return CalibratedClassifierCV(
        base,
        method="sigmoid",
        cv=5,
        n_jobs=-1,
    )


def evaluate(
    df: pd.DataFrame,
    features: list[str],
    split_seed: int,
    model_seed: int,
    variant: str,
) -> dict[str, float | int | str]:
    X_train, X_test, y_train, y_test = train_test_split(
        df[features],
        df["machine_failure"],
        test_size=0.20,
        random_state=split_seed,
        stratify=df["machine_failure"],
    )

    model = build_calibrated_model(features, model_seed)
    model.fit(X_train, y_train)

    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.50).astype(int)

    return {
        "variant": variant,
        "seed": split_seed,
        "model_seed": model_seed,
        "pr_auc": average_precision_score(y_test, prob),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "brier": brier_score_loss(y_test, prob),
    }


def main() -> None:
    raw = load_raw()
    engineered = add_engineered_features(raw)

    rows: list[dict[str, float | int | str]] = []

    for seed in SEEDS:
        rows.append(
            evaluate(
                raw,
                BASE_FEATURES,
                split_seed=seed,
                model_seed=seed,
                variant="raw",
            )
        )
        rows.append(
            evaluate(
                engineered,
                MODEL_FEATURES,
                split_seed=seed,
                model_seed=seed,
                variant="raw_plus_engineered",
            )
        )

    results = pd.DataFrame(rows)
    raw_results = results[results["variant"] == "raw"].set_index("seed")
    eng_results = results[results["variant"] == "raw_plus_engineered"].set_index("seed")

    paired = pd.DataFrame(index=raw_results.index)
    for metric in ["pr_auc", "precision", "recall", "f1", "brier"]:
        paired[f"{metric}_delta"] = eng_results[metric] - raw_results[metric]

    summary_rows = []
    for variant, group in results.groupby("variant", sort=False):
        for metric in ["pr_auc", "precision", "recall", "f1", "brier"]:
            summary_rows.append(
                {
                    "variant": variant,
                    "metric": metric,
                    "mean": group[metric].mean(),
                    "std": group[metric].std(ddof=1),
                    "min": group[metric].min(),
                    "max": group[metric].max(),
                }
            )

    summary = pd.DataFrame(summary_rows)

    report_dir = PROJECT_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(report_dir / "research_multiseed_ablation_results.csv", index=False)
    summary.to_csv(report_dir / "research_multiseed_ablation_summary.csv", index=False)

    print("\nAERIS MULTI-SEED ABLATION")
    print("=" * 88)
    print(f"Seeds: {SEEDS}")
    print("Evaluation: stratified 80/20 split per seed; sigmoid calibration with 5-fold CV")
    print("Threshold for precision/recall/F1: 0.50")
    print()

    display_cols = ["variant", "seed", "pr_auc", "precision", "recall", "f1", "brier"]
    print(results[display_cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()

    print("SUMMARY (mean ± SD)")
    print("-" * 88)
    for variant in ["raw", "raw_plus_engineered"]:
        sub = results[results["variant"] == variant]
        print(f"\n{variant}")
        for metric in ["pr_auc", "precision", "recall", "f1", "brier"]:
            print(
                f"  {metric:9s}: "
                f"{sub[metric].mean():.4f} ± {sub[metric].std(ddof=1):.4f} "
                f"(range {sub[metric].min():.4f}–{sub[metric].max():.4f})"
            )

    print("\nPAIRED ENGINEERED - RAW DELTAS")
    print("-" * 88)
    print(
        paired.reset_index().to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print("\nPAIRWISE IMPROVEMENT COUNTS")
    print("-" * 88)
    for metric in ["pr_auc_delta", "precision_delta", "recall_delta", "f1_delta", "brier_delta"]:
        values = paired[metric]
        better = (values > 0).sum()
        worse = (values < 0).sum()
        equal = (values == 0).sum()
        direction = "higher is better" if metric != "brier_delta" else "lower is better"
        print(
            f"{metric:14s}: better={better}, worse={worse}, equal={equal} ({direction})"
        )

    print("\nRESEARCH INTERPRETATION")
    print("-" * 88)
    pr_gain = paired["pr_auc_delta"]
    print(
        f"Engineered-feature PR-AUC delta: mean {pr_gain.mean():+.4f}, "
        f"median {pr_gain.median():+.4f}, "
        f"min {pr_gain.min():+.4f}, max {pr_gain.max():+.4f}."
    )
    print(
        "This is a paired robustness experiment across predefined random seeds; "
        "it is not a significance test and does not establish causality."
    )


if __name__ == "__main__":
    main()
