import numpy as np
import pandas as pd
import pytest

from research.xjtu_signal_gate import vibration_ratio, combine, evaluate


def fixture():
    return pd.DataFrame([
        {"bearing":f"Bearing{c}_{b}","condition":c,"age":a,
         "horizontal_rms":float(1 if a<=5 else a-4),
         "vertical_rms":float(b)}
        for c in range(1,4) for b in range(1,3) for a in range(1,13)
    ])


def test_gate_is_prefix_invariant():
    frame=fixture()
    full=vibration_ratio(frame)
    for age in (1,4,5,8,11):
        prefix=frame.loc[frame.age<=age]
        pd.testing.assert_series_equal(full.loc[prefix.index],vibration_ratio(prefix))
    assert (full.loc[frame.age<=5]==1).all()


def test_switch_boundaries_and_ramp():
    result=combine([100]*5,[20]*5,[1,2,3,4,6])
    np.testing.assert_allclose(result["switch_2x"],[100,20,20,20,20])
    np.testing.assert_allclose(result["switch_4x"],[100,100,100,20,20])
    np.testing.assert_allclose(result["ramp_2x_4x"],[100,100,60,20,20])
    with pytest.raises(ValueError):
        combine([1],[2],[float("nan")])


def test_group_isolation_and_landmark_support():
    report=evaluate(fixture(),landmarks=(5,10,12))
    for row in report["predictions"]:
        assert row["bearing"] not in row["fit_bearings"]
        if row["split"]=="condition":
            assert all(b[7]!=row["bearing"][7] for b in row["fit_bearings"])
    for split in ("bearing","condition"):
        assert report["summary"][split]["stage"]["all"]["learned"]["endpoints"]==24
        assert set(report["summary"][split]["landmark"]["by_point"])=={"5","10"}
