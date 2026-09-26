"""
AERIS - Machine Health Intelligence
Data loading utility for the AI4I 2020 Predictive Maintenance Dataset.
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "ai4i2020.csv"

REQUIRED_NORMALIZED_COLUMNS = {
    "udi",
    "product_id",
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
    "machine_failure",
    "twf",
    "hdf",
    "pwf",
    "osf",
    "rnf",
}

RENAME_MAP = {
    "UDI": "udi",
    "Product ID": "product_id",
    "Type": "type",
    "Air temperature [K]": "air_temp_k",
    "Process temperature [K]": "process_temp_k",
    "Rotational speed [rpm]": "rot_speed_rpm",
    "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min",
    "Machine failure": "machine_failure",
    "TWF": "twf",
    "HDF": "hdf",
    "PWF": "pwf",
    "OSF": "osf",
    "RNF": "rnf",
}


def load_raw(path: str | Path = RAW_PATH) -> pd.DataFrame:
    """Load and normalize the source CSV column names."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Place ai4i2020.csv in data/ first."
        )

    df = pd.read_csv(path, encoding="utf-8-sig")
    normalized = df.rename(columns=RENAME_MAP)

    missing = REQUIRED_NORMALIZED_COLUMNS.difference(normalized.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            "Dataset is missing required AI4I columns after normalization: "
            f"{missing_list}"
        )

    return normalized


if __name__ == "__main__":
    frame = load_raw()
    print(f"Loaded {frame.shape[0]:,} rows x {frame.shape[1]} columns")
    print(frame.dtypes)
