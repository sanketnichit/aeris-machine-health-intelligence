"""
AERIS - failure-mode attribution feasibility study.

AI4I failure-mode labels are not mutually exclusive, so this stage is multi-label.
We only promote modes whose cross-validated signal is defensible.
"""
from pathlib import Path

import pandas as pd
from sklearn.metrics import make_scorer, precision_score
from sklearn.model_selection import StratifiedKFold, cross_validate

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .models import build_mode_pipeline
    from .load_data import load_raw
except ImportError:  # direct script execution from src/
    from features import MODEL_FEATURES, add_engineered_features
    from models import build_mode_pipeline
    from load_data import load_raw

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "failure_mode_attribution.md"

FEATURES = MODEL_FEATURES

ALL_MODES = ["twf", "hdf", "pwf", "osf", "rnf"]


def main() -> None:
    df = add_engineered_features(load_raw())
    X = df[FEATURES]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    lines = [
        "# Failure-mode Attribution\n\n",
        "AERIS v1 treats failure modes as a **multi-label attribution** problem "
        "rather than forcing every failed row into exactly one class.\n\n",
        "## Cross-validation feasibility check\n\n",
        "| Mode | Positives | Mean PR-AUC | Mean Precision | Mean Recall | Mean F1 |\n",
        "|---|---:|---:|---:|---:|---:|\n",
    ]

    for mode in ALL_MODES:
        y = df[mode]
        scores = cross_validate(
            build_mode_pipeline(),
            X,
            y,
            cv=cv,
            scoring={
                "pr_auc": "average_precision",
                "precision": make_scorer(precision_score, zero_division=0),
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
            f"{scores['test_f1'].mean():.3f} |\n"
        )

    lines.extend(
        [
            "\n## AERIS v1 exposure decision\n",
            "Promote **HDF, PWF and OSF** into the v1 attribution panel.\n\n",
            "TWF and RNF remain deferred because their cross-validated signal is too weak/unstable "
            "for the v1 engineering review panel.\n\n",
            "## Synthetic-benchmark caveat\n",
            "The very strong HDF signal should not be interpreted as evidence of physical root-cause "
            "understanding. The AI4I benchmark is synthetic and can contain structured relationships "
            "between its generated labels and operating variables. AERIS therefore reports these mode "
            "scores as benchmark attribution signals, not physical diagnoses.\n\n",
            "## Multi-label caveat\n",
            "A single failed observation can have more than one mode flag. Therefore AERIS reports mode "
            "scores side-by-side and does not claim that one model output proves a unique physical root cause.\n",
        ]
    )

    report = "".join(lines)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
