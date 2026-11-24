import numpy as np
import pandas as pd
import pytest

from research.sensor_stress import corrupt, SENSORS


def sample():
    return pd.DataFrame({
        "type": ["L", "H"], "air_temp_k": [300., 301.],
        "process_temp_k": [310., 312.], "rot_speed_rpm": [1500., 1600.],
        "torque_nm": [40., 45.], "tool_wear_min": [100., 200.],
        "machine_failure": [0, 1],
    }, index=[9, 15])


def test_clean_input_and_derived_features():
    frame = sample()
    out = corrupt(frame, dict.fromkeys(SENSORS, 1.))
    assert out.index.equals(frame.index)
    assert "machine_failure" not in out
    np.testing.assert_allclose(out.temp_delta_k, [10., 11.])
    np.testing.assert_allclose(out.mechanical_power_kw, frame.rot_speed_rpm * frame.torque_nm / 9549.2966)


def test_corruption_is_reproducible_and_does_not_mutate_input():
    frame = sample()
    original = frame.copy(deep=True)
    scales = dict.fromkeys(SENSORS, 1.)
    a = corrupt(frame, scales, level=.5, seed=11)
    b = corrupt(frame, scales, level=.5, seed=11)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(frame, original)
    np.testing.assert_allclose(a.temp_delta_k, a.process_temp_k-a.air_temp_k)
    np.testing.assert_allclose(a.mechanical_power_kw, a.rot_speed_rpm*a.torque_nm/9549.2966)


def test_missing_sensor_values_propagate_to_derived_features():
    out = corrupt(sample(), dict.fromkeys(SENSORS, 1.), missing=1.)
    assert out[SENSORS + ["temp_delta_k", "mechanical_power_kw"]].isna().all().all()
    assert out["type"].tolist() == ["L", "H"]


@pytest.mark.parametrize("kwargs", [{"level": -1.}, {"level": np.inf}, {"missing": 1.1}])
def test_invalid_corruption_parameters(kwargs):
    with pytest.raises(ValueError):
        corrupt(sample(), dict.fromkeys(SENSORS, 1.), **kwargs)
