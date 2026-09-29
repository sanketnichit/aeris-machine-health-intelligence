"""Model-building helpers shared by the main scripts and Streamlit app.

Keeping the preprocessing and HGB setup here avoids having slightly different
model definitions in different files.
"""

from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

try:
    from .features import MODEL_FEATURES
except ImportError:  # direct script execution from src/
    from features import MODEL_FEATURES


HGB_PARAMS = {
    "max_iter": 300,
    "learning_rate": 0.06,
    "max_leaf_nodes": 31,
    "l2_regularization": 1.0,
    "random_state": 42,
}

MODE_HGB_PARAMS = {
    "max_iter": 250,
    "learning_rate": 0.06,
    "max_leaf_nodes": 31,
    "l2_regularization": 1.0,
    "class_weight": "balanced",
    "random_state": 42,
}


def build_preprocessor(features: list[str] | None = None) -> ColumnTransformer:
    """Build the preprocessor for the selected feature list."""
    resolved = MODEL_FEATURES if features is None else list(features)
    return ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                ["type"],
            ),
            ("numeric", "passthrough", resolved[1:]),
        ]
    )


def build_hgb_pipeline(features: list[str] | None = None) -> Pipeline:
    """Build the HistGradientBoosting pipeline used by the project."""
    return Pipeline(
        [
            ("preprocessor", build_preprocessor(features)),
            ("model", HistGradientBoostingClassifier(**HGB_PARAMS)),
        ]
    )


def build_calibrated_hgb(
    *,
    calibration_method: str = "sigmoid",
    cv: int = 5,
    n_jobs: int = -1,
    features: list[str] | None = None,
) -> CalibratedClassifierCV:
    """Build the calibrated risk model for the selected feature list."""
    return CalibratedClassifierCV(
        build_hgb_pipeline(features),
        method=calibration_method,
        cv=cv,
        n_jobs=n_jobs,
    )


def build_mode_pipeline() -> Pipeline:
    """Build the secondary failure-mode attribution model."""
    return Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            ("model", HistGradientBoostingClassifier(**MODE_HGB_PARAMS)),
        ]
    )
