import pandas as pd

from src.console_models import train_console_models


def test_console_model_bundle_runs(tmp_path):
    rows = []
    for i in range(120):
        failure = int(i % 5 == 0 or i % 11 == 0)
        rows.append(
            {
                "UDI": i + 1,
                "Product ID": f"LTEST{i:04d}",
                "Type": ["L", "M", "H"][i % 3],
                "Air temperature [K]": 296.0 + (i % 20) * 0.2,
                "Process temperature [K]": 306.5 + (i % 20) * 0.2,
                "Rotational speed [rpm]": 1200 + (i % 40) * 20 + failure * 180,
                "Torque [Nm]": 20.0 + (i % 25) * 1.2 + failure * 8,
                "Tool wear [min]": i % 120,
                "Machine failure": failure,
                "TWF": int(failure and i % 10 == 0),
                "HDF": int(failure and i % 3 == 0),
                "PWF": int(failure and i % 4 == 0),
                "OSF": int(failure and i % 5 == 0),
                "RNF": 0,
            }
        )

    path = tmp_path / "ai4i2020.csv"
    pd.DataFrame(rows).to_csv(path, index=False)

    risk_model, preprocessor, explain_model, mode_models = train_console_models(path)

    sample = pd.DataFrame(
        [
            {
                "type": "L",
                "air_temp_k": 298.0,
                "process_temp_k": 308.0,
                "rot_speed_rpm": 1500,
                "torque_nm": 40.0,
                "tool_wear_min": 100,
                "temp_delta_k": 10.0,
                "mechanical_power_kw": 1500 * 40 / 9549.2966,
            }
        ]
    )

    risk = risk_model.predict_proba(sample)[0, 1]
    transformed = preprocessor.transform(sample)
    explanation = explain_model.predict_proba(transformed)[0, 1]

    assert 0.0 <= risk <= 1.0
    assert 0.0 <= explanation <= 1.0
    assert set(mode_models) == {"hdf", "pwf", "osf"}

    for model in mode_models.values():
        score = model.predict_proba(sample)[0, 1]
        assert 0.0 <= score <= 1.0
