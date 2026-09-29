"""Models used by the Streamlit app.

The app uses the same training setup as the main risk-model script. Trained
models are saved in a local cache so the app does not retrain everything on
every restart.
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from .features import MODEL_FEATURES, add_engineered_features
from .load_data import load_raw
from .models import (
    build_calibrated_hgb,
    build_hgb_pipeline,
    build_mode_pipeline,
    build_preprocessor,
)

MODES = ["hdf", "pwf", "osf"]
CACHE_VERSION = "2026-09-26-console-bundle-v1"


def _cache_path(data_path: Path) -> Path:
    """Return a cache path based on the dataset and model version."""
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()[:16]
    cache_dir = data_path.parent.parent / ".aeris_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"console_bundle_{CACHE_VERSION}_{digest}.pkl"


def _load_cached_bundle(cache_path: Path):
    try:
        with cache_path.open("rb") as handle:
            return pickle.load(handle)
    except (OSError, EOFError, pickle.PickleError, AttributeError, ImportError, ValueError):
        return None


def _save_cached_bundle(cache_path: Path, bundle) -> None:
    temp_path = cache_path.with_suffix(".tmp")
    try:
        with temp_path.open("wb") as handle:
            pickle.dump(bundle, handle, protocol=pickle.HIGHEST_PROTOCOL)
        temp_path.replace(cache_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def train_console_models(
    data_path: str | Path,
    *,
    random_state: int = 42,
):
    """Load the cached models or train them when needed."""
    data_path = Path(data_path)
    cache_path = _cache_path(data_path)

    cached_bundle = _load_cached_bundle(cache_path)
    if cached_bundle is not None:
        return cached_bundle

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

    bundle = (risk_model, explainer_pre, explain_model, mode_models)
    _save_cached_bundle(cache_path, bundle)
    return bundle
