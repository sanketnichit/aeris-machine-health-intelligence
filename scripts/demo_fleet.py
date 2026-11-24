"""Explicitly synthetic local API demonstration; no hardware connection."""
import argparse
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

SIGNALS=("horizontal_vibration_rms","vertical_vibration_rms")
ASSETS=("synthetic-normal","synthetic-missing","synthetic-drift")
START=datetime(2026,1,1,tzinfo=timezone.utc)


def scenario():
    records=[]
    for i in range(60):
        for j,asset in enumerate(ASSETS):
            horizontal=round(1.0+0.08*math.sin(i/4+j),6)
            vertical=round(0.8+0.05*math.cos(i/5+j),6)
            if asset=="synthetic-drift" and i>=40:
                horizontal=round(horizontal+(i-39)*0.15,6)
            measurements={SIGNALS[0]:{"value":horizontal,"unit":"m/s2"},
                          SIGNALS[1]:{"value":vertical,"unit":"m/s2"}}
            if asset=="synthetic-missing" and 20<=i<30:
                del measurements[SIGNALS[1]]
            records.append({"asset_id":asset,"timestamp":(START+timedelta(seconds=10*i)).isoformat(),
                            "measurements":measurements})
    return {"schema_version":1,"records":records}


def submit(base,route,payload):
    headers={"Content-Type":"application/json"}
    token=os.environ.get("AERIS_API_TOKEN")
    if token:
        headers["Authorization"]="Bearer "+token
    request=Request(base.rstrip("/")+route,data=json.dumps(payload).encode(),headers=headers)
    with urlopen(request,timeout=15) as response:
        return json.load(response)


def run(base,pace=0):
    if not math.isfinite(pace) or not 0<=pace<=60:
        raise ValueError('Pace must be 0 to 60 seconds')
    for asset in ASSETS:
        submit(base,"/v1/assets",{"asset_id":asset,"name":"Synthetic demo: "+asset.removeprefix("synthetic-"),
                                  "expected_measurements":list(SIGNALS)})
        submit(base,"/v1/policies",{"asset_id":asset,"bounds":{SIGNALS[0]:{"max":2.0}}})
    payload=scenario()
    if pace==0:
        return submit(base,"/v1/telemetry/ingest",payload)
    totals={"status":"stored","inserted":0,"duplicates":0,"events_created":0,"persisted":True,"forecast":None}
    for offset in range(0,len(payload["records"]),len(ASSETS)):
        if offset:
            time.sleep(pace)
        result=submit(base,"/v1/telemetry/ingest",{"schema_version":1,"records":payload["records"][offset:offset+len(ASSETS)]})
        for key in ("inserted","duplicates","events_created"):
            totals[key]+=result[key]
    return totals


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:8080")
    parser.add_argument("--pace",type=float,default=0,help="Seconds between historical synthetic batches; 0 sends all at once")
    args=parser.parse_args()
    print(json.dumps(run(args.url,args.pace),indent=2))
