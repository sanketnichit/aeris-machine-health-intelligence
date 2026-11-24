"""Disposable-stack integration check; never use with production telemetry."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ASSET="synthetic-reliability-audit"
SIGNAL="horizontal_vibration_rms"


def client(base,token,route,payload=None):
    headers={"Content-Type":"application/json"}
    if token:
        headers["Authorization"]="Bearer "+token
    request=Request(base.rstrip("/")+route,headers=headers,
                    data=None if payload is None else json.dumps(payload).encode())
    try:
        with urlopen(request,timeout=15) as response:
            return response.status,json.load(response)
    except HTTPError as exc:
        return exc.code,json.load(exc)


def batch(value=3):
    return {"schema_version":1,"records":[{"asset_id":ASSET,"timestamp":"2026-01-01T00:00:00Z",
                        "measurements":{SIGNAL:{"value":value,"unit":"m/s2"}}}]}


def run(base,token):
    if not token:
        raise ValueError("Configure a token on the disposable service and client")
    def get(route):
        code,result=client(base,token,route)
        assert code==200,(code,result)
        return result
    def post(route,payload):
        code,result=client(base,token,route,payload)
        assert code==200,(code,result)
        return result
    assert client(base,None,"/health")[0]==200
    assert client(base,None,"/v1/evidence")[0]==200
    for route in ("/v1/assets","/v1/events","/v1/incidents","/v1/advisory?asset_id="+ASSET):
        assert client(base,None,route)[0]==401
        assert client(base,"incorrect-token",route)[0]==401
    assert client(base,None,"/v1/telemetry/ingest",batch())[0]==401
    post("/v1/assets",{"asset_id":ASSET,"name":"Synthetic reliability audit","expected_measurements":[SIGNAL]})
    post("/v1/policies",{"asset_id":ASSET,"bounds":{SIGNAL:{"max":2}}})
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:post("/v1/telemetry/ingest",batch()),range(16)))
    assert sum(x["inserted"] for x in results)==1
    assert sum(x["duplicates"] for x in results)==15
    assert sum(x["events_created"] for x in results)==1
    assert client(base,token,"/v1/telemetry/ingest",batch(4))[0]==409
    assert len(get("/v1/telemetry/history?asset_id="+ASSET)["records"])==1
    assert len(get("/v1/events?asset_id="+ASSET)["events"])==1
    post("/v1/freshness",{"asset_id":ASSET,"max_age_seconds":60})
    deadline=time.monotonic()+90
    while True:
        rows=[i for i in get("/v1/incidents?limit=1000")["incidents"] if i["asset_id"]==ASSET]
        fresh=[i for i in rows if i["kind"]=="telemetry_freshness"]
        if fresh:
            assert len(fresh)==1 and fresh[0]["detail"]["reason"]=="stale_data"
            break
        if time.monotonic()>=deadline:
            raise AssertionError("Periodic worker did not open freshness incident")
        time.sleep(2)
    incident=next(i for i in rows if i["kind"]=="configured_bound_breach")
    identifier=incident["incident_id"]
    payload={"incident_id":identifier,"action":"resolve","note":"Invalid transition test"}
    assert client(base,token,"/v1/incidents/transition",payload)[0]==409
    payload={"incident_id":identifier,"action":"acknowledge","note":"Synthetic review"}
    with ThreadPoolExecutor(max_workers=4) as pool:
        codes=list(pool.map(lambda _:client(base,token,"/v1/incidents/transition",payload)[0],range(4)))
    assert sorted(codes)==[200,409,409,409]
    post("/v1/incidents/transition",{"incident_id":identifier,"action":"resolve","note":"Synthetic review complete"})
    result=get("/v1/advisory?asset_id="+ASSET)
    assert result["status"]=="review_required" and result["forecast"]["remaining_life"] is None
    reviewed=next(i for i in get("/v1/incidents?limit=1000")["incidents"] if i["incident_id"]==identifier)
    assert reviewed["status"]=="resolved"
    assert [h["action"] for h in reviewed["history"]]==["opened","acknowledged","resolved"]
    return {"concurrent_ingest_requests":16,"inserted":1,"duplicates":15,
            "conflicting_record_rejected":True,"periodic_freshness_detected":True,
            "concurrent_acknowledgements":4,"successful_acknowledgements":1,
            "resolved_incident":identifier,"forecast_withheld":True}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:8080")
    args=parser.parse_args()
    print(json.dumps(run(args.url,os.environ.get("AERIS_API_TOKEN")),indent=2))
