import numpy as np
import pandas as pd
import pytest

from src.physics_rules import rule_predictions


def row(**changes):
    base = dict(type="L", air_temp_k=300., process_temp_k=310.,
                rot_speed_rpm=1500., torque_nm=40., tool_wear_min=100.)
    return pd.DataFrame([base | changes], index=[17])


def test_nominal_and_index():
    result = rule_predictions(row())
    assert list(result.index) == [17]
    assert not result.any(axis=None)


def test_heat_requires_both_conditions():
    assert rule_predictions(row(process_temp_k=308., rot_speed_rpm=1300.)).hdf.iloc[0]
    assert not rule_predictions(row(process_temp_k=308., rot_speed_rpm=1380.)).hdf.iloc[0]
    assert not rule_predictions(row(rot_speed_rpm=1300.)).hdf.iloc[0]


def test_power_low_and_high():
    assert rule_predictions(row(torque_nm=10.)).pwf.iloc[0]
    assert rule_predictions(row(torque_nm=100.)).pwf.iloc[0]


@pytest.mark.parametrize("kind,limit", [("L",11000),("M",12000),("H",13000)])
def test_overstrain_strict_boundary(kind, limit):
    assert not rule_predictions(row(type=kind, torque_nm=50., tool_wear_min=limit/50)).osf.iloc[0]
    result = rule_predictions(row(type=kind, torque_nm=50., tool_wear_min=limit/50+1))
    assert result.osf.iloc[0] and result.rule_failure.iloc[0]


def test_target_columns_are_ignored():
    sample = row()
    assert rule_predictions(sample).equals(rule_predictions(sample.assign(machine_failure=1, hdf=1)))


@pytest.mark.parametrize("changes", [dict(type="X"),dict(torque_nm=np.nan),dict(rot_speed_rpm=np.inf)])
def test_invalid_inputs(changes):
    with pytest.raises(ValueError):
        rule_predictions(row(**changes))
