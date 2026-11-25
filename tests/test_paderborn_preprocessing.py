import numpy as np
import pytest
from src.paderborn_preprocessing import conditional_paths,comparison_summary,effective_orders,linked_axis,MIN_SOURCE,SOURCE_RATE,WINDOW,WINDOWS


def signal():
    t=np.arange(MIN_SOURCE+500)/SOURCE_RATE
    return np.sin(2*np.pi*3000*t),t


def test_uniform_fixture_reproduces_both_paths():
    x,t=signal()
    paths=conditional_paths(x,t)
    assert len(paths["nominal"])==WINDOW*WINDOWS
    np.testing.assert_allclose(paths["nominal"],paths["stored_time"],atol=1e-12)
    assert comparison_summary(paths)["relative_waveform_l2_difference"]<1e-12


def test_large_gap_is_explicit_abstention_for_time_path():
    x,t=signal()
    t[len(t)//2:]+=.001
    result=conditional_paths(x,t)
    assert result["stored_time"] is None and result["reason"]=="stored_time_gap_limit_exceeded"
    assert not comparison_summary(result)["operational_authorization"]


def test_nonmonotone_time_is_rejected():
    x,t=signal()
    t[50]=t[49]
    with pytest.raises(ValueError,match="strictly"):
        conditional_paths(x,t)


def test_irregular_fixture_sensitivity_without_clock_claim():
    x,t=signal()
    t=t+.2/SOURCE_RATE*np.sin(np.arange(len(t))*.1)
    result=comparison_summary(conditional_paths(x,t))
    assert result["relative_waveform_l2_difference"]>0
    assert not result["diagnostic_scoring_performed"] and not result["operational_authorization"]


def test_geometry_orders_match_frozen_twice_ball_convention():
    orders=effective_orders(8,28.55,6.75,0.)
    assert orders["inner"]+orders["outer"]==pytest.approx(8.)
    assert orders["ball"]==pytest.approx(28.55/6.75-6.75/28.55)
    with pytest.raises(ValueError):
        effective_orders(8,28.55,29.,0.)


def test_index_and_raster_must_both_match():
    record={"X":[{"Raster":"fast","Data":np.arange(10)}],
            "Y":[{"Name":"vibration_1","XIndex":1,"Raster":"fast","Data":np.arange(10)}]}
    a,b=linked_axis(record,"vibration_1")
    assert len(a)==len(b)==10
    record["Y"][0]["Raster"]="wrong"
    with pytest.raises(ValueError,match="disagree"):
        linked_axis(record,"vibration_1")
