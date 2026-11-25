"""Research-only fusion of two declared deterministic speed-error budgets.

Intervals describe the same reference speed, relative to the first indication.
Agreement is not evidence of calibration or statistical independence.
"""
import math

from src.measurement_budget import measurement_budget
from src.order_breakpoints import verify_breakpoints


def intersect_measurements(secondary_over_primary, primary_repeatability,
                           primary_bias, secondary_repeatability, secondary_bias):
    if (type(secondary_over_primary) not in (int, float)
            or not math.isfinite(secondary_over_primary)
            or not .5 <= secondary_over_primary <= 1.5):
        raise ValueError("Invalid secondary to primary speed ratio")
    primary = measurement_budget(primary_repeatability, primary_bias)
    secondary = measurement_budget(secondary_repeatability, secondary_bias)
    if primary["scale_interval"] is None or secondary["scale_interval"] is None:
        return {"status": "bias_bound_missing", "intersection": None,
                "anchor_scale": None, "scale_interval": None}
    a, b = primary["scale_interval"]
    c, d = secondary["scale_interval"]
    ratio = secondary_over_primary
    # Outward rounding mitigates ordinary floating point endpoint error;
    # this is not formal interval arithmetic.
    lo = max(math.nextafter(a, -math.inf), math.nextafter(c*ratio, -math.inf))
    hi = min(math.nextafter(b, math.inf), math.nextafter(d*ratio, math.inf))
    if lo > hi:
        return {"status": "measurement_conflict", "intersection": None,
                "anchor_scale": None, "scale_interval": None}
    anchor = lo + (hi-lo)/2
    return {"status": "declared_intersection", "intersection": (lo, hi),
            "anchor_scale": anchor,
            "scale_interval": (min(1., math.nextafter(lo/anchor, -math.inf)),
                               max(1., math.nextafter(hi/anchor, math.inf)))}


def fusion_guard(frequencies, window_powers, primary_centers, secondary_over_primary,
                 primary_repeatability, primary_bias, secondary_repeatability,
                 secondary_bias, tolerance, floor, margin):
    result = intersect_measurements(secondary_over_primary, primary_repeatability,
                                   primary_bias, secondary_repeatability, secondary_bias)
    if result["intersection"] is None:
        return {**result, "suggestion": None, "reason": result["status"],
                "cells_checked": 0}
    if not isinstance(primary_centers, dict):
        raise ValueError("Expected characteristic frequency mapping")
    centers = {k: v*result["anchor_scale"] for k,v in primary_centers.items()}
    verified = verify_breakpoints(frequencies, window_powers, centers,
                                  result["scale_interval"], tolerance, floor, margin)
    return {**result, **verified}
