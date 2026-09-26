"""
AERIS - Machine Health Intelligence
Focused Streamlit engineering console.

Run:
    streamlit run app.py
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


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                ["Type"],
            ),
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


@st.cache_resource
def train_models():
    df = load_data()
    X = df[FEATURES]
    y = df["Machine failure"]

    X_train, X_test, y_train, y_test = train_test_split(
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

    # Separate tree model for SHAP explanations.
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
        mode_target = mode
        m = Pipeline(
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
        m.fit(X_train, df.loc[X_train.index, mode_target])
        mode_models[mode] = m

    return risk_model, explainer_pre, explain_model, mode_models


def risk_label(risk: float) -> tuple[str, str]:
    if risk >= 0.5:
        return "HIGH RISK", "The model predicts the positive failure class."
    if risk >= 0.2:
        return "ELEVATED", "The model sees a meaningful increase in failure risk."
    return "LOWER RISK", "The model does not cross the current failure threshold."


def local_shap(
    preprocessor: ColumnTransformer,
    tree_model: HistGradientBoostingClassifier,
    row: pd.DataFrame,
) -> pd.DataFrame:
    transformed = preprocessor.transform(row)
    explainer = shap.TreeExplainer(tree_model)
    values = explainer.shap_values(transformed)

    names = preprocessor.get_feature_names_out()
    values = np.asarray(values).reshape(-1)

    rows: list[tuple[str, float]] = []
    type_total = 0.0
    for name, value in zip(names, values):
        if name.startswith("categorical__Type_"):
            type_total += float(value)
        else:
            clean = name.replace("numeric__", "")
            rows.append((clean, float(value)))

    rows.append(("Machine type", type_total))
    return (
        pd.DataFrame(rows, columns=["Feature", "SHAP value"])
        .assign(abs_value=lambda d: d["SHAP value"].abs())
        .sort_values("abs_value", ascending=False)
    )


st.set_page_config(
    page_title="AERIS — Machine Health Intelligence",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ AERIS — Machine Health Intelligence")
st.caption(
    "Explainable machine-failure detection and risk scoring using the AI4I 2020 benchmark."
)

st.info(
    "This is a portfolio/research prototype using public benchmark data. "
    "The score is a calibrated model estimate, not a production maintenance decision."
)

risk_model, explainer_pre, explain_model, mode_models = train_models()

with st.sidebar:
    st.header("Machine operating state")
    machine_type = st.selectbox("Machine type", ["L", "M", "H"])
    air_temp = st.number_input("Air temperature [K]", 295.0, 305.0, 298.0, 0.1)
    process_temp = st.number_input(
        "Process temperature [K]",
        300.0,
        315.0,
        308.0,
        0.1,
    )
    rpm = st.number_input("Rotational speed [rpm]", 800, 3000, 1500, 1)
    torque = st.number_input("Torque [Nm]", 1.0, 80.0, 40.0, 0.1)
    tool_wear = st.number_input("Tool wear [min]", 0, 300, 100, 1)

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

risk = float(risk_model.predict_proba(row)[0, 1])
label, detail = risk_label(risk)

c1, c2, c3 = st.columns(3)
c1.metric("Failure risk", f"{risk * 100:.1f}%")
c2.metric("Predicted state", label)
c3.metric("Temperature delta", f"{process_temp - air_temp:.1f} K")

st.caption(detail)

left, right = st.columns(2)

with left:
    st.subheader("Why did the model score this observation this way?")
    explanation = local_shap(explainer_pre, explain_model, row).head(6)
    chart = explanation.set_index("Feature")["SHAP value"]
    st.bar_chart(chart)
    st.caption(
        "Positive SHAP values push the underlying tree model toward failure; "
        "negative values push it toward non-failure. SHAP explains model behaviour, "
        "not physical causality."
    )

with right:
    st.subheader("Failure-mode attribution")
    mode_values = {}
    for mode, model in mode_models.items():
        mode_values[mode] = float(model.predict_proba(row)[0, 1])

    mode_frame = pd.DataFrame(
        {"Estimated mode likelihood": mode_values}
    )
    st.bar_chart(mode_frame)

    st.caption(
        "HDF, PWF and OSF are the modes promoted into v1. The underlying dataset "
        "permits overlapping mode labels, so this panel reports separate scores "
        "rather than claiming one unique root cause."
    )

st.divider()
st.subheader("AERIS interpretation")

if risk >= 0.5:
    st.error(
        "⚠️ The model crosses the current failure decision threshold. "
        "Inspect the contributing features before treating this as an engineering alert."
    )
elif risk >= 0.2:
    st.warning(
        "🟡 The model sees elevated risk. This is a screening signal, not a diagnosis."
    )
else:
    st.success(
        "🟢 The model does not cross the current failure threshold for this operating state."
    )
