"""Conservative harmonic-bin bounds over a declared common frequency scale.

Research-only sufficient condition, not an estimated speed or calibrated risk.
"""
import math
import numpy as np

ORDERS = ("inner", "outer", "ball")


def _number(v):
    return type(v) in (int, float) and math.isfinite(v)


def interval_fractions(frequencies, powers, centers, scale_interval, tolerance_hz):
    """Bound normalized power for each harmonic union at every scale in [lo, hi].

    A bin guaranteed inside any one harmonic throughout the interval contributes
    to the lower bound; a bin possibly inside any harmonic contributes to upper.
    This may be conservative when coverage transfers between harmonics.
    """
    f = np.asarray(frequencies, dtype=float)
    p = np.asarray(powers, dtype=float)
    if (f.ndim != 1 or p.shape != f.shape or not 2 <= len(f) <= 4097
            or not np.isfinite(f).all() or not np.isfinite(p).all()
            or f[0] != 0 or np.any(np.diff(f) <= 0) or np.any(p < 0) or p[0] != 0):
        raise ValueError("Invalid one-sided non-DC spectrum")
    total = float(p.sum())
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Undefined spectral power")
    if not isinstance(centers, dict) or set(centers) != set(ORDERS):
        raise ValueError("Expected three characteristic frequencies")
    if any(not _number(c) or not 0 < c <= f[-1] for c in centers.values()):
        raise ValueError("Invalid characteristic frequency")
    if not isinstance(scale_interval, (list, tuple)) or len(scale_interval) != 2:
        raise ValueError("Declared frequency-scale interval required")
    lo, hi = scale_interval
    if not all(_number(s) for s in (lo, hi)) or not .5 <= lo <= 1 <= hi <= 1.5:
        raise ValueError("Invalid frequency-scale interval")
    if not _number(tolerance_hz) or not 0 < tolerance_hz <= f[-1]:
        raise ValueError("Invalid harmonic tolerance")
    bounds = {}
    # Conservative numerical slack at bin boundaries; not formal interval arithmetic.
    slack = 64 * np.finfo(float).eps * max(1., float(f[-1]), 3 * max(centers.values()) * hi)
    for name, center in centers.items():
        guaranteed = np.zeros(len(f), dtype=bool)
        possible = np.zeros(len(f), dtype=bool)
        for harmonic in (1, 2, 3):
            a, b = harmonic * center * lo, harmonic * center * hi
            guaranteed |= (f >= b - tolerance_hz + slack) & (f <= a + tolerance_hz - slack)
            possible |= (f >= a - tolerance_hz - slack) & (f <= b + tolerance_hz + slack)
        lower = max(0., float(p[guaranteed].sum()/total) - 1e-12)
        upper = min(1., float(p[possible].sum()/total) + 1e-12)
        bounds[name] = {"lower": lower, "upper": upper}
    return bounds


def stable_suggestion(window_bounds, floor, margin):
    """Median monotonicity gives record bounds; accept only a sufficient winner."""
    if not _number(floor) or not 0 <= floor < 1 or not _number(margin) or not 0 <= margin <= 1:
        raise ValueError("Invalid frozen decision parameters")
    if not isinstance(window_bounds, (list, tuple)) or not 1 <= len(window_bounds) <= 1000:
        raise ValueError("Expected bounded window list")
    for window in window_bounds:
        if not isinstance(window, dict) or set(window) != set(ORDERS):
            raise ValueError("Invalid window bounds")
        for band in window.values():
            if not isinstance(band, dict) or set(band) != {"lower", "upper"}:
                raise ValueError("Invalid fraction bounds")
            a, b = band["lower"], band["upper"]
            if not all(_number(v) for v in (a, b)) or not 0 <= a <= b <= 1:
                raise ValueError("Invalid fraction bounds")
    record = {k: {side: float(np.median([w[k][side] for w in window_bounds]))
                  for side in ("lower", "upper")} for k in ORDERS}
    winners = []
    for name in ORDERS:
        low = record[name]["lower"]
        other = max(record[k]["upper"] for k in ORDERS if k != name)
        if low > floor and low > other and (low-other)/low >= margin + 1e-12:
            winners.append(name)
    return {"suggestion": winners[0] if len(winners) == 1 else None,
            "reason": "interval_stable_research_suggestion" if len(winners) == 1 else "interval_stability_not_established",
            "median_bounds": record}
