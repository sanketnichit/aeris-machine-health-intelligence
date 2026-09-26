"""
AERIS - Machine Health Intelligence
Focused Streamlit engineering console.
Run: streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import shap
import streamlit as st
from sklearn.model_selection import train_test_split

from src.features import MODEL_FEATURES, add_engineered_features
from src.console_models import train_console_models


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "ai4i2020.csv"

MODES = ["hdf", "pwf", "osf"]
RISK_THRESHOLD = 0.50

# Primary seed-42 held-out evaluation for the current engineered-feature model.
MODEL_PR_AUC = 0.899
MODEL_F1 = 0.880
MODEL_BRIER = 0.0075



def risk_state(risk: float) -> tuple[str, str]:
    if risk >= RISK_THRESHOLD:
        return "HIGH RISK", "Threshold crossed"
    if risk >= 0.20:
        return "ELEVATED", "Screening signal"
    return "LOWER", "Below threshold"


@st.cache_resource
def train_models():
    """Train the UI model bundle using the canonical offline architecture."""
    return train_console_models(DATA_PATH, random_state=42)


@st.cache_resource
def get_shap_explainer(model: HistGradientBoostingClassifier):
    return shap.TreeExplainer(model)


def local_shap(
    preprocessor: ColumnTransformer,
    tree_model: HistGradientBoostingClassifier,
    row: pd.DataFrame,
) -> pd.DataFrame:
    transformed = preprocessor.transform(row)
    explainer = get_shap_explainer(tree_model)
    values = np.asarray(explainer.shap_values(transformed)).reshape(-1)
    names = preprocessor.get_feature_names_out()

    rows: list[tuple[str, float]] = []
    type_total = 0.0

    for name, value in zip(names, values):
        if name.startswith("categorical__type_"):
            type_total += float(value)
        else:
            rows.append(
                (
                    name.replace("numeric__", ""),
                    float(value),
                )
            )

    rows.append(("Machine type", type_total))

    return (
        pd.DataFrame(rows, columns=["Feature", "SHAP value"])
        .assign(abs_value=lambda d: d["SHAP value"].abs())
        .sort_values("abs_value", ascending=False)
    )


st.set_page_config(
    page_title="AERIS | Machine Health Intelligence",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-title { font-size: 2.3rem; font-weight: 750; margin-bottom: 0.15rem; }
        .subtitle { color: #6b7280; font-size: 1rem; margin-bottom: 1.2rem; }
        .section-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: #6b7280;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">⚙️ AERIS — Machine Health Intelligence</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Explainable fault detection and calibrated failure-risk scoring for the AI4I 2020 benchmark.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        '<div class="section-label">Machine operating state</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Enter one machine observation. AERIS derives two engineering features "
        "before scoring the state."
    )

    machine_type = st.selectbox(
        "Product type",
        ["L", "M", "H"],
        index=1,
        help="AI4I product-type category.",
    )
    air_temp = st.number_input(
        "Air temperature [K]",
        min_value=295.3,
        max_value=304.5,
        value=298.0,
        step=0.1,
    )
    process_temp = st.number_input(
        "Process temperature [K]",
        min_value=305.7,
        max_value=313.8,
        value=308.0,
        step=0.1,
    )
    rpm = st.number_input(
        "Rotational speed [rpm]",
        min_value=1168,
        max_value=2886,
        value=1500,
        step=1,
    )
    torque = st.number_input(
        "Torque [Nm]",
        min_value=3.8,
        max_value=76.6,
        value=40.0,
        step=0.1,
    )
    tool_wear = st.number_input(
        "Tool wear [min]",
        min_value=0,
        max_value=253,
        value=100,
        step=1,
    )

    st.divider()
    st.caption(
        "HistGradientBoosting + sigmoid calibration · Primary metric: PR-AUC"
    )
    st.caption(
        "Input limits follow the observed AI4I benchmark ranges to keep the demo "
        "inside the model's validated feature domain."
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

# Use exactly the same deterministic feature engineering as the offline pipeline.
app_row = add_engineered_features(raw_row)[MODEL_FEATURES]

try:
    risk_model, explainer_pre, explain_model, mode_models = train_models()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

risk = float(risk_model.predict_proba(app_row)[0, 1])
label, _ = risk_state(risk)

temp_delta = float(app_row["temp_delta_k"].iloc[0])
mechanical_power = float(app_row["mechanical_power_kw"].iloc[0])

k1, k2, k3, k4 = st.columns(4)
k1.metric("Failure risk", f"{risk * 100:.1f}%")
k2.metric("Current state", label)
k3.metric("Temp delta", f"{temp_delta:.1f} K")
k4.metric("Mechanical power", f"{mechanical_power:.1f} kW")

st.progress(min(max(risk, 0.0), 1.0))

if risk >= RISK_THRESHOLD:
    st.error(
        "⚠️ **Threshold crossed.** The model flags this operating state for further inspection."
    )
elif risk >= 0.20:
    st.warning(
        "🟡 **Elevated model risk.** Treat this as a screening signal, not a diagnosis."
    )
else:
    st.success(
        "🟢 **Below the current threshold.** This does not guarantee the machine is healthy."
    )

left, right = st.columns([1.45, 1])

with left:
    st.subheader("Why did the model score it this way?")
    explanation = local_shap(
        explainer_pre,
        explain_model,
        app_row,
    ).head(5)
    st.bar_chart(
        explanation.set_index("Feature")["SHAP value"],
        height=300,
    )
    st.caption(
        "Positive values push the underlying tree model toward failure; negative "
        "values push it toward non-failure. SHAP explains model behaviour, not "
        "physical causality."
    )

with right:
    st.subheader("Failure-mode attribution")

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
        "HDF, PWF and OSF are separate mode scores. Source labels can overlap, "
        "so AERIS does not claim one unique physical root cause."
    )

st.divider()

with st.expander("Derived engineering features"):
    st.markdown(
        """
        AERIS adds two deterministic features before prediction:

        **Temperature delta** = process temperature − air temperature

        **Mechanical power** = torque × rotational speed / 9549.2966

        These are transformations of observed operating signals; they do not use
        machine-failure labels or failure-mode flags.
        """
    )

with st.expander("Model quality & scope"):
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("PR-AUC", f"{MODEL_PR_AUC:.3f}")
    q2.metric("F1 @ 0.50", f"{MODEL_F1:.3f}")
    q3.metric("Brier", f"{MODEL_BRIER:.4f}")
    q4.metric("Failures", "3.39%")

    st.markdown(
        """
        **Important context**

        AERIS uses the synthetic AI4I 2020 benchmark as a controlled
        predictive-maintenance experiment. The risk score is calibrated for this
        benchmark and should not be treated as a production maintenance probability
        or as evidence about any specific real-world fleet.
        """
    )

with st.expander("Engineering notes"):
    st.markdown(
        """
        **Raw inputs:** product type, air/process temperature, rotational speed,
        torque and tool wear.

        **Derived inputs:** temperature delta and mechanical power.

        **Excluded from prediction:** UDI, Product ID and failure-mode target flags,
        because they would introduce identifier/label leakage.

        **Primary evaluation:** PR-AUC, with precision, recall, F1 and Brier score
        reported because failures are rare.

        **Future extensions:** C-MAPSS/RUL, temporal degradation modelling,
        counterfactual analysis and real industrial time-series validation.
        """
    )
