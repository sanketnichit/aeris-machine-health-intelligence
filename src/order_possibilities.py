"""Research-only outer approximation of possible accepted point suggestions.

Membership is not a diagnosis, a probability, or proof of attainability.
The existing fail-closed stable suggestion remains unchanged.
"""
import numpy as np

from src.order_breakpoints import breakpoint_partition
from src.order_uncertainty import ORDERS, interval_fractions, stable_suggestion


def _possible(bounds, floor, margin):
    # Necessary (not sufficient) conditions for an accepted point winner.
    out = set()
    for name in ORDERS:
        upper = bounds[name]["upper"]
        rival = max(bounds[k]["lower"] for k in ORDERS if k != name)
        if (upper >= floor and upper >= rival and
                upper - rival + 1e-12 >= margin * upper):
            out.add(name)
    return out


def possible_suggestions(frequencies, window_powers, centers, interval,
                         tolerance, floor, margin):
    if not isinstance(window_powers, (list, tuple)) or not 1 <= len(window_powers) <= 1000:
        raise ValueError("Expected bounded window list")
    bounds = [interval_fractions(frequencies, p, centers, interval, tolerance)
              for p in window_powers]
    baseline = stable_suggestion(bounds, floor, margin)
    broad = _possible(baseline["median_bounds"], floor, margin)
    f = np.asarray(frequencies, dtype=float)
    p = np.asarray(window_powers, dtype=float)
    totals = p.sum(axis=1)
    cells = breakpoint_partition(f, centers, interval, tolerance)
    if cells is None:
        return {"possible_suggestions": sorted(broad), "global_possible": sorted(broad),
                "reason": "global_fallback_budget", "cells_checked": 0}
    slack = 64*np.finfo(float).eps*max(1., float(f[-1]), 3*max(centers.values())*interval[1])
    union = set()
    for a, b in cells:
        record = {}
        for name, center in centers.items():
            guaranteed = np.zeros(len(f), dtype=bool)
            possible = np.zeros(len(f), dtype=bool)
            for h in (1, 2, 3):
                left, right = h*center*a, h*center*b
                guaranteed |= (f >= right-tolerance+slack) & (f <= left+tolerance-slack)
                possible |= (f >= left-tolerance-slack) & (f <= right+tolerance+slack)
            low = np.maximum(0., p[:, guaranteed].sum(axis=1)/totals-1e-12)
            high = np.minimum(1., p[:, possible].sum(axis=1)/totals+1e-12)
            record[name] = {"lower": float(np.median(low)), "upper": float(np.median(high))}
        union.update(_possible(record, floor, margin))
    return {"possible_suggestions": sorted(union & broad), "global_possible": sorted(broad),
            "reason": "closed_cell_outer_approximation", "cells_checked": len(cells)}
