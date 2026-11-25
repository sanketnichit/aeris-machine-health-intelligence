"""Tighter sufficient stability checks over closed frequency-scale subintervals.

No sparse-grid guarantee: every point is covered by a closed cell. Numerical
slack can force abstention at boundaries; this is not exact interval arithmetic.
"""
import numpy as np

from src.order_uncertainty import ORDERS, interval_fractions, stable_suggestion

MAX_CELLS = 4096


def breakpoint_partition(f, centers, interval, tolerance):
    lo, hi = interval
    points = {float(lo), float(hi)}
    for c in centers.values():
        for h in (1, 2, 3):
            for sign in (-1, 1):
                crossings = (f + sign*tolerance)/(h*c)
                points.update(float(v) for v in crossings if lo < v < hi)
    ordered = sorted(points)
    if len(ordered) == 1:
        return [(lo, hi)]
    # Bisect each region, avoiding coupling different endpoint ambiguities
    # when feasible. Closed cells still cover both original breakpoints.
    if 2*(len(ordered)-1) > MAX_CELLS:
        return None
    cells = []
    for a,b in zip(ordered,ordered[1:]):
        mid = a+(b-a)/2
        if a < mid < b:
            cells.extend([(a,mid),(mid,b)])
        else:
            cells.append((a,b))
    return cells


def verify_breakpoints(frequencies, window_powers, centers, interval, tolerance, floor, margin):
    """Accept only one common winner established throughout every closed cell.

    Return the original global sufficient result immediately when available.
    Otherwise bound the score within each cell using common-scale localization.
    A complexity cap yields abstention rather than silently sampling cells.
    """
    if not isinstance(window_powers,(list,tuple)) or not 1 <= len(window_powers) <= 1000:
        raise ValueError("Expected bounded window list")
    global_bounds = [interval_fractions(frequencies,p,centers,interval,tolerance)
                     for p in window_powers]
    baseline = stable_suggestion(global_bounds,floor,margin)
    if baseline["suggestion"] is not None:
        return {"suggestion":baseline["suggestion"],"reason":"global_bound_sufficient",
                "cells_checked":0,"cell_count":0}
    f = np.asarray(frequencies,dtype=float)
    p = np.asarray(window_powers,dtype=float)
    totals = p.sum(axis=1)
    cells = breakpoint_partition(f,centers,interval,tolerance)
    if cells is None:
        return {"suggestion":None,"reason":"partition_budget_exceeded",
                "cells_checked":0,"cell_count":None}
    # Same spectral-bin boundary slack as the global sufficient test.
    slack = 64*np.finfo(float).eps*max(1.,float(f[-1]),3*max(centers.values())*interval[1])
    winner = None
    for index,(a,b) in enumerate(cells,1):
        per_window = [{} for _ in window_powers]
        for name,c in centers.items():
            guaranteed = np.zeros(len(f),dtype=bool)
            possible = np.zeros(len(f),dtype=bool)
            for h in (1,2,3):
                left,right = h*c*a,h*c*b
                guaranteed |= (f >= right-tolerance+slack)&(f <= left+tolerance-slack)
                possible |= (f >= left-tolerance-slack)&(f <= right+tolerance+slack)
            lower = np.maximum(0.,p[:,guaranteed].sum(axis=1)/totals-1e-12)
            upper = np.minimum(1.,p[:,possible].sum(axis=1)/totals+1e-12)
            for i in range(len(window_powers)):
                per_window[i][name] = {"lower":float(lower[i]),"upper":float(upper[i])}
        result = stable_suggestion(per_window,floor,margin)["suggestion"]
        if result is None or (winner is not None and result != winner):
            return {"suggestion":None,"reason":"cell_stability_not_established",
                    "cells_checked":index,"cell_count":len(cells),"first_unresolved_cell":[a,b]}
        winner = result
    return {"suggestion":winner,"reason":"all_cells_stable",
            "cells_checked":len(cells),"cell_count":len(cells)}
