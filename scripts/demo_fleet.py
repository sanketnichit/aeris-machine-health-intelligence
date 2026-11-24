"""Explicitly synthetic local API demonstration; no hardware connection."""
import argparse
import json
import math
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
    request=Request(base.rstrip("/")+route,data=json.dumps(payload).encode(),
                    headers={"Content-Type":"application/json"})
    with urlopen(request,timeout=15) as response:
        return json.load(response)


def run(base):
    for asset in ASSETS:
        submit(base,"/v1/assets",{"asset_id":asset,"name":"Synthetic demo: "+asset.removeprefix("synthetic-"),
                                  "expected_measurements":list(SIGNALS)})
        submit(base,"/v1/policies",{"asset_id":asset,"bounds":{SIGNALS[0]:{"max":2.0}}})
    return submit(base,"/v1/telemetry/ingest",scenario())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:8080")
    args=parser.parse_args()
    print(json.dumps(run(args.url),indent=2))
