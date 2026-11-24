"""Transparent advisory reliability policy, not a safety certification."""
import numpy as np


def assess_forecast(reference, learned, prediction, radius, *, observed, scale,
                    min_observations=5, disagreement_limit=.5, width_limit=1.):
    """Return a forecast only when all configured heuristic checks pass.

    Scale is a positive fitting-population reference lifetime. A missing
    calibration radius is an explicit abstention, never zero uncertainty.
    """
    values = np.asarray([reference, learned, prediction, scale], dtype=float)
    if not np.isfinite(values).all() or (values[:3] < 0).any() or scale <= 0:
        raise ValueError("Invalid forecast or reference scale")
    if not isinstance(observed, (int, np.integer)) or observed < 0:
        raise ValueError("Invalid observation count")
    if min_observations < 1 or not np.isfinite([disagreement_limit,width_limit]).all() or min(disagreement_limit,width_limit) < 0:
        raise ValueError("Invalid review policy")
    if radius is not None and (not np.isfinite(radius) or radius < 0):
        raise ValueError("Invalid calibration radius")
    disagreement = abs(reference-learned)/scale
    reasons = []
    if observed < min_observations:
        reasons.append("insufficient_history")
    if radius is None:
        lower = upper = width = None
        reasons.append("insufficient_calibration")
    else:
        lower = max(0., prediction-radius)
        upper = prediction+radius
        width = (upper-lower)/scale
        if width > width_limit:
            reasons.append("wide_interval")
    if disagreement > disagreement_limit:
        reasons.append("model_disagreement")
    return {"status":"review_required" if reasons else "forecast_available",
            "reasons":reasons,"candidate":float(prediction),
            "advisory_forecast":None if reasons else float(prediction),
            "lower":None if lower is None else float(lower),
            "upper":None if upper is None else float(upper),
            "normalized_width":None if width is None else float(width),
            "normalized_disagreement":float(disagreement)}


def selective_metrics(actual, predicted, accepted):
    y,p,k = np.asarray(actual,dtype=float),np.asarray(predicted,dtype=float),np.asarray(accepted)
    if y.ndim!=1 or y.shape!=p.shape or y.shape!=k.shape or not len(y) or k.dtype.kind!="b" or not np.isfinite(y).all() or not np.isfinite(p).all() or (y<0).any() or (p<0).any():
        raise ValueError("Invalid selective evaluation")
    err=np.abs(y-p)
    return {"endpoints":len(y),"accepted":int(k.sum()),"abstained":int((~k).sum()),
            "retained_fraction":float(k.mean()),"all_mae":float(err.mean()),
            "retained_mae":float(err[k].mean()) if k.any() else None,
            "abstained_mae":float(err[~k].mean()) if (~k).any() else None}
