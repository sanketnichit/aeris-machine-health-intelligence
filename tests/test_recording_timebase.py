import numpy as np
import pytest
from src.recording_timebase import inspect_record,vector_summary


def fixture():
    return {"X":[{"Name":"time","Raster":"fast","Unit":"s","Data":np.arange(10)/64000},
                 {"Name":"time","Raster":"slow","Unit":"s","Data":np.arange(3)/100}],
            "Y":[{"Name":"vibration_1","Raster":"fast","Data":np.arange(10)},
                 {"Name":"speed","Raster":"slow","Unit":"rpm","Data":np.array([1500.,1499.,1501.])}]}


def test_separate_time_axes_no_calibration_claim():
    out=inspect_record(fixture())
    assert out["channels"][0]["raster_and_count_candidates"]==[0]
    assert out["channels"][1]["raster_and_count_candidates"]==[1]
    assert out["time_axes"][0]["vector"]["median_step"]==pytest.approx(1/64000)
    assert not out["timing_association_verified"] and not out["diagnostic_scoring_performed"]
    assert "median" not in out["channels"][0]["vector"]


def test_count_match_is_not_raster_match():
    f=fixture()
    f["Y"][0]["Raster"]="unknown"
    out=inspect_record(f)
    assert out["channels"][0]["count_only_candidates"]==[0]
    assert out["channels"][0]["raster_and_count_candidates"]==[]


def test_irregular_clock_and_duplicate_time():
    out=vector_summary([0.,1.,1.,3.],True)
    assert not out["strictly_increasing"] and out["max_relative_step_deviation"]>0


def test_invalid_time_vector_not_inferred():
    assert vector_summary([0.,float("nan")],True)["status"]=="nonfinite"
    assert vector_summary([[1.,2.]],True)["status"]=="not_real_vector"


def test_missing_speed_refused():
    f=fixture()
    f["Y"].pop()
    with pytest.raises(ValueError,match="unique"):
        inspect_record(f)
