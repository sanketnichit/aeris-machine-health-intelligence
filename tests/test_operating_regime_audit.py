import pandas as pd

from research.operating_regime_audit import regimes


def test_regime_boundaries_and_label_independence():
    frame = pd.DataFrame({
        "rot_speed_rpm": [1379, 1380, 1500],
        "torque_nm": [49, 50, 51],
        "tool_wear_min": [199, 200, 201],
        "temp_delta_k": [8.5, 8.6, 9.0],
        "type": ["L", "M", "H"],
        "machine_failure": [0, 1, 0],
    }, index=[4, 8, 12])
    expected = {
        "low_speed": [True, False, False],
        "high_torque": [False, True, True],
        "high_wear": [False, True, True],
        "low_temperature_delta": [True, False, False],
        "type_L": [True, False, False],
        "type_M": [False, True, False],
        "type_H": [False, False, True],
    }
    masks = regimes(frame)
    reversed_labels = regimes(frame.assign(machine_failure=1-frame.machine_failure))
    assert set(masks) == set(expected)
    for name, mask in masks.items():
        assert mask.index.equals(frame.index)
        assert mask.tolist() == expected[name]
        assert mask.equals(reversed_labels[name])
        assert not set(frame.loc[mask].index) & set(frame.loc[~mask].index)
