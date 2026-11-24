"""Split conformal intervals for held-out engine endpoints.

Calibration must use one independently selected endpoint per calibration engine,
disjoint from training and model selection. Coverage assumes exchangeability.
"""
import math
import numpy as np


def conformal_radius(actual, predicted, alpha=0.1):
    """Finite-sample absolute-residual quantile; fail if calibration is too small."""
    y = np.asarray(actual, dtype=float)
    p = np.asarray(predicted, dtype=float)
    if y.ndim != 1 or y.shape != p.shape or not len(y):
        raise ValueError("Expected aligned nonempty one-dimensional calibration arrays")
    if not np.isfinite(y).all() or not np.isfinite(p).all() or (y < 0).any():
        raise ValueError("Invalid calibration values")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    rank = math.ceil((len(y) + 1) * (1 - alpha))
    if rank > len(y):
        raise ValueError("Insufficient independent calibration engines for finite interval")
    return float(np.sort(np.abs(y - p))[rank - 1])


def intervals(predicted, radius):
    p = np.asarray(predicted, dtype=float)
    if p.ndim != 1 or not np.isfinite(p).all() or (p < 0).any():
        raise ValueError("Expected finite nonnegative RUL predictions")
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("Invalid interval radius")
    return np.maximum(0, p - radius), p + radius


def interval_metrics(actual, lower, upper):
    y, lo, hi = (np.asarray(v, dtype=float) for v in (actual, lower, upper))
    if y.ndim != 1 or not len(y) or y.shape != lo.shape or y.shape != hi.shape:
        raise ValueError("Expected aligned nonempty endpoint arrays")
    if not all(np.isfinite(v).all() for v in (y, lo, hi)) or (y < 0).any() or (lo < 0).any() or (hi < lo).any():
        raise ValueError("Invalid interval values")
    return {"coverage": float(((y >= lo) & (y <= hi)).mean()),
            "mean_width": float((hi - lo).mean()), "endpoints": len(y)}
