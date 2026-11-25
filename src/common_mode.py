"""Common-mode speed error model, with explicit conditional assumptions.

indicated_i = reference * (1 + common + individual_i).
All bounds are deterministic relative errors, not standard deviations.
"""
import math

from src.measurement_budget import _bound, measurement_budget
from src.measurement_fusion import intersect_measurements
from src.order_breakpoints import verify_breakpoints


def common_mode_intersection(ratio, primary_bound, secondary_bound, common_bound):
    if type(ratio) not in (int, float) or not math.isfinite(ratio) or not .5 <= ratio <= 1.5:
        raise ValueError("Invalid secondary/primary ratio")
    a, b = _bound(primary_bound), _bound(secondary_bound)
    if common_bound is None:
        return {"status": "common_mode_bound_missing", "intersection": None,
                "expanded_intersection": None, "anchor_scale": None, "scale_interval": None}
    c = _bound(common_bound)
    # First impose per-channel total bounds. At zero shared error the old
    # intersection is already the exact real-arithmetic feasible region.
    expanded = intersect_measurements(ratio, a, c, b, c)
    if expanded["intersection"] is None:
        return {**expanded, "expanded_intersection": None}
    lo, hi = expanded["intersection"]
    if c > 0:
        # Eliminate the latent common error: the two independent-error
        # intervals for common must overlap. In reference/primary units t,
        # |ratio - 1| <= (a+b)*t.
        slack = 64 * math.ulp(max(1., abs(ratio)))
        difference = max(0., abs(ratio-1.)-slack)
        total = math.nextafter(a+b, math.inf)
        if difference > 0:
            if total == 0 or difference > total*hi + slack:
                return {"status": "common_mode_conflict", "intersection": None,
                        "expanded_intersection": expanded["intersection"],
                        "anchor_scale": None, "scale_interval": None}
            lo = max(lo, math.nextafter(difference/total, -math.inf))
        if lo > hi:
            return {"status": "common_mode_conflict", "intersection": None,
                    "expanded_intersection": expanded["intersection"],
                    "anchor_scale": None, "scale_interval": None}
    anchor = lo+(hi-lo)/2
    return {"status": "conditional_common_mode_intersection",
            "expanded_intersection": expanded["intersection"],
            "intersection": (lo, hi), "anchor_scale": anchor,
            "scale_interval": (min(1., math.nextafter(lo/anchor, -math.inf)),
                               max(1., math.nextafter(hi/anchor, math.inf)))}


def common_mode_guard(frequencies, window_powers, primary_centers, ratio,
                      primary_bound, secondary_bound, common_bound, tolerance, floor, margin):
    result = common_mode_intersection(ratio, primary_bound, secondary_bound, common_bound)
    if result["intersection"] is None:
        return {**result, "suggestion": None, "reason": result["status"], "cells_checked": 0}
    if not isinstance(primary_centers, dict):
        raise ValueError("Expected characteristic frequency mapping")
    centers = {k:v*result["anchor_scale"] for k,v in primary_centers.items()}
    check = verify_breakpoints(frequencies, window_powers, centers, result["scale_interval"],
                               tolerance, floor, margin)
    return {**result, **check}
