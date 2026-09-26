from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

from features import MODEL_FEATURES, add_engineered_features
from models import build_calibrated_hgb
from load_data import load_raw


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "error_analysis.md"

FEATURES = MODEL_FEATURES
MODES = ["twf", "hdf", "pwf", "osf", "rnf"]


build_model = build_calibrated_hgb

def main() -> None:
    df = add_engineered_features(load_raw())
    X = df[FEATURES]
    y = df["machine_failure"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    model = build_model()
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.50).astype(int)

    errors = X_test.copy()
    errors["actual"] = y_test.to_numpy()
    errors["risk"] = prob
    errors["predicted"] = pred
    errors["error"] = "correct"
    errors.loc[
        (errors.actual == 0) & (errors.predicted == 1), "error"
    ] = "false_positive"
    errors.loc[
        (errors.actual == 1) & (errors.predicted == 0), "error"
    ] = "false_negative"
    errors = errors.join(df.loc[errors.index, MODES])

    fp = errors[errors.error == "false_positive"]
    fn = errors[errors.error == "false_negative"]
    tp = errors[(errors.actual == 1) & (errors.predicted == 1)]

    lines = [
        "# AERIS Error Analysis\n\n",
        "This analysis uses the same primary seed-42 held-out test set as the "
        "risk-model report. It is descriptive only: no threshold or model change "
        "is made from these observations.\n\n",
        "## Test-set outcome counts\n",
        f"- True positives: **{len(tp)}**\n",
        f"- False positives: **{len(fp)}**\n",
        f"- False negatives: **{len(fn)}**\n",
        f"- True negatives: **{int(((errors.actual == 0) & (errors.predicted == 0)).sum())}**\n\n",
        "## False-negative profile\n",
        f"- False-negative count: **{len(fn)}**\n",
        f"- Median model risk on false negatives: **{fn.risk.median():.3f}**\n",
        f"- Highest false-negative risk: **{fn.risk.max():.3f}**\n",
        f"- Lowest false-negative risk: **{fn.risk.min():.3f}**\n",
        "- Failure-mode flags among false negatives:\n",
    ]

    for mode in MODES:
        lines.append(f"  - {mode.upper()}: **{int(fn[mode].sum())}**\n")

    lines.append(
        f"  - Multiple mode flags: **{int((fn[MODES].sum(axis=1) > 1).sum())}**\n\n"
    )

    lines.extend(
        [
            "## False-positive profile\n",
            f"- False-positive count: **{len(fp)}**\n",
            f"- Median model risk on false positives: **{fp.risk.median():.3f}**\n",
            f"- Highest false-positive risk: **{fp.risk.max():.3f}**\n\n",
            "## Interpretation\n",
            "False negatives are the principal miss class at the 0.50 threshold. "
            "Their model scores remain below the alert cutoff even though the "
            "benchmark target is positive, which illustrates why a production alert "
            "policy would need an explicit cost for missed failures. The failure-mode "
            "counts are descriptive only because the AI4I mode labels are synthetic "
            "benchmark indicators rather than physical root-cause measurements.\n\n",
            "## Ranking check\n",
            f"Overall held-out average precision remains **{average_precision_score(y_test, prob):.3f}**. "
            "Error analysis is intentionally kept downstream of the fixed evaluation "
            "so it does not become an untracked tuning loop.\n",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))


if __name__ == "__main__":
    main()
