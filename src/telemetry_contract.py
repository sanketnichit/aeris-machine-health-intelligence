"""Validation-only telemetry contract; no inference or equipment control."""
import math
import re
from datetime import datetime, timezone

SCHEMA_VERSION = 1
MAX_RECORDS = 1000
ASSET = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
UNITS = {
    "air_temperature": "K",
    "process_temperature": "K",
    "rotational_speed": "rpm",
    "torque": "N.m",
    "tool_wear": "min",
    "horizontal_vibration_rms": "m/s2",
    "vertical_vibration_rms": "m/s2",
}


def validate_batch(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "records"}:
        raise ValueError("Expected schema_version and records")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported schema version")
    records = payload["records"]
    if not isinstance(records,list) or not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError("Expected 1 to 1000 records")
    normalized = []
    last = {}
    for index, record in enumerate(records):
        if not isinstance(record,dict) or set(record)!={"asset_id","timestamp","measurements"}:
            raise ValueError(f"Record {index}: invalid fields")
        asset = record["asset_id"]
        if not isinstance(asset,str) or not ASSET.fullmatch(asset):
            raise ValueError(f"Record {index}: invalid asset_id")
        stamp = record["timestamp"]
        if not isinstance(stamp,str) or len(stamp)>40 or "T" not in stamp:
            raise ValueError(f"Record {index}: expected ISO timestamp")
        try:
            dt = datetime.fromisoformat(stamp.replace("Z","+00:00"))
            if dt.tzinfo is None or dt.utcoffset() is None:
                raise ValueError("Timezone required")
            dt = dt.astimezone(timezone.utc)
        except (ValueError,OverflowError):
            raise ValueError(f"Record {index}: invalid timestamp or missing timezone") from None
        if asset in last and dt<=last[asset]:
            raise ValueError(f"Record {index}: timestamps must strictly increase per asset within batch")
        last[asset]=dt
        measurements=record["measurements"]
        if not isinstance(measurements,dict) or not measurements or not set(measurements)<=set(UNITS):
            raise ValueError(f"Record {index}: unknown or missing measurement")
        clean={}
        for name,item in measurements.items():
            if not isinstance(item,dict) or set(item)!={"value","unit"} or item["unit"]!=UNITS[name]:
                raise ValueError(f"Record {index}: incorrect measurement contract for {name}")
            value=item["value"]
            if type(value) not in (int,float):
                raise ValueError(f"Record {index}: expected numeric value")
            try:
                value=float(value)
            except OverflowError:
                raise ValueError(f"Record {index}: value too large") from None
            if not math.isfinite(value) or (name!="torque" and value<0):
                raise ValueError(f"Record {index}: invalid measurement value")
            clean[name]={"value":value,"unit":UNITS[name]}
        normalized.append({"asset_id":asset,"timestamp":dt.isoformat().replace("+00:00","Z"),"measurements":clean})
    return {"schema_version":SCHEMA_VERSION,"validated_records":len(normalized),"assets":len(last),
            "records":normalized,"status":"validated_only","persisted":False,"forecast":None}
