"""Observation-level policy events, not validated machine diagnoses."""
import json
import math

from src.telemetry_contract import UNITS


def validate_policy(payload):
    if not isinstance(payload,dict) or set(payload)!={"bounds"}:
        raise ValueError("Expected bounds")
    bounds=payload["bounds"]
    if not isinstance(bounds,dict) or not set(bounds)<=set(UNITS):
        raise ValueError("Unknown measurement in bounds")
    result={}
    for name,bound in bounds.items():
        if not isinstance(bound,dict) or not bound or not set(bound)<={"min","max"}:
            raise ValueError("Expected min and/or max")
        values={}
        for key,value in bound.items():
            if type(value) not in (int,float):
                raise ValueError("Bounds must be finite numbers")
            try:
                value=float(value)
            except OverflowError:
                raise ValueError("Bounds must be finite numbers") from None
            if not math.isfinite(value):
                raise ValueError("Bounds must be finite numbers")
            values[key]=value
        if "min" in values and "max" in values and values["min"]>values["max"]:
            raise ValueError("Minimum exceeds maximum")
        result[name]=values
    return result


def evaluate(expected,measurements,bounds):
    """Evaluate a single observation, without assuming unobserved values."""
    events=[]
    missing=sorted(set(expected)-set(measurements))
    if missing:
        events.append(("missing_measurements",{"missing":missing}))
    for name,limits in sorted(bounds.items()):
        if name not in measurements:
            continue
        value=measurements[name]["value"]
        if "min" in limits and value<limits["min"]:
            events.append(("configured_bound_breach",{"measurement":name,"value":value,
                           "unit":UNITS[name],"direction":"below","bound":limits["min"]}))
        elif "max" in limits and value>limits["max"]:
            events.append(("configured_bound_breach",{"measurement":name,"value":value,
                           "unit":UNITS[name],"direction":"above","bound":limits["max"]}))
    return events
