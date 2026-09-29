"""
AERIS - Machine Health Intelligence
Focused Streamlit engineering console.

The UI is intentionally a thin presentation layer over the canonical AERIS
feature contract and model bundle. It does not define a second ML pipeline.
Run: streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import shap
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier

from src.console_models import train_console_models
from src.features import MODEL_FEATURES, add_engineered_features


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "ai4i2020.csv"

DATASET_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"

EXPECTED_DATASET_HEADER = (
    "UDI,Product ID,Type,Air temperature [K],Process temperature [K],"
    "Rotational speed [rpm],Torque [Nm],Tool wear [min],Machine failure,"
    "TWF,HDF,PWF,OSF,RNF"
)

def ensure_dataset() -> None:
    """Download the benchmark CSV if it is missing."""
    if DATA_PATH.exists():
        return

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        DATASET_URL,
        headers={"User-Agent": "AERIS-streamlit/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
    except urllib.error.URLError as exc:
        st.error(
            "The AI4I benchmark CSV is missing and could not be downloaded from UCI. "
            "Download it manually to data/ai4i2020.csv. Network error: " + str(exc)
        )
        st.stop()

    header = payload.splitlines()[0].decode("utf-8-sig").strip()
    if header != EXPECTED_DATASET_HEADER:
        st.error(
            "The downloaded file did not match the expected AI4I 2020 schema. "
            "Download the canonical CSV and place it at data/ai4i2020.csv."
        )
        st.stop()

    temp_path = DATA_PATH.with_suffix(".csv.tmp")
    try:
        temp_path.write_bytes(payload)
        temp_path.replace(DATA_PATH)
    finally:
        if temp_path.exists():
            temp_path.unlink()


ensure_dataset()
RISK_THRESHOLD = 0.50
SCREENING_THRESHOLD = 0.20

# Primary seed-42 held-out evaluation for the current engineered-feature model.
MODEL_PR_AUC = 0.899
MODEL_PRECISION = 0.965
MODEL_RECALL = 0.809
MODEL_F1 = 0.880
MODEL_BRIER = 0.0075
BOOTSTRAP_PR_AUC = "[0.835, 0.953]"
BOOTSTRAP_F1 = "[0.817, 0.938]"

DEMO_PRESETS = {
    "Held-out failure example": {
        "type": "L",
        "air_temp_k": 300.8,
        "process_temp_k": 309.9,
        "rot_speed_rpm": 1312,
        "torque_nm": 65.3,
        "tool_wear_min": 192,
    },
    "Held-out non-failure example": {
        "type": "L",
        "air_temp_k": 297.6,
        "process_temp_k": 308.6,
        "rot_speed_rpm": 1576,
        "torque_nm": 32.7,
        "tool_wear_min": 83,
    },
    "High tool-wear stress test": {
        "type": "M",
        "air_temp_k": 300.1,
        "process_temp_k": 310.4,
        "rot_speed_rpm": 1650,
        "torque_nm": 46.0,
        "tool_wear_min": 235,
    },
    "High-load stress test": {
        "type": "H",
        "air_temp_k": 301.2,
        "process_temp_k": 311.1,
        "rot_speed_rpm": 1950,
        "torque_nm": 68.0,
        "tool_wear_min": 180,
    },
}


def risk_state(risk: float) -> tuple[str, str]:
    if risk >= RISK_THRESHOLD:
        return "HIGH RISK", "Threshold crossed"
    if risk >= SCREENING_THRESHOLD:
        return "ELEVATED", "Screening signal"
    return "LOWER RISK", "Below threshold"


def review_message(risk: float) -> str:
    if risk >= RISK_THRESHOLD:
        return (
            "Model recommendation: **flag this observation for engineering review**. "
            "The score is above the current 0.50 demonstration threshold."
        )
    if risk >= SCREENING_THRESHOLD:
        return (
            "Model recommendation: **retain as a screening signal** and review the "
            "operating context before drawing a conclusion."
        )
    return (
        "Model recommendation: **no alert from the current threshold**. "
        "A low score does not guarantee healthy operation."
    )


def format_direction(value: float) -> str:
    if value > 0:
        return "Pushes toward failure"
    if value < 0:
        return "Pushes toward non-failure"
    return "Near-neutral"


@st.cache_resource
def train_models():
    """Train the model used by the Streamlit demo."""
    return train_console_models(DATA_PATH, random_state=42)


@st.cache_resource
def get_shap_explainer(_model: HistGradientBoostingClassifier):
    """Cache the SHAP explainer without hashing the sklearn model object.

    Streamlit's default argument hashing can choke on function-bearing sklearn
    objects. The leading underscore intentionally excludes the already-canonical
    model from cache-key hashing while retaining the explainer across reruns.
    The console model bundle is fixed for the running AERIS process.
    """
    return shap.TreeExplainer(_model)


def local_shap(
    preprocessor: ColumnTransformer,
    tree_model: HistGradientBoostingClassifier,
    row: pd.DataFrame,
) -> pd.DataFrame:
    transformed = preprocessor.transform(row)
    explainer = get_shap_explainer(tree_model)
    raw_values = explainer.shap_values(transformed)
    if isinstance(raw_values, list):
        raw_values = raw_values[1] if len(raw_values) > 1 else raw_values[0]
    values = np.asarray(raw_values).reshape(-1)
    names = preprocessor.get_feature_names_out()

    rows: list[tuple[str, float]] = []
    type_total = 0.0

    display_names = {
        "air_temp_k": "Air temperature",
        "process_temp_k": "Process temperature",
        "rot_speed_rpm": "Rotational speed",
        "torque_nm": "Torque",
        "tool_wear_min": "Tool wear",
        "temp_delta_k": "Temperature delta",
        "mechanical_power_kw": "Mechanical power",
    }

    for name, value in zip(names, values):
        if name.startswith("categorical__type_"):
            type_total += float(value)
        else:
            internal = name.replace("numeric__", "")
            rows.append(
                (
                    display_names.get(internal, internal),
                    float(value),
                )
            )

    rows.append(("Machine type", type_total))

    return (
        pd.DataFrame(rows, columns=["Feature", "SHAP value"])
        .assign(
            abs_value=lambda d: d["SHAP value"].abs(),
            Direction=lambda d: d["SHAP value"].map(format_direction),
        )
        .sort_values("abs_value", ascending=False)
    )


st.set_page_config(
    page_title="AERIS | Machine Failure Prediction",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.35rem;
            font-weight: 760;
            margin-bottom: 0.1rem;
        }
        .subtitle {
            color: #6b7280;
            font-size: 1rem;
            margin-bottom: 0.7rem;
        }
        .section-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            color: #6b7280;
            font-weight: 750;
        }
        .status-pill {
            display: inline-block;
            padding: 0.30rem 0.65rem;
            border-radius: 999px;
            background: #ecfdf5;
            color: #047857;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .decision-card {
            padding: 0.9rem 1rem;
            border: 1px solid #e5e7eb;
            border-radius: 0.8rem;
            background: #fafafa;
        }
        .small-muted {
            color: #6b7280;
            font-size: 0.82rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">AERIS — Machine Failure Prediction</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">A small Streamlit demo for the machine-failure model trained on AI4I 2020.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="status-pill">AI4I 2020 BENCHMARK</span>',
    unsafe_allow_html=True,
)
st.caption(
    "Seed-42 primary evaluation · PR-AUC is the primary metric · "
    "0.50 is the current demonstration threshold"
)

with st.sidebar:
    st.markdown(
        '<div class="section-label">Observation input</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Enter one machine observation. AERIS derives two deterministic engineering "
        "features before scoring the operating state."
    )

    preset = st.selectbox(
        "Scenario",
        ["Custom"] + list(DEMO_PRESETS),
        help="Two presets are held-out benchmark examples; the stress-test presets are illustrative operating conditions.",
    )

    preset_values = DEMO_PRESETS.get(preset, {})

    machine_type = st.selectbox(
        "Product type",
        ["L", "M", "H"],
        index=["L", "M", "H"].index(preset_values.get("type", "M")),
        disabled=preset != "Custom",
        help="AI4I product-type category.",
    )
    air_temp = st.number_input(
        "Air temperature [K]",
        min_value=295.3,
        max_value=304.5,
        value=float(preset_values.get("air_temp_k", 298.0)),
        step=0.1,
        disabled=preset != "Custom",
    )
    process_temp = st.number_input(
        "Process temperature [K]",
        min_value=305.7,
        max_value=313.8,
        value=float(preset_values.get("process_temp_k", 308.0)),
        step=0.1,
        disabled=preset != "Custom",
    )
    rpm = st.number_input(
        "Rotational speed [rpm]",
        min_value=1168,
        max_value=2886,
        value=int(preset_values.get("rot_speed_rpm", 1500)),
        step=1,
        disabled=preset != "Custom",
    )
    torque = st.number_input(
        "Torque [Nm]",
        min_value=3.8,
        max_value=76.6,
        value=float(preset_values.get("torque_nm", 40.0)),
        step=0.1,
        disabled=preset != "Custom",
    )
    tool_wear = st.number_input(
        "Tool wear [min]",
        min_value=0,
        max_value=253,
        value=int(preset_values.get("tool_wear_min", 100)),
        step=1,
        disabled=preset != "Custom",
    )

    st.divider()
    st.markdown("**Input contract**")
    st.caption(
        "Every input is constrained to the observed AI4I benchmark domain. "
        "This console does not extrapolate beyond those ranges."
    )

raw_row = pd.DataFrame(
    [
        {
            "type": machine_type,
            "air_temp_k": air_temp,
            "process_temp_k": process_temp,
            "rot_speed_rpm": rpm,
            "torque_nm": torque,
            "tool_wear_min": tool_wear,
        }
    ]
)

# Use the same feature engineering as the training code.
app_row = add_engineered_features(raw_row)[MODEL_FEATURES]

with st.spinner("Preparing AERIS model bundle..."):
    try:
        risk_model, explainer_pre, explain_model, mode_models = train_models()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()

risk = float(risk_model.predict_proba(app_row)[0, 1])
label, state_note = risk_state(risk)

temp_delta = float(app_row["temp_delta_k"].iloc[0])
mechanical_power = float(app_row["mechanical_power_kw"].iloc[0])

st.subheader("Prediction")

d1, d2, d3, d4 = st.columns(4)
d1.metric("Failure risk", f"{risk * 100:.1f}%")
d2.metric("Model state", label)
d3.metric("Alert threshold", f"{RISK_THRESHOLD:.2f}")
d4.metric("Input domain", "Within range")

st.progress(min(max(risk, 0.0), 1.0))
st.caption(f"{state_note} · {review_message(risk)}")

if risk >= RISK_THRESHOLD:
    st.error(
        "Threshold crossed. This observation should be treated as an engineering "
        "review candidate, not as a confirmed diagnosis."
    )
elif risk >= SCREENING_THRESHOLD:
    st.warning(
        "Elevated model risk. This is a screening signal; inspect operating context "
        "before making a maintenance decision."
    )
else:
    st.success(
        "Below the current alert threshold. This does not guarantee healthy operation."
    )

st.subheader("Input values")

snapshot = pd.DataFrame(
    [
        ["Product type", machine_type, "—"],
        ["Air temperature", air_temp, "K"],
        ["Process temperature", process_temp, "K"],
        ["Rotational speed", rpm, "rpm"],
        ["Torque", torque, "Nm"],
        ["Tool wear", tool_wear, "min"],
        ["Temperature delta", temp_delta, "K"],
        ["Mechanical power", mechanical_power, "kW"],
    ],
    columns=["Signal", "Value", "Unit"],
)
st.dataframe(
    snapshot.style.format({"Value": lambda x: f"{x:.2f}" if isinstance(x, float) else x}),
    use_container_width=True,
    hide_index=True,
)

left, right = st.columns([1.5, 1])

with left:
    st.subheader("Why the model predicted this")
    explanation = local_shap(
        explainer_pre,
        explain_model,
        app_row,
    ).head(5)

    st.bar_chart(
        explanation.set_index("Feature")["SHAP value"],
        height=290,
    )

    explanation_view = explanation[["Feature", "SHAP value", "Direction"]].copy()
    explanation_view["SHAP value"] = explanation_view["SHAP value"].map(
        lambda value: f"{value:+.3f}"
    )
    st.dataframe(
        explanation_view,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "SHAP explains the underlying tree model. It shows what moved the model "
        "toward or away from failure; it does not establish physical root cause."
    )

with right:
    st.subheader("Failure-mode experiments")

    mode_rows = []
    for mode, model in mode_models.items():
        score = float(model.predict_proba(app_row)[0, 1])
        mode_rows.append({"Mode": mode.upper(), "Model score": score})

    mode_frame = pd.DataFrame(mode_rows)
    st.dataframe(
        mode_frame.style.format({"Model score": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "HDF, PWF and OSF are separate benchmark attribution signals. Source labels "
        "can overlap, so these scores are not unique physical diagnoses."
    )

    st.markdown("**Notes**")
    st.info(
        f"The model score is {risk:.1%}. The demonstration alert threshold is "
        f"{RISK_THRESHOLD:.2f}. Any operational policy would need its own cost-based "
        "threshold and validation on real fleet data."
    )

st.divider()

with st.expander("Engineering-derived signals"):
    st.markdown(
        """
        AERIS adds two deterministic features before prediction:

        **Temperature delta** = process temperature − air temperature

        **Mechanical power** = torque × rotational speed / 9549.2966

        Both are calculated only from observed operating inputs. They do not use
        machine-failure labels, failure-mode flags, UDI or Product ID.
        """
    )

with st.expander("Model results"):
    q1, q2, q3, q4, q5 = st.columns(5)
    q1.metric("PR-AUC", f"{MODEL_PR_AUC:.3f}")
    q2.metric("Precision", f"{MODEL_PRECISION:.3f}")
    q3.metric("Recall", f"{MODEL_RECALL:.3f}")
    q4.metric("F1 @ 0.50", f"{MODEL_F1:.3f}")
    q5.metric("Brier", f"{MODEL_BRIER:.4f}")

    st.markdown(
        f"""
        **Held-out evaluation:** seed-42 stratified 80/20 split.

        **Bootstrap context:** PR-AUC 95% interval {BOOTSTRAP_PR_AUC}; F1 95% interval {BOOTSTRAP_F1}.

        **Primary limitation:** AI4I 2020 is a synthetic benchmark. These metrics are
        evidence about this benchmark experiment, not a claim of production fleet performance.
        """
    )

with st.expander("Project notes"):
    st.markdown(
        """
        **Prediction inputs:** product type, air/process temperature, rotational speed,
        torque and tool wear, plus two deterministic derived signals.

        **Excluded:** UDI, Product ID and failure-mode target flags to avoid identifier or
        target leakage.

        **Evaluation discipline:** the final seed-42 test partition is reserved for
        evaluation; model selection is performed on the training partition.

        **Future work:** independent industrial time-series validation, C-MAPSS/RUL,
        temporal degradation modelling, counterfactual analysis and deployment/monitoring.
        """
    )

st.caption(
    "AERIS is an educational benchmark prototype. Do not use its score as a standalone "
    "maintenance decision or real-world failure probability."
)
