"""Conditional Paderborn preprocessing; never establishes clock or geometry validity.

Both paths use the same frozen 12 kHz anti-alias resampling and four windows.
The stored-time path assumes timestamps are ADC instants in seconds; the
nominal path assumes 64 kHz uniform indexing. Neither assumption is verified.
"""
import math
import numpy as np
from scipy.signal import resample_poly

SOURCE_RATE=64000
RATE=12000
WINDOW=8192
WINDOWS=4
MAX_GAP=8/SOURCE_RATE
MAX_SAMPLES=1_000_000
# Extra source points protect the fixed analyzed endpoint from filter edges.
MIN_SOURCE=math.ceil(WINDOW*WINDOWS*SOURCE_RATE/RATE)+256


def _vector(values):
    a=np.asarray(values)
    if a.ndim!=1 or not np.issubdtype(a.dtype,np.number) or np.iscomplexobj(a) or not 2<=len(a)<=MAX_SAMPLES:
        raise ValueError("Expected bounded real vector")
    a=a.astype(float)
    if not np.isfinite(a).all():
        raise ValueError("Nonfinite input")
    return a


def linked_axis(record,name):
    y=record["Y"]
    channels=[y] if isinstance(y,dict) else list(y)
    matches=[v for v in channels if v.get("Name")==name]
    if len(matches)!=1:
        raise ValueError("Expected one explicitly named channel")
    channel=matches[0]
    x=record["X"]
    axes=[x] if isinstance(x,dict) else list(x)
    raw_index=channel.get("XIndex")
    if type(raw_index) not in (int,float) or not math.isfinite(raw_index) or not float(raw_index).is_integer():
        raise ValueError("Missing integer XIndex")
    idx=int(raw_index)-1
    if not 0<=idx<len(axes):
        raise ValueError("XIndex outside axis inventory")
    axis=axes[idx]
    if not isinstance(channel.get("Raster"),str) or not channel["Raster"] or axis.get("Raster")!=channel["Raster"]:
        raise ValueError("Raster and XIndex disagree")
    values,times=_vector(channel["Data"]),_vector(axis["Data"])
    if len(values)!=len(times) or not (np.diff(times)>0).all():
        raise ValueError("Channel and timestamp contract mismatch")
    return values,times


def _resample(signal):
    x=resample_poly(signal,3,16,window=("kaiser",5.0),padtype="constant")
    if len(x)<WINDOW*WINDOWS:
        raise ValueError("Insufficient effective samples")
    return x[:WINDOW*WINDOWS]


def conditional_paths(values,timestamps):
    x,t=_vector(values),_vector(timestamps)
    if len(x)!=len(t) or len(x)<MIN_SOURCE:
        raise ValueError("Insufficient or mismatched source samples")
    if np.min(x)==np.max(x):
        raise ValueError("Constant source waveform")
    t=t-t[0]
    steps=np.diff(t)
    if not np.isfinite(steps).all() or not (steps>0).all():
        raise ValueError("Stored times must be strictly increasing")
    nominal=_resample(x)
    if steps.max()>MAX_GAP:
        return {"nominal":nominal,"stored_time":None,"reason":"stored_time_gap_limit_exceeded",
                "max_gap":float(steps.max()),"span":float(t[-1])}
    count=min(MAX_SAMPLES,int(math.floor(t[-1]*SOURCE_RATE))+1)
    grid=np.arange(count,dtype=float)/SOURCE_RATE
    grid=grid[grid<=t[-1]]
    if len(grid)<MIN_SOURCE:
        return {"nominal":nominal,"stored_time":None,"reason":"stored_time_span_insufficient",
                "max_gap":float(steps.max()),"span":float(t[-1])}
    repaired=np.interp(grid,t,x)
    return {"nominal":nominal,"stored_time":_resample(repaired),"reason":None,
            "max_gap":float(steps.max()),"span":float(t[-1])}


def effective_orders(rolling_elements,pitch_diameter,element_diameter,angle_deg):
    values=(rolling_elements,pitch_diameter,element_diameter,angle_deg)
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
        raise ValueError("Finite explicit geometry required")
    if not float(rolling_elements).is_integer() or not 3<=rolling_elements<=100 or not 0<element_diameter<pitch_diameter or not 0<=angle_deg<90:
        raise ValueError("Invalid bearing geometry")
    ratio=element_diameter/pitch_diameter
    q=ratio*math.cos(math.radians(angle_deg))
    # Ball order is twice BSF to match the frozen MFPT diagnostic convention.
    return {"inner":rolling_elements/2*(1+q),"outer":rolling_elements/2*(1-q),
            "ball":(1-q*q)/ratio}


def comparison_summary(paths):
    result={"scope":"conditional_preprocessing_sensitivity_not_clock_validation",
            "reason":paths["reason"],"max_stored_gap":paths["max_gap"],
            "stored_span":paths["span"],"effective_samples":len(paths["nominal"]),
            "relative_waveform_l2_difference":None,"diagnostic_scoring_performed":False,
            "operational_authorization":False}
    if paths["stored_time"] is not None:
        x,y=paths["nominal"],paths["stored_time"]
        # Scale before norm to avoid overflow; dimensionless sensitivity only.
        scale=max(float(np.max(np.abs(x))),float(np.max(np.abs(y))))
        if scale<=0:
            raise ValueError("Undefined waveform comparison")
        denominator=np.linalg.norm(x/scale)
        if denominator==0:
            raise ValueError("Undefined nominal waveform norm")
        result["relative_waveform_l2_difference"]=float(np.linalg.norm((x/scale)-(y/scale))/denominator)
    return result
