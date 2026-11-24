"""C-MAPSS prognostics primitives. Units are independent engine histories."""
from pathlib import Path

import numpy as np
import pandas as pd

SETTINGS = [f"setting_{i}" for i in range(1, 4)]
SENSORS = [f"sensor_{i}" for i in range(1, 22)]
COLUMNS = ["unit", "cycle"] + SETTINGS + SENSORS


def load_trajectories(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=r"\s+", header=None)
    if frame.empty or frame.shape[1] != len(COLUMNS):
        raise ValueError("Expected nonempty C-MAPSS file with 26 columns")
    frame.columns = COLUMNS
    return validate_trajectories(frame)


def validate_trajectories(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or not set(COLUMNS).issubset(frame.columns):
        raise ValueError("Missing trajectory observations or columns")
    data = frame[COLUMNS].apply(pd.to_numeric, errors="raise").copy()
    if not np.isfinite(data.to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite trajectory observation")
    for col in ("unit", "cycle"):
        values = data[col].to_numpy()
        if (values < 1).any() or (values != np.floor(values)).any():
            raise ValueError(f"{col} must contain positive integers")
        data[col] = data[col].astype("int64")
    data = data.sort_values(["unit", "cycle"]).reset_index(drop=True)
    expected = data.groupby("unit").cumcount() + 1
    if not np.array_equal(data.cycle.to_numpy(), expected.to_numpy()):
        raise ValueError("Each unit must have contiguous cycles beginning at one")
    return data


def training_targets(frame: pd.DataFrame) -> pd.Series:
    """Use ONLY complete run-to-failure training trajectories."""
    return frame.groupby("unit")["cycle"].transform("max") - frame["cycle"]


def causal_features(frame: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Features at cycle t depend exclusively on observations through t."""
    if not isinstance(window, int) or window < 2:
        raise ValueError("Window must be an integer >= 2")
    data = validate_trajectories(frame)
    features = data[["cycle"] + SETTINGS + SENSORS].copy()
    grouped = data.groupby("unit", sort=False)
    rolling = grouped[SENSORS].rolling(window, min_periods=1)
    means = rolling.mean().reset_index(level=0, drop=True).sort_index()
    changes = grouped[SENSORS].diff(window - 1).fillna(0)
    return pd.concat([features, means.add_suffix("_mean"), changes.add_suffix("_delta")], axis=1)


def endpoint_targets(frame: pd.DataFrame, path: str | Path) -> pd.Series:
    """Official test offsets are ordered by unit ID (1..N)."""
    offsets = pd.read_csv(path, sep=r"\s+", header=None)
    units = np.sort(frame.unit.unique())
    if offsets.shape != (len(units), 1) or not np.array_equal(units, np.arange(1, len(units)+1)):
        raise ValueError("RUL file does not match contiguous test unit IDs")
    values = offsets.iloc[:, 0].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any() or (values != np.floor(values)).any():
        raise ValueError("Invalid official RUL offsets")
    return pd.Series(values, index=units, name="rul")


def endpoint_indices(frame: pd.DataFrame) -> np.ndarray:
    """One final observed row per unit, ordered by unit ID."""
    return frame.groupby("unit", sort=True)["cycle"].idxmax().to_numpy()
