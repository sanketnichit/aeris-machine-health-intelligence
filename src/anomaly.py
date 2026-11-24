"""Exploratory per-signal deviation scoring, not a probability or failure diagnosis."""
import math
from statistics import median


def deviation_series(records, signal, window=30, minimum=10):
    if type(window) is not int or type(minimum) is not int or not 3<=minimum<=window<=1000:
        raise ValueError("Require 3 <= minimum <= window <= 1000")
    baseline=[]
    result=[]
    for record in records:
        item=record["measurements"].get(signal)
        point={"timestamp":record["timestamp"],"value":None,"baseline":None,
               "score":None,"status":"missing_measurement"}
        if item is not None:
            value=float(item["value"])
            if not math.isfinite(value):
                raise ValueError("Nonfinite measurement")
            point["value"]=value
            prior=baseline[-window:]
            if len(prior)<minimum:
                point["status"]="insufficient_history"
            else:
                center=median(prior)
                mad=median(abs(v-center) for v in prior)
                point["baseline"]=center if math.isfinite(center) else None
                scale=1.4826*mad
                if not math.isfinite(center) or not math.isfinite(scale) or scale<=max(1e-12,abs(center)*1e-12):
                    point["status"]="unstable_scale"
                else:
                    score=abs(value-center)/scale
                    if math.isfinite(score):
                        point["score"]=score
                        point["status"]="scored"
                    else:
                        point["status"]="unstable_scale"
            baseline.append(value)
        result.append(point)
    return result
