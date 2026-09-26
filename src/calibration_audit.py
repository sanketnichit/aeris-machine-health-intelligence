from pathlib import Path

import pandas as pd
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split

try:
    from .features import MODEL_FEATURES, add_engineered_features
    from .models import build_calibrated_hgb
    from .load_data import load_raw
except ImportError:  # direct script execution from src/
    from features import MODEL_FEATURES, add_engineered_features
    from models import build_calibrated_hgb
    from load_data import load_raw

ROOT = Path(__file__).resolve().parents[1]
FEATURES = MODEL_FEATURES


build_model = build_calibrated_hgb

def add_rows(lines, name, subset, prob):
    y = subset["machine_failure"].to_numpy()
    p = prob.loc[subset.index].to_numpy()
    lines.append(
        f"| {name} | {len(subset)} | {int(y.sum())} | {y.mean():.4f} | "
        f"{p.mean():.4f} | {p.mean() - y.mean():+.4f} | "
        f"{brier_score_loss(y, p):.4f} |\n"
    )


def main() -> None:
    df = add_engineered_features(load_raw())
    X = df[FEATURES]
    y = df["machine_failure"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    model = build_model().fit(X_train, y_train)
    prob = pd.Series(model.predict_proba(X_test)[:, 1], index=X_test.index)

    lines = [
        "# AERIS Calibration Audit\n\n",
        "This audit checks how the calibrated risk score behaves across selected "
        "subgroups of the primary held-out test set. The global calibration model "
        "and 0.50 threshold are unchanged.\n\n",
        "A calibration gap is **mean predicted risk minus observed failure rate**. "
        "Positive values indicate average overprediction in that subgroup; negative "
        "values indicate average underprediction.\n\n",
        "## Product-type calibration\n\n",
        "| Group | Rows | Failures | Observed rate | Mean predicted | Calibration gap | Brier |\n",
        "|---|---:|---:|---:|---:|---:|---:|\n",
    ]

    test_frame = X_test.copy()
    test_frame["machine_failure"] = y_test

    for value in ["H", "L", "M"]:
        subset = test_frame[test_frame.type == value]
        add_rows(lines, f"Type {value}", subset, prob)

    lines.extend(
        [
            "\n## High/low operating-regime checks\n\n",
            "The regime boundaries below are fixed from the **training partition "
            "quartiles** and then applied to the held-out test set. This avoids "
            "deriving the operating bands from the test labels.\n\n",
            "| Regime | Rows | Failures | Observed rate | Mean predicted | Calibration gap | Brier |\n",
            "|---|---:|---:|---:|---:|---:|---:|\n",
        ]
    )

    train_frame = X_train.copy()
    train_frame["machine_failure"] = y_train

    for feature, label in [
        ("torque_nm", "Torque"),
        ("rot_speed_rpm", "Rotational speed"),
        ("tool_wear_min", "Tool wear"),
        ("air_temp_k", "Air temperature"),
    ]:
        q1, q3 = train_frame[feature].quantile([0.25, 0.75])
        for band, mask in [
            ("lower quartile", test_frame[feature] <= q1),
            ("upper quartile", test_frame[feature] > q3),
        ]:
            subset = test_frame.loc[mask]
            if len(subset) == 0:
                continue
            add_rows(lines, f"{label} — {band}", subset, prob)

    lines.extend(
        [
            "\n## Risk-bin calibration\n\n",
            "The primary test predictions are partitioned into five equal-count risk "
            "bins. This checks whether higher model scores correspond to higher "
            "observed failure frequency without treating a single threshold as "
            "universally correct.\n\n",
            "| Risk bin | Rows | Observed rate | Mean predicted | Gap |\n",
            "|---|---:|---:|---:|---:|\n",
        ]
    )

    risk_frame = pd.DataFrame(
        {"y": y_test.to_numpy(), "prob": prob.to_numpy()},
        index=y_test.index,
    ).sort_values("prob")
    risk_frame["bin"] = pd.qcut(risk_frame["prob"], q=5, duplicates="drop")

    for interval, subset in risk_frame.groupby("bin", observed=True):
        lines.append(
            f"| {interval.left:.3f}–{interval.right:.3f} | {len(subset)} | "
            f"{subset.y.mean():.4f} | {subset.prob.mean():.4f} | "
            f"{subset.prob.mean() - subset.y.mean():+.4f} |\n"
        )

    lines.extend(
        [
            "\n## Interpretation\n",
            "Calibration is not expected to be identical in every subgroup, especially "
            "when the positive class is rare. The useful check is whether the score "
            "retains reasonable ordering and whether large subgroup calibration gaps "
            "are visible. Any production use would require recalibration and "
            "prospective validation on the actual target population.\n",
        ]
    )

    out = ROOT / "reports" / "calibration_audit.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
