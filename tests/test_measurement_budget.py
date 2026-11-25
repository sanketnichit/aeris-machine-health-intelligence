import numpy as np
import pytest

from src.measurement_budget import measurement_budget, calibration_guard
from src.order_breakpoints import verify_breakpoints


def test_additive_budget_and_inverse_scale():
    out = measurement_budget(.005, .05)
    assert out["total_relative_bound"] == pytest.approx(.055)
    lo, hi = out["scale_interval"]
    assert lo == pytest.approx(1/1.055)
    assert hi == pytest.approx(1/.945)
    for bias in (-.05, .05):
        for noise in (-.005, .005):
            assert lo-1e-15 <= 1/(1+bias+noise) <= hi+1e-15


def test_missing_calibration_fails_closed_without_spectrum_evaluation():
    out = calibration_guard(None, None, None, .005, None, .1, .5, .8)
    assert out["suggestion"] is None
    assert out["reason"] == "bias_bound_missing"


@pytest.mark.parametrize("repeatability,bias", [(-.01,.01), (.01,-.01), (True,.01),
    (.01,float("nan")), (.2,.2), (.01,"unknown")])
def test_invalid_bounds_rejected(repeatability, bias):
    with pytest.raises(ValueError):
        measurement_budget(repeatability,bias)


def test_zero_bias_reproduces_existing_verifier():
    f = np.arange(151,dtype=float)
    p = np.zeros_like(f)
    p[9:12] = 1
    centers = {"outer":10., "inner":40., "ball":45.}
    w = .01
    out = calibration_guard(f,[p],centers,w,0.,1.1,.5,.8)
    ref = verify_breakpoints(f,[p],centers,(1/(1+w),1/(1-w)),1.1,.5,.8)
    assert all(out[k]==v for k,v in ref.items())


def test_total_bound_does_not_claim_sensor_calibration():
    out = measurement_budget(.001,.05)
    assert out["status"] == "declared_bounds_composed"
    assert "calibrated" not in out
