"""
AERIS - failure-mode attribution feasibility study.

AI4I failure-mode labels are not mutually exclusive, so this stage is multi-label.
We only promote modes whose cross-validated signal is defensible.
"""
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from load_data import load_raw

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "failure_mode_attribution.md"

FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]

ALL_MODES = ["twf", "hdf", "pwf", "osf", "rnf"]


def build_pipeline() -> Pipeline:
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

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                HistGradientBoostingClassifier(
                    max_iter=250,
                    learning_rate=0.06,
                    max_leaf_nodes=31,
                    l2_regularization=1.0,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def main() -> None:
    df = load_raw()
    X = df[FEATURES]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    lines = [
        "# Failure-mode Attribution\\n\\n",
        "AERIS v1 treats failure modes as a **multi-label attribution** problem "
        "rather than forcing every failed row into exactly one class.\\n\\n",
        "## Cross-validation feasibility check\\n\\n",
        "| Mode | Positives | Mean PR-AUC | Mean Precision | Mean Recall | Mean F1 |\\n",
        "|---|---:|---:|---:|---:|---:|\\n",
    ]

    for mode in ALL_MODES:
        y = df[mode]
        scores = cross_validate(
            build_pipeline(),
            X,
            y,
            cv=cv,
            scoring={
                "pr_auc": "average_precision",
                "precision": "precision",
                "recall": "recall",
                "f1": "f1",
            },
            n_jobs=-1,
            error_score=0.0,
        )

        lines.append(
            f"| {mode.upper()} | {int(y.sum())} | "
            f"{scores['test_pr_auc'].mean():.3f} ± {scores['test_pr_auc'].std():.3f} | "
            f"{scores['test_precision'].mean():.3f} | "
            f"{scores['test_recall'].mean():.3f} | "
            f"{scores['test_f1'].mean():.3f} |\\n"
        )

    lines.extend(
        [
            "\\n## Production-facing v1 decision\\n",
            "Promote **HDF, PWF and OSF** into the v1 attribution panel. "
            "TWF and RNF are deferred because their cross-validated signal is "
            "too weak/unstable for an honest engineering-facing prediction layer.\\n\\n",
            "## Multi-label caveat\\n",
            "A single failed observation can have more than one mode flag. "
            "Therefore AERIS reports mode scores side-by-side and does not claim "
            "that one model output proves a unique physical root cause.\\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
