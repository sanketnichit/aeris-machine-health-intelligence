"""Research-only composition of externally supplied relative speed-error bounds.

Both components must be absolute bounds relative to the same reference speed.
No calibration is inferred from spectra. Missing bias information fails closed.
"""
import math

from src.order_breakpoints import verify_breakpoints


def _bound(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= .25:
        raise ValueError("Expected finite nonnegative relative error bound <= 0.25")
    return float(value)


def measurement_budget(repeatability_bound, bias_bound):
    repeatability = _bound(repeatability_bound)
    if bias_bound is None:
        return {"status": "bias_bound_missing", "total_relative_bound": None,
                "scale_interval": None}
    bias = _bound(bias_bound)
    width = math.fsum((repeatability, bias))
    # The existing frequency-scale verifier supports upper scale <= 1.5.
    if width > 1/3:
        raise ValueError("Combined bound exceeds supported scale domain")
    return {"status": "declared_bounds_composed", "total_relative_bound": width,
            "scale_interval": (1/(1+width), 1/(1-width))}


def calibration_guard(frequencies, window_powers, centers, repeatability_bound,
                      bias_bound, tolerance, floor, margin):
    budget = measurement_budget(repeatability_bound, bias_bound)
    if budget["scale_interval"] is None:
        return {**budget, "suggestion": None, "reason": "bias_bound_missing",
                "cells_checked": 0}
    result = verify_breakpoints(frequencies, window_powers, centers,
                                budget["scale_interval"], tolerance, floor, margin)
    return {**budget, **result}
