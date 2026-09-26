from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, make_scorer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from features import MODEL_FEATURES, add_engineered_features
from load_data import load_raw

ROOT = Path(__file__).resolve().parents[1]
FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]
SPLIT_SEEDS = [42, 7, 21, 84, 123]
N_REPEATS = 10


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["type"],
            ),
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )
    model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.06,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )
    return Pipeline([("preprocessor", pre), ("model", model)])


def main() -> None:
    df = add_engineered_features(load_raw())
    X = df[FEATURES]
    y = df["machine_failure"]

    scorer = make_scorer(average_precision_score, response_method="predict_proba")
    all_rows = []

    for seed in SPLIT_SEEDS:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, stratify=y, random_state=seed
        )
        model = build_pipeline().fit(X_train, y_train)
        base_ap = average_precision_score(
            y_test, model.predict_proba(X_test)[:, 1]
        )
        pi = permutation_importance(
            model,
            X_test,
            y_test,
            scoring=scorer,
            n_repeats=N_REPEATS,
            random_state=seed,
            n_jobs=-1,
        )
        fold = pd.DataFrame(
            {
                "seed": seed,
                "feature": FEATURES,
                "importance_mean": pi.importances_mean,
                "importance_std": pi.importances_std,
                "base_pr_auc": base_ap,
            }
        )
        fold["rank"] = (
            fold["importance_mean"]
            .rank(method="min", ascending=False)
            .astype(int)
        )
        all_rows.append(fold)

    result = pd.concat(all_rows, ignore_index=True)
    summary = (
        result.groupby("feature")
        .agg(
            mean_ap_drop=("importance_mean", "mean"),
            std_ap_drop=("importance_mean", "std"),
            mean_rank=("rank", "mean"),
            best_rank=("rank", "min"),
            worst_rank=("rank", "max"),
        )
        .sort_values("mean_ap_drop", ascending=False)
    )

    rank_pivot = result.pivot(index="seed", columns="feature", values="rank")
    summary["top1_count"] = (rank_pivot == 1).sum()
    summary["top2_count"] = (rank_pivot <= 2).sum()

    lines = [
        "# AERIS Feature-Stability Audit\n\n",
        "This audit measures permutation importance across five independent "
        "stratified 80/20 splits using the fixed HistGradientBoosting architecture. "
        "Importance is measured as the decrease in average precision on each "
        "held-out split. The audit is descriptive and does not tune model "
        "hyperparameters or thresholds.\n\n",
        "## Stability summary\n\n",
        "| Feature | Mean AP drop | Across-split SD | Mean rank | Best rank | Worst rank | Top-1 splits | Top-2 splits |\n",
        "|---|---:|---:|---:|---:|---:|---:|---:|\n",
    ]

    for feature, row in summary.iterrows():
        lines.append(
            f"| {feature} | {row.mean_ap_drop:.4f} | {row.std_ap_drop:.4f} | "
            f"{row.mean_rank:.2f} | {int(row.best_rank)} | {int(row.worst_rank)} | "
            f"{int(row.top1_count)}/5 | {int(row.top2_count)}/5 |\n"
        )

    lines.extend(
        [
            "\n## Per-split importance\n\n",
            "| Seed | Feature | AP drop | Rank |\n",
            "|---:|---|---:|---:|\n",
        ]
    )

    for _, row in result.sort_values(["seed", "rank"]).iterrows():
        lines.append(
            f"| {int(row.seed)} | {row.feature} | {row.importance_mean:.4f} | "
            f"{int(row['rank'])} |\n"
        )

    lines.extend(
        [
            "\n## Interpretation\n",
            "Feature importance is not a causal ranking, and correlated variables "
            "can share attribution. The useful question here is whether the broad "
            "ordering is stable across plausible held-out partitions. Large movement "
            "in rank is evidence that a feature's importance should be treated "
            "cautiously rather than presented as universally dominant.\n",
        ]
    )

    out = ROOT / "reports" / "feature_stability.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
