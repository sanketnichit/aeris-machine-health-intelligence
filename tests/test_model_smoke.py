import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


FEATURES = [
    "type",
    "air_temp_k",
    "process_temp_k",
    "rot_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]


def build_model() -> CalibratedClassifierCV:
    pre = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ["type"],
            ),
            ("numeric", "passthrough", FEATURES[1:]),
        ]
    )
    base = Pipeline(
        [
            ("preprocessor", pre),
            (
                "model",
                HistGradientBoostingClassifier(
                    max_iter=30,
                    learning_rate=0.08,
                    max_leaf_nodes=7,
                    l2_regularization=1.0,
                    random_state=42,
                ),
            ),
        ]
    )
    return CalibratedClassifierCV(base, method="sigmoid", cv=3)


def test_calibrated_pipeline_smoke():
    rows = []
    for i in range(30):
        rows.append(
            {
                "type": ["L", "M", "H"][i % 3],
                "air_temp_k": 298.0 + (i % 5) * 0.1,
                "process_temp_k": 308.0 + (i % 4) * 0.2,
                "rot_speed_rpm": 1400 + i * 8,
                "torque_nm": 25 + i * 0.8,
                "tool_wear_min": i * 5,
            }
        )

    X = pd.DataFrame(rows)
    y = pd.Series([0, 1] * 15, name="machine_failure")

    model = build_model()
    model.fit(X, y)

    probabilities = model.predict_proba(X)
    assert probabilities.shape == (30, 2)
    assert ((probabilities >= 0.0) & (probabilities <= 1.0)).all()
