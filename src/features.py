"""
AERIS feature engineering.

Derived features are deterministic transformations of raw operating signals.
They are computed after loading the source data and before model training so that
all model entry points use the same definitions.

Engineering-derived features:
- temp_delta_k: process temperature minus air temperature.
- mechanical_power_kw: torque * rotational speed / 9549.2966.
  This converts N·m and rpm to an approximate mechanical power signal in kW.
"""

from __future__ import annotations

import pandas as pd

BASE_FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]

DERIVED_FEATURES = [
    "temp_delta_k",
    "mechanical_power_kw",
]

MODEL_FEATURES = BASE_FEATURES + DERIVED_FEATURES


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with deterministic AERIS engineering features added."""
    out = df.copy()
    out["temp_delta_k"] = out["process_temp_k"] - out["air_temp_k"]
    out["mechanical_power_kw"] = (
        out["rot_speed_rpm"] * out["torque_nm"] / 9549.2966
    )
    return out
