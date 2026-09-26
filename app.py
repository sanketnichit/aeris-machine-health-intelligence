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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "ai4i2020.csv"

FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
MODES = ["HDF", "PWF", "OSF"]
RISK_THRESHOLD = 0.50
MODEL_PR_AUC = 0.849
MODEL_F1 = 0.820


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["Type"],
            ),
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "AI4I dataset not found. Place ai4i2020.csv in data/."
        )
    return pd.read_csv(DATA_PATH)


@st.cache_resource
def train_models():
    df = load_data()
    X = df[FEATURES]
    y = df["Machine failure"]

    X_train, _, y_train, _ = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    base = Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            (
                "model",
                HistGradientBoostingClassifier(
                    max_iter=300,
                    learning_rate=0.06,
                    max_leaf_nodes=31,
                    l2_regularization=1.0,
                    random_state=42,
                ),
            ),
        ]
    )

    risk_model = CalibratedClassifierCV(
        base,
        method="sigmoid",
        cv=5,
        n_jobs=-1,
    )
    risk_model.fit(X_train, y_train)

    explainer_pre = build_preprocessor()
    X_train_t = explainer_pre.fit_transform(X_train, y_train)

    explain_model = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.06,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    )
    explain_model.fit(X_train_t, y_train)

    mode_models = {}
    for mode in MODES:
        mode_model = Pipeline(
            [
                ("preprocessor", build_preprocessor()),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=250,
                        learning_rate=0.06,
                        max_leaf_nodes=31,
                        l2_regularization=1.0,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        mode_model.fit(X_train, df.loc[X_train.index, mode])
        mode_models[mode] = mode_model

    return risk_model, explainer_pre, explain_model, mode_models


def risk_state(risk: float) -> tuple[str, str]:
    if risk >= 0.50:
        return "HIGH RISK", "Threshold crossed"
    if risk >= 0.20:
        return "ELEVATED", "Screening signal"
    return "LOWER", "Below threshold"


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
        if name.startswith("categorical__Type_"):
            type_total += float(value)
        else:
            rows.append((name.replace("numeric__", ""), float(value)))

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
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.10em;
            color: #6b7280; font-weight: 700;
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
    st.caption("Enter one machine observation to inspect the model response.")

    machine_type = st.selectbox(
        "Product type",
        ["L", "M", "H"],
        index=1,
        help="AI4I product-type category.",
    )
    air_temp = st.number_input(
        "Air temperature [K]",
        min_value=295.0,
        max_value=305.0,
        value=298.0,
        step=0.1,
    )
    process_temp = st.number_input(
        "Process temperature [K]",
        min_value=300.0,
        max_value=315.0,
        value=308.0,
        step=0.1,
    )
    rpm = st.number_input(
        "Rotational speed [rpm]",
        min_value=800,
        max_value=3000,
        value=1500,
        step=1,
    )
    torque = st.number_input(
        "Torque [Nm]",
        min_value=1.0,
        max_value=80.0,
        value=40.0,
        step=0.1,
    )
    tool_wear = st.number_input(
        "Tool wear [min]",
        min_value=0,
        max_value=300,
        value=100,
        step=1,
    )

    st.divider()
    st.caption(
        "HistGradientBoosting + sigmoid calibration · Primary metric: PR-AUC"
    )

row = pd.DataFrame(
    [
        {
            "Type": machine_type,
            "Air temperature [K]": air_temp,
            "Process temperature [K]": process_temp,
            "Rotational speed [rpm]": rpm,
            "Torque [Nm]": torque,
            "Tool wear [min]": tool_wear,
        }
    ]
)

try:
    risk_model, explainer_pre, explain_model, mode_models = train_models()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

risk = float(risk_model.predict_proba(row)[0, 1])
label, _ = risk_state(risk)
temp_delta = process_temp - air_temp

k1, k2, k3, k4 = st.columns(4)
k1.metric("Failure risk", f"{risk * 100:.1f}%")
k2.metric("Current state", label)
k3.metric("Temp delta", f"{temp_delta:.1f} K")
k4.metric("Alert threshold", f"{RISK_THRESHOLD * 100:.0f}%")

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
    explanation = local_shap(explainer_pre, explain_model, row).head(5)
    st.bar_chart(
        explanation.set_index("Feature")["SHAP value"],
        height=300,
    )
    st.caption(
        "Positive values push the underlying tree model toward failure; negative values "
        "push it toward non-failure. SHAP explains model behaviour, not physical causality."
    )

with right:
    st.subheader("Failure-mode attribution")

    mode_rows = []
    for mode, model in mode_models.items():
        score = float(model.predict_proba(row)[0, 1])
        mode_rows.append({"Mode": mode, "Model score": score})

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

with st.expander("Model quality & scope"):
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("PR-AUC", f"{MODEL_PR_AUC:.3f}")
    q2.metric("F1 @ 0.50", f"{MODEL_F1:.3f}")
    q3.metric("Dataset", "AI4I 2020")
    q4.metric("Failures", "3.39%")

    st.markdown(
        """
        **Important context**

        AERIS uses the synthetic AI4I 2020 benchmark as a controlled predictive-maintenance
        experiment. The risk score is calibrated for this benchmark and should not be treated
        as a production maintenance probability or as evidence about any specific real-world fleet.
        """
    )

with st.expander("Engineering notes"):
    st.markdown(
        """
        **Feature set:** product type, air/process temperature, rotational speed,
        torque and tool wear.

        **Excluded from prediction:** UDI, Product ID and failure-mode target flags,
        because they would introduce identifier/label leakage.

        **Primary evaluation:** PR-AUC, with precision, recall and F1 reported because
        failures are rare.

        **Future extensions:** C-MAPSS/RUL, temporal degradation modelling,
        counterfactual analysis and real industrial time-series validation.
        """
    )
