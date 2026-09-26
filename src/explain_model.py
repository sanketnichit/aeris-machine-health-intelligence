"""
AERIS - feature explanation.

Global permutation importance uses the canonical calibrated risk model on the
held-out test set. SHAP explains the canonical underlying HistGradientBoosting
model before probability calibration.

Model attribution is not physical causality.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, make_scorer
from sklearn.model_selection import train_test_split

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .load_data import load_raw
    from .models import build_calibrated_hgb, build_hgb_pipeline, build_preprocessor
except ImportError:  # direct script execution from src/
    from features import MODEL_FEATURES, add_engineered_features
    from load_data import load_raw
    from models import build_calibrated_hgb, build_hgb_pipeline, build_preprocessor


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "explainability.md"
FEATURES = MODEL_FEATURES

DISPLAY_NAMES = {
    "type": "Type",
    "air_temp_k": "Air temperature [K]",
    "process_temp_k": "Process temperature [K]",
    "rot_speed_rpm": "Rotational speed [rpm]",
    "torque_nm": "Torque [Nm]",
    "tool_wear_min": "Tool wear [min]",
    "temp_delta_k": "Temperature delta [K]",
    "mechanical_power_kw": "Mechanical power [kW]",
}


def display_feature(name: str) -> str:
    """Map the internal feature contract to a stable human-readable label."""
    return DISPLAY_NAMES.get(name, name)


def display_transformed_feature(name: str) -> str:
    """Map a transformed preprocessing name to a readable label."""
    if name.startswith("categorical__type_"):
        return name.replace("categorical__type_", "Type_")
    if name.startswith("numeric__"):
        return display_feature(name.replace("numeric__", ""))
    return name


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

    calibrated = build_calibrated_hgb(cv=5, n_jobs=-1)
    calibrated.fit(X_train, y_train)

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
            "feature": [display_feature(feature) for feature in FEATURES],
            "importance_mean": permutation.importances_mean,
            "importance_std": permutation.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)

    # Fit the canonical underlying tree architecture on the training partition.
    explainer_pre = build_preprocessor()
    transformed_train = explainer_pre.fit_transform(X_train, y_train)
    transformed_test = explainer_pre.transform(X_test)

    fitted_tree = build_hgb_pipeline().named_steps["model"]
    fitted_tree.fit(transformed_train, y_train)

    explainer = shap.TreeExplainer(fitted_tree)
    shap_values = np.asarray(explainer.shap_values(transformed_test[:200]))
    transformed_names = explainer_pre.get_feature_names_out()

    shap_importance = (
        pd.DataFrame(
            {
                "feature": [display_transformed_feature(name) for name in transformed_names],
                "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            }
        )
        .sort_values("mean_abs_shap", ascending=False)
    )

    lines = [
        "# AERIS Explainability\n\n",
        "## Global feature importance: permutation importance\n\n",
        "| Feature | Mean AP decrease |\n",
        "|---|---:|\n",
    ]

    for _, row in permutation_df.iterrows():
        lines.append(
            f"| {row['feature']} | {row['importance_mean']:.4f} |\n"
        )

    lines.extend(
        [
            "\nPermutation importance is computed on the held-out test set using "
            "average precision. A larger decrease means the model loses more "
            "ranking performance when that feature is permuted.\n\n",
            "## SHAP global importance\n\n",
            "| Encoded feature | Mean absolute SHAP |\n",
            "|---|---:|\n",
        ]
    )

    for _, row in shap_importance.iterrows():
        lines.append(
            f"| {row['feature']} | {row['mean_abs_shap']:.4f} |\n"
        )

    lines.extend(
        [
            "\nSHAP values explain the underlying tree model before probability "
            "calibration. They are model attributions, not physical root-cause "
            "measurements. Correlated raw and engineered variables can share or "
            "redistribute attribution.\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
