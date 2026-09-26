"""
AERIS - feature explanation.

The project uses:
1) permutation importance on the held-out test set for robust global ranking;
2) SHAP TreeExplainer on the fitted HistGradientBoosting base model for
   local/global explanation after the core model is trustworthy.

The calibrated wrapper is used for the risk score; SHAP explains the underlying
tree model that produces the uncalibrated score before probability calibration.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import make_scorer, average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from load_data import load_raw


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "explainability.md"

FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]


def main() -> None:
    df = load_raw()
    X = df[FEATURES]
    y = df["machine_failure"]

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
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )

    tree_model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.06,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )

    base_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", tree_model),
        ]
    )

    calibrated = CalibratedClassifierCV(
        base_pipeline,
        method="sigmoid",
        cv=5,
        n_jobs=-1,
    )
    calibrated.fit(X_train, y_train)

    # Permutation importance on the final held-out test set.
    scorer = make_scorer(
        average_precision_score,
        response_method="predict_proba",
    )
    permutation = permutation_importance(
        calibrated,
        X_test,
        y_test,
        scoring=scorer,
        n_repeats=20,
        random_state=42,
        n_jobs=-1,
    )

    permutation_df = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance_mean": permutation.importances_mean,
            "importance_std": permutation.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)

    # SHAP on the fitted underlying tree model, using an unseen test subset.
    fitted_pre = preprocessor.fit(X_train, y_train)
    transformed_train = fitted_pre.transform(X_train)
    transformed_test = fitted_pre.transform(X_test)

    fitted_tree = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.06,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )
    fitted_tree.fit(transformed_train, y_train)

    explainer = shap.TreeExplainer(fitted_tree)
    shap_values = explainer.shap_values(transformed_test[:200])
    transformed_names = fitted_pre.get_feature_names_out()

    shap_importance = (
        pd.DataFrame(
            {
                "feature": transformed_names,
                "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            }
        )
        .sort_values("mean_abs_shap", ascending=False)
    )

    lines = [
        "# AERIS Explainability\n\n",
        "## Global feature importance: permutation importance\n\n",
        "| Feature | Mean AP decrease | Std |\n",
        "|---|---:|---:|\n",
    ]

    for _, row in permutation_df.iterrows():
        lines.append(
            f"| {row['feature']} | {row['importance_mean']:.4f} | "
            f"{row['importance_std']:.4f} |\\n"
        )

    lines.extend(
        [
            "\\nPermutation importance is computed on the held-out test set using "
            "average precision. A larger decrease means the model loses more "
            "ranking performance when that feature is permuted.\\n\\n",
            "## SHAP global importance\\n\\n",
            "| Encoded feature | Mean absolute SHAP |\n",
            "|---|---:|\n",
        ]
    )

    for _, row in shap_importance.iterrows():
        lines.append(
            f"| {row['feature']} | {row['mean_abs_shap']:.4f} |\\n"
        )

    lines.extend(
        [
            "\\nSHAP values are used for explanation, not as evidence that a "
            "feature is a physical root cause. Correlated variables can share "
            "or redistribute model attribution.\\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
