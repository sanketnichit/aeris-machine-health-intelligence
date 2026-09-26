"""
AERIS - Machine Health Intelligence
Data validation: missing values, duplicates, schema sanity checks, class balance.
"""
from pathlib import Path

import pandas as pd

try:
    from .load_data import load_raw
except ImportError:  # direct script execution from src/
    from load_data import load_raw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "data_validation.md"


def validate(df: pd.DataFrame) -> str:
    """Generate a Markdown validation report from a normalized dataframe."""
    lines: list[str] = []
    lines.append("# Data Validation Report\n")
    lines.append(f"- Rows: {df.shape[0]:,}, Columns: {df.shape[1]}\n")

    missing = df.isnull().sum()
    lines.append("## Missing values\n")
    if missing.sum() == 0:
        lines.append("- No missing values in any column.\n")
    else:
        lines.append("Missing values by column:\n\n")
        lines.append(missing[missing > 0].to_string())
        lines.append("\n")

    dupe_rows = int(df.duplicated().sum())
    dupe_udi = int(df["udi"].duplicated().sum())
    dupe_pid = int(df["product_id"].duplicated().sum())

    lines.append("## Duplicates\n")
    lines.append(f"- Fully duplicated rows: {dupe_rows}\n")
    lines.append(f"- Duplicate UDI values: {dupe_udi}\n")
    lines.append(f"- Duplicate Product ID values: {dupe_pid}\n")

    lines.append("## Range sanity checks\n")
    checks = {
        "air_temp_k negative or zero": int((df["air_temp_k"] <= 0).sum()),
        "process_temp_k negative or zero": int((df["process_temp_k"] <= 0).sum()),
        "rot_speed_rpm negative": int((df["rot_speed_rpm"] < 0).sum()),
        "torque_nm negative": int((df["torque_nm"] < 0).sum()),
        "tool_wear_min negative": int((df["tool_wear_min"] < 0).sum()),
        "process_temp < air_temp": int(
            (df["process_temp_k"] < df["air_temp_k"]).sum()
        ),
    }

    for name, count in checks.items():
        lines.append(f"- {name}: {count}\n")

    lines.append("## Categorical check\n")
    lines.append(f"- Unique type values: {sorted(df['type'].unique())}\n")

    flags = df[["twf", "hdf", "pwf", "osf", "rnf"]].sum(axis=1)
    any_flag = (flags > 0).astype(int)
    mismatch = int((any_flag != df["machine_failure"]).sum())

    lines.append("## Target consistency\n")
    lines.append(
        f"- Rows where machine_failure disagrees with any failure-mode flag: "
        f"{mismatch}\n"
    )

    if mismatch:
        mismatched = df[any_flag != df["machine_failure"]]
        lines.append(
            f"- Example mismatched UDIs: {mismatched['udi'].head(10).tolist()}\n"
        )

    lines.append("## Class balance\n")
    counts = df["machine_failure"].value_counts()
    percentages = df["machine_failure"].value_counts(normalize=True) * 100

    lines.append(
        f"- No failure (0): {counts.get(0, 0):,} "
        f"({percentages.get(0, 0):.2f}%)\n"
    )
    lines.append(
        f"- Failure (1): {counts.get(1, 0):,} "
        f"({percentages.get(1, 0):.2f}%)\n"
    )

    lines.append("## Failure-mode counts (among machine_failure == 1)\n")
    failures = df[df["machine_failure"] == 1]

    for mode in ["twf", "hdf", "pwf", "osf", "rnf"]:
        lines.append(f"- {mode.upper()}: {int(failures[mode].sum())}\n")

    multiple_modes = int((flags[df["machine_failure"] == 1] > 1).sum())
    lines.append(
        f"- Rows with more than one failure-mode flag set: {multiple_modes}\n"
    )

    return "".join(lines)


if __name__ == "__main__":
    df = load_raw()
    report = validate(df)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
