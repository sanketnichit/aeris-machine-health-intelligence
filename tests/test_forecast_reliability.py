import numpy as np
import pandas as pd
import pytest

from src.forecast_reliability import assess_forecast, selective_metrics
from research.xjtu_reliability_audit import evaluate


def test_missing_calibration_is_not_zero_uncertainty():
    report=assess_forecast(20,20,20,None,observed=10,scale=100)
    assert report["status"]=="review_required"
    assert report["advisory_forecast"] is None
    assert report["lower"] is None
    assert report["reasons"]==["insufficient_calibration"]


def test_multiple_review_reasons_and_valid_forecast():
    report=assess_forecast(100,10,20,80,observed=3,scale=100,width_limit=.5)
    assert set(report["reasons"])=={"insufficient_history","wide_interval","model_disagreement"}
    assert report["advisory_forecast"] is None
    ok=assess_forecast(20,25,22,5,observed=5,scale=100)
    assert ok["advisory_forecast"]==22
    assert ok["lower"]==17 and ok["upper"]==27


def test_selective_metrics_empty_acceptance():
    report=selective_metrics([3,4],[5,7],[False,False])
    assert report["retained_mae"] is None
    assert report["abstained_mae"]==2.5
    with pytest.raises(ValueError):
        selective_metrics([1],[2],[1])


def test_bearing_calibration_and_small_sample_limit():
    data=pd.DataFrame([{"bearing":f"Bearing{c}_{b}","condition":c,"age":a,
                        "horizontal_rms":float(1+a/10),"vertical_rms":float(b)}
                       for c in range(1,4) for b in range(1,6) for a in range(1,13)])
    report=evaluate(data,landmarks=(5,10,12))
    for row in report["predictions"]:
        assert row["bearing"] not in row["fit_bearings"]
        assert row["bearing"] not in row["calibration_bearings"]
        assert not set(row["fit_bearings"]) & set(row["calibration_bearings"])
        assert row["radii"]["0.1"] is None
        assert row["radii"]["0.2"] is not None
        if row["split"]=="condition":
            assert all(b[7]!=row["bearing"][7] for b in row["fit_bearings"]+row["calibration_bearings"])
    for split in ("bearing","condition"):
        assert set(report["summary"][split])=={"5","10"}
        assert report["summary"][split]["5"]["endpoints"]==15
        assert report["summary"][split]["5"]["finite_90_percent_intervals"]==0
