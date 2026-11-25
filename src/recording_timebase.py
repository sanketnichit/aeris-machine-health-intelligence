"""Structural timing inspection. No sample clock calibration or fault scoring."""
import math
import numpy as np


def structures(value):
    if isinstance(value,dict):
        return [value]
    if isinstance(value,(list,np.ndarray)):
        return list(value)
    return []


def metadata(value):
    if isinstance(value,(str,int,float,bool)):
        return str(value)[:200]
    arr=np.asarray(value)
    if arr.size==0:
        return "[]"
    if arr.ndim==0:
        return str(arr.item())[:200]
    return f"array shape={arr.shape}, dtype={arr.dtype}"


def vector_summary(value, timing=False):
    a=np.asarray(value)
    out={"shape":list(a.shape),"dtype":str(a.dtype),"count":int(a.size)}
    if a.ndim!=1 or not np.issubdtype(a.dtype,np.number) or np.iscomplexobj(a) or not a.size:
        return {**out,"status":"not_real_vector"}
    a=a.astype(float)
    if not np.isfinite(a).all():
        return {**out,"status":"nonfinite"}
    out.update(status="finite",minimum=float(a.min()),maximum=float(a.max()),
               median=float(np.median(a)),first=float(a[0]),last=float(a[-1]))
    if timing and len(a)>1:
        delta=np.diff(a)
        if not np.isfinite(delta).all():
            return {**out,"status":"nonfinite_difference"}
        median=float(np.median(delta))
        out.update(strictly_increasing=bool((delta>0).all()),median_step=median,
                   min_step=float(delta.min()),max_step=float(delta.max()),
                   max_relative_step_deviation=None if median<=0 else float(np.max(np.abs(delta-median))/median),
                   span=float(a[-1]-a[0]))
    return out


def inspect_record(record):
    if not isinstance(record,dict):
        raise ValueError("Expected named MAT record")
    axes=[]
    for i,x in enumerate(structures(record.get("X"))):
        if not isinstance(x,dict):
            raise ValueError("Unexpected X structure")
        axes.append({"index":i,"metadata":{k:metadata(v) for k,v in x.items() if k!="Data"},
                     "vector":vector_summary(x.get("Data"),True)})
    channels=[]
    for y in structures(record.get("Y")):
        if not isinstance(y,dict):
            raise ValueError("Unexpected Y structure")
        name=y.get("Name")
        if name not in ("vibration_1","speed"):
            continue
        # Do not inspect amplitude distributions of vibration before diagnostic protocol.
        a=np.asarray(y["Data"])
        info={"shape":list(a.shape),"count":int(a.size),"dtype":str(a.dtype)}
        if name=="speed":
            info=vector_summary(a)
        md={k:metadata(v) for k,v in y.items() if k!="Data"}
        # Exact nonempty shared Raster identifier is a candidate association,
        # not a proven schema mapping. Count equality alone never establishes one.
        raster=y.get("Raster")
        candidates=[x["index"] for x in axes if isinstance(raster,str) and raster
                    and x["metadata"].get("Raster")==raster and x["vector"]["count"]==a.size]
        channels.append({"name":name,"metadata":md,"vector":info,
                         "raster_and_count_candidates":candidates,
                         "count_only_candidates":[x["index"] for x in axes if x["vector"]["count"]==a.size]})
    if sorted(x["name"] for x in channels)!=["speed","vibration_1"]:
        raise ValueError("Expected unique speed and vibration channels")
    return {"record_fields":sorted(record),"time_axes":axes,"channels":channels,
            "timing_association_verified":False,"diagnostic_scoring_performed":False}
