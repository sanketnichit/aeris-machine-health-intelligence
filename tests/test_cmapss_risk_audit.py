import numpy as np
import pytest

from research.cmapss_risk_audit import age_blend, ordered_bounds, cqr_radius, risk_metrics


def test_blend_boundaries():
    np.testing.assert_allclose(age_blend([1,50,100,150,200], [80]*5, [20]*5),
                               [80,80,50,20,20])


def test_crossed_quantiles_are_ordered_and_nonnegative():
    lo, hi = ordered_bounds([8,-3,5],[2,4,-1])
    np.testing.assert_array_equal(lo,[2,0,0])
    np.testing.assert_array_equal(hi,[8,4,5])


def test_cqr_finite_sample_and_nonnegative():
    assert cqr_radius(np.arange(9),np.zeros(9),np.zeros(9)) == 8.
    assert cqr_radius(np.ones(9),np.zeros(9),np.ones(9)*2) == 0.
    with pytest.raises(ValueError):
        cqr_radius([1,2],[0,0],[3,3])


def test_risk_metrics_preserve_signed_error():
    report = risk_metrics([50,50,50],[75,25,50])
    assert report["mean_signed_error"] == 0.
    assert report["overprediction_gt20_fraction"] == pytest.approx(1/3)
    assert report["underprediction_gt20_fraction"] == pytest.approx(1/3)
    with pytest.raises(ValueError):
        risk_metrics([50],[-1])
