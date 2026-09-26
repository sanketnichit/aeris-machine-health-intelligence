"""
AERIS - Machine Health Intelligence
First-pass EDA on AI4I 2020. No modelling yet.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

try:
    from .load_data import load_raw
except ImportError:  # direct script execution from src/
    from load_data import load_raw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "figures"


def savefig(name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"{name}.png", dpi=140)
    plt.close()


def main() -> None:
    df = load_raw()

    # 1. Class balance
    plt.figure(figsize=(4, 4))
    df["machine_failure"].value_counts().sort_index().plot(kind="bar")
    plt.xticks([0, 1], ["No failure", "Failure"], rotation=0)
    plt.ylabel("Count")
    plt.title("Class balance: machine failure")
    savefig("01_class_balance")

    # 2. Failure rate by product type
    rate_by_type = df.groupby("type")["machine_failure"].mean().sort_values()
    plt.figure(figsize=(4, 4))
    rate_by_type.plot(kind="bar")
    plt.ylabel("Failure rate")
    plt.title("Failure rate by product type")
    savefig("02_failure_rate_by_type")

    # 3. Temperature difference vs failure
    df["temp_diff_k"] = df["process_temp_k"] - df["air_temp_k"]
    plt.figure(figsize=(5, 4))
    for label, group in df.groupby("machine_failure"):
        plt.scatter(
            group["rot_speed_rpm"],
            group["temp_diff_k"],
            s=6,
            alpha=0.4,
            label="Failure" if label else "Normal",
        )
    plt.axhline(
        8.6,
        linestyle="--",
        linewidth=1,
        label="HDF threshold (8.6 K)",
    )
    plt.xlabel("Rotational speed (rpm)")
    plt.ylabel("Process - Air temperature (K)")
    plt.title("Heat-dissipation failure zone")
    plt.legend()
    savefig("03_temp_diff_vs_speed")

    # 4. Torque vs tool wear
    plt.figure(figsize=(5, 4))
    for label, group in df.groupby("machine_failure"):
        plt.scatter(
            group["tool_wear_min"],
            group["torque_nm"],
            s=6,
            alpha=0.4,
            label="Failure" if label else "Normal",
        )
    plt.xlabel("Tool wear (min)")
    plt.ylabel("Torque (Nm)")
    plt.title("Overstrain failure zone")
    plt.legend()
    savefig("04_torque_vs_toolwear")

    # 5. Failure-mode breakdown
    fail_df = df[df["machine_failure"] == 1]
    mode_counts = (
        fail_df[["twf", "hdf", "pwf", "osf", "rnf"]]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(5, 4))
    mode_counts.plot(kind="bar")
    plt.ylabel("Count among labelled failures")
    plt.title("Failure-mode breakdown")
    savefig("05_failure_mode_breakdown")

    # 6. Correlation heatmap
    num_cols = [
        "air_temp_k",
        "process_temp_k",
        "rot_speed_rpm",
        "torque_nm",
        "tool_wear_min",
        "machine_failure",
    ]
    corr = df[num_cols].corr()

    plt.figure(figsize=(6, 5))
    image = plt.imshow(corr, vmin=-1, vmax=1)
    plt.xticks(
        range(len(num_cols)),
        num_cols,
        rotation=45,
        ha="right",
    )
    plt.yticks(range(len(num_cols)), num_cols)

    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            plt.text(
                j,
                i,
                f"{corr.iloc[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=8,
            )

    plt.colorbar(image, fraction=0.046, pad=0.04)
    plt.title("Correlation matrix")
    savefig("06_correlation_heatmap")

    print("Saved 6 figures to figures/")
    print("\nFailure rate by type:\n", rate_by_type)
    print(
        "\nCorrelation with machine_failure:\n",
        corr["machine_failure"].sort_values(ascending=False),
    )


if __name__ == "__main__":
    main()
