"""Falsification-only search of the frozen floating-point point decision.

A witnessed disagreement is useful evidence against point-decision invariance.
No witness is not a certificate; this module never authorizes a suggestion.
"""
import numpy as np

from research.cwru_selective import decide
from src.order_breakpoints import breakpoint_partition
from src.order_uncertainty import interval_fractions, stable_suggestion


def search_counterexample(frequencies, window_powers, centers, interval, tolerance,
                          floor, margin):
    if not isinstance(window_powers, (list, tuple)) or not 1 <= len(window_powers) <= 1000:
        raise ValueError("Expected bounded window list")
    bounds = [interval_fractions(frequencies, p, centers, interval, tolerance)
              for p in window_powers]
    stable_suggestion(bounds, floor, margin)  # validate frozen decision parameters
    f = np.asarray(frequencies, dtype=float)
    powers = np.asarray(window_powers, dtype=float)
    totals = powers.sum(axis=1)

    def at(scale):
        scores = {}
        for name, center in centers.items():
            mask = np.zeros(len(f), dtype=bool)
            for h in (1, 2, 3):
                mask |= np.abs(f - h * (center * scale)) <= tolerance
            scores[name] = float(np.median(powers[:, mask].sum(axis=1) / totals))
        return decide(scores, floor, margin)

    nominal = at(1.0)
    if nominal["suggestion"] is None:
        return {"status": "nominal_abstention", "nominal": nominal,
                "points_checked": 1}
    cells = breakpoint_partition(f, centers, interval, tolerance)
    if cells is None:
        return {"status": "partition_budget_exceeded", "nominal": nominal,
                "points_checked": 1}
    points = {float(interval[0]), float(interval[1])}
    for a, b in cells:
        points.update((float(a), float(b), float(a + (b-a)/2)))
    # Count the nominal evaluation once. Endpoints and interiors are searched
    # deterministically, but floating-point crossings are not an exact proof.
    checked = 1
    for scale in sorted(points - {1.0}):
        decision = at(scale)
        checked += 1
        if decision["suggestion"] != nominal["suggestion"]:
            return {"status": "point_counterexample", "nominal": nominal,
                    "points_checked": checked, "witness_scale": scale,
                    "witness_decision": decision,
                    "witness_type": "abstention" if decision["suggestion"] is None
                    else "competing_suggestion"}
    return {"status": "no_witness_found", "nominal": nominal,
            "points_checked": checked}
