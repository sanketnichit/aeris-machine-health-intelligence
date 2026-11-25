"""Training-only regime normalization and observable-prefix support checks.

Setting support is not fault-mode recognition or a guarantee of exchangeability.
"""
import math
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from src.prognostics import SETTINGS, SENSORS, validate_trajectories, causal_features


def finite_radius(values, alpha=.1):
    v=np.asarray(values,dtype=float)
    if v.ndim!=1 or not np.isfinite(v).all() or (v<0).any() or not 0<alpha<1:
        raise ValueError("Invalid calibration scores")
    rank=math.ceil((len(v)+1)*(1-alpha))
    return None if rank>len(v) else float(np.sort(v)[rank-1])


class RegimeFeatures:
    def __init__(self, clusters):
        if type(clusters) is not int or not 1<=clusters<=6:
            raise ValueError("Expected 1 to 6 declared training regimes")
        self.clusters=clusters

    def fit(self, frame):
        data=validate_trajectories(frame)
        x=data[SETTINGS].to_numpy()
        self.center=x.mean(axis=0)
        # Floors in native C-MAPSS setting units; fixed before evaluation.
        self.scale=np.maximum(x.std(axis=0),[.1,.01,1.])
        self.kmeans=KMeans(n_clusters=self.clusters,random_state=42,n_init=10)
        groups=self.kmeans.fit_predict((x-self.center)/self.scale)
        sensors=data[SENSORS].to_numpy()
        self.means=[]; self.scales=[]
        for k in range(self.clusters):
            part=sensors[groups==k]
            if not len(part):
                raise ValueError("Empty training regime")
            self.means.append(part.mean(axis=0))
            self.scales.append(np.maximum(part.std(axis=0),1e-6))
        self.means=np.asarray(self.means)
        self.scales=np.asarray(self.scales)
        return self

    def transform(self, frame):
        data=validate_trajectories(frame)
        distances=self.kmeans.transform((data[SETTINGS].to_numpy()-self.center)/self.scale)
        group=distances.argmin(axis=1)
        distance=distances.min(axis=1)
        normalized=data.copy()
        normalized[SENSORS]=(data[SENSORS].to_numpy()-self.means[group])/self.scales[group]
        x=causal_features(normalized)
        # No retrospective per-engine full-life normalizer.
        first=normalized.groupby("unit")[SENSORS].transform("first")
        x=pd.concat([x,(normalized[SENSORS]-first).add_suffix("_relative")],axis=1)
        x["regime"]=group
        x["setting_distance"]=distance
        prefix=pd.Series(distance).groupby(data.unit).cummax().to_numpy()
        return x,prefix


def forecast_gate(prediction, prefix_distance, support_radius, interval_radius,
                  *, domain_matches, width_limit=80.):
    if not isinstance(domain_matches,bool):
        raise ValueError("Explicit domain applicability required")
    for value in (prediction,prefix_distance,width_limit):
        if not math.isfinite(value) or value<0:
            raise ValueError("Invalid forecast input")
    for value in (support_radius,interval_radius):
        if value is not None and (not math.isfinite(value) or value<0):
            raise ValueError("Invalid calibrated radius")
    reason=None
    lo=hi=None
    if not domain_matches:
        reason="declared_domain_mismatch"
    elif support_radius is None or interval_radius is None:
        reason="insufficient_calibration"
    elif prefix_distance>support_radius:
        reason="settings_outside_calibrated_support"
    else:
        lo=max(0.,prediction-interval_radius); hi=prediction+interval_radius
        if hi-lo>width_limit:
            reason="interval_too_wide"
    return {"status":"withheld" if reason else "conditional_research_forecast",
            "reason":reason,"forecast":None if reason else float(prediction),
            "interval":None if reason else [float(lo),float(hi)],
            "operational_authorization":False}
