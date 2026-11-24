"""Published AI4I generation rules, not validated industrial safety limits.

Source: https://doi.org/10.24432/C5HS5C
Only observable inputs are used. Stochastic TWF/RNF are not reconstructed.
"""
import numpy as np
import pandas as pd

from .features import BASE_FEATURES


def rule_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    """Return three deterministic flags and their union, preserving row index."""
    missing = set(BASE_FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing observed inputs: {sorted(missing)}")
    numeric = frame[BASE_FEATURES[1:]].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Rule inputs must be finite")
    limits = frame["type"].map({"L": 11000, "M": 12000, "H": 13000})
    if limits.isna().any():
        raise ValueError("Unknown product type")
    rpm = numeric["rot_speed_rpm"]
    torque = numeric["torque_nm"]
    power = torque * rpm * (2 * np.pi / 60)
    delta = numeric["process_temp_k"] - numeric["air_temp_k"]
    flags = pd.DataFrame({
        "hdf": (delta < 8.6) & (rpm < 1380),
        "pwf": (power < 3500) | (power > 9000),
        "osf": numeric["tool_wear_min"] * torque > limits,
    }, index=frame.index)
    flags["rule_failure"] = flags.any(axis=1)
    return flags
