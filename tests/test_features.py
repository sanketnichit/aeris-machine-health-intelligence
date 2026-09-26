import pandas as pd

from src.features import DERIVED_FEATURES, MODEL_FEATURES, add_engineered_features


def test_engineered_features_are_deterministic():
    df = pd.DataFrame(
        {
            "type": ["L", "M"],
            "air_temp_k": [300.0, 298.0],
            "process_temp_k": [310.0, 307.0],
            "rot_speed_rpm": [1500, 2000],
            "torque_nm": [40.0, 30.0],
            "tool_wear_min": [100, 50],
        }
    )

    out = add_engineered_features(df)

    assert DERIVED_FEATURES[0] in out.columns
    assert DERIVED_FEATURES[1] in out.columns
    assert out.loc[0, "temp_delta_k"] == 10.0
    assert out.loc[1, "temp_delta_k"] == 9.0
    assert abs(out.loc[0, "mechanical_power_kw"] - (1500 * 40 / 9549.2966)) < 1e-12
    assert list(MODEL_FEATURES) == [
        "type",
        "air_temp_k",
        "process_temp_k",
        "rot_speed_rpm",
        "torque_nm",
        "tool_wear_min",
        "temp_delta_k",
        "mechanical_power_kw",
    ]
