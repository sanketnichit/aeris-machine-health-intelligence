import numpy as np
import pytest

from src.rul_uncertainty import conformal_radius, intervals, interval_metrics


def test_finite_sample_rank():
    assert conformal_radius(np.arange(9), np.zeros(9), .1) == 8
    assert conformal_radius(np.arange(19), np.zeros(19), .1) == 17


def test_insufficient_calibration():
    with pytest.raises(ValueError):
        conformal_radius([1, 2], [1, 2], .1)


def test_intervals_and_coverage():
    lo, hi = intervals([2, 10], 4)
    np.testing.assert_array_equal(lo, [0, 6])
    np.testing.assert_array_equal(hi, [6, 14])
    assert interval_metrics([6, 15], lo, hi) == {
        "coverage": .5, "mean_width": 7., "endpoints": 2}


@pytest.mark.parametrize("pred,radius", [([-1], 1), ([np.nan], 1), ([1], -1)])
def test_invalid_intervals(pred, radius):
    with pytest.raises(ValueError):
        intervals(pred, radius)
