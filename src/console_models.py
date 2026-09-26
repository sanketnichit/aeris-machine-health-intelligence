"""Model bundle used by the AERIS Streamlit console.

The console uses the same seed-42 train/test partition and canonical model
builders as the offline evaluation pipeline. The held-out partition is never
needed by the UI at inference time; it is used only to keep the training
architecture consistent with the documented v1 evaluation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from .features import MODEL_FEATURES, add_engineered_features
from .load_data import load_raw
from .models import build_calibrated_hgb, build_hgb_pipeline, build_mode_pipeline, build_preprocessor

MODES = ["hdf", "pwf", "osf"]


def train_console_models(
    data_path: str | Path,
    *,
    random_state: int = 42,
):
    """Train the console's risk, SHAP tree and failure-mode models.

    The binary risk model is the canonical calibrated HGB used by the offline
    risk-model evaluation. The explanation tree shares the same architecture
    and training partition, while mode models use the canonical class-weighted
    architecture on the same training partition.
    """
    df = add_engineered_features(load_raw(data_path))

    X = df[MODEL_FEATURES]
    y = df["machine_failure"]

    train_idx, _test_idx = train_test_split(
        df.index,
        test_size=0.20,
        random_state=random_state,
        stratify=y,
    )

    X_train = X.loc[train_idx]
    y_train = y.loc[train_idx]

    risk_model = build_calibrated_hgb(
        calibration_method="sigmoid",
        cv=5,
        n_jobs=-1,
    )
    risk_model.fit(X_train, y_train)

    explainer_pre = build_preprocessor()
    transformed_train = explainer_pre.fit_transform(X_train, y_train)

    explain_model = build_hgb_pipeline().named_steps["model"]
    explain_model.fit(transformed_train, y_train)

    mode_models = {}
    for mode in MODES:
        mode_model = build_mode_pipeline()
        mode_model.fit(X_train, df.loc[train_idx, mode])
        mode_models[mode] = mode_model

    return risk_model, explainer_pre, explain_model, mode_models
