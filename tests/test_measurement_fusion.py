import pytest
import numpy as np

from src.measurement_fusion import intersect_measurements, fusion_guard


def test_compatible_intersection_contains_reference():
    # Primary reads 5% high, secondary is reference-aligned.
    out = intersect_measurements(1/1.05, .001, .05, .001, .004)
    assert out["status"] == "declared_intersection"
    lo, hi = out["intersection"]
    assert lo <= 1/1.05 <= hi
    assert hi-lo < .011
    assert out["scale_interval"][0] <= 1 <= out["scale_interval"][1]


def test_conflict_fails_closed():
    out = fusion_guard(None,None,None,1.05,.001,0.,.001,0.,1.,.1,.8)
    assert out["suggestion"] is None
    assert out["reason"] == "measurement_conflict"


@pytest.mark.parametrize("primary,secondary", [(None,.01),(.01,None)])
def test_unknown_bias_fails_closed(primary,secondary):
    out = fusion_guard(None,None,None,1.,.001,primary,.001,secondary,1.,.1,.8)
    assert out["suggestion"] is None
    assert out["reason"] == "bias_bound_missing"


def test_shared_false_bias_can_agree():
    out = intersect_measurements(1.,.001,.01,.001,.004)
    assert out["status"] == "declared_intersection"
    lo, hi = out["intersection"]
    assert not lo <= 1/1.05 <= hi


def test_recentered_interval_handles_non_nominal_reference():
    f = np.arange(151,dtype=float)
    p = np.zeros_like(f)
    p[9:12] = 1
    centers = {"outer":10.5,"inner":42.,"ball":47.25}
    out = fusion_guard(f,[p],centers,1/1.05,.001,.05,.001,.004,1.1,.5,.8)
    assert out["suggestion"] == "outer"
    assert out["intersection"][1] < 1


@pytest.mark.parametrize("ratio", [0, True, float("inf"), 2])
def test_invalid_ratio(ratio):
    with pytest.raises(ValueError):
        intersect_measurements(ratio,.001,.01,.001,.01)
