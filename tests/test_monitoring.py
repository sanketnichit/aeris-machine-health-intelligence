import json
import sqlite3
import threading
from urllib.request import urlopen

import pytest

from src.api import make_server
from src.telemetry_store import initialize, register, configure_policy, ingest, list_events, history, Conflict
from src.monitoring import validate_policy
from scripts.demo_fleet import run, ASSETS, SIGNALS


def test_policy_events_and_idempotence(tmp_path):
    db=tmp_path/"store.sqlite3"
    initialize(db)
    register(db,{"asset_id":"a","name":"Asset A","expected_measurements":list(SIGNALS)})
    policy={"bounds":{SIGNALS[0]:{"max":2}}}
    assert configure_policy(db,"a",policy)["revision"]==1
    assert configure_policy(db,"a",policy)["revision"]==1
    payload={"schema_version":1,"records":[{"asset_id":"a","timestamp":"2026-01-01T00:00:00Z",
        "measurements":{SIGNALS[0]:{"value":3,"unit":"m/s2"}}}]}
    assert ingest(db,payload)["events_created"]==2
    assert ingest(db,payload)["events_created"]==0
    assert configure_policy(db,"a",{"bounds":{}})["revision"]==2
    assert {e["policy_revision"] for e in list_events(db)["events"]}=={1}
    assert {e["kind"] for e in list_events(db)["events"]}=={"missing_measurements","configured_bound_breach"}
    payload["records"].append({"asset_id":"a","timestamp":"2026-01-01T00:00:10Z",
        "measurements":{SIGNALS[0]:{"value":4,"unit":"m/s2"}}})
    payload["records"][0]["measurements"][SIGNALS[0]]["value"]=5
    with pytest.raises(Conflict):
        ingest(db,payload)
    assert len(history(db,"a"))==1
    assert len(list_events(db)["events"])==2


def test_v1_migration_preserves_assets(tmp_path):
    db=tmp_path/"v1.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE assets (asset_id TEXT PRIMARY KEY, name TEXT NOT NULL, expected TEXT NOT NULL)")
        conn.execute("INSERT INTO assets VALUES ('a','Existing','[]')")
        conn.execute("PRAGMA user_version=1")
    initialize(db)
    assert list_events(db)["events"]==[]
    assert configure_policy(db,"a",{"bounds":{}})["revision"]==1


@pytest.mark.parametrize("bound",[{"min":3,"max":2},{"max":True},{"max":float("nan")},{}])
def test_invalid_bounds(bound):
    with pytest.raises(ValueError):
        validate_policy({"bounds":{SIGNALS[0]:bound}})


def test_demo_fleet_http(tmp_path):
    server=make_server(port=0,database=tmp_path/"demo.sqlite3")
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        base=f"http://127.0.0.1:{server.server_port}"
        result=run(base)
        assert result["inserted"]==180
        with urlopen(base+"/v1/events?limit=1000",timeout=5) as response:
            events=json.load(response)["events"]
        assert len([e for e in events if e["kind"]=="missing_measurements"])==10
        assert any(e["kind"]=="configured_bound_breach" for e in events)
        assert {e["asset_id"] for e in events}==set(ASSETS[1:])
        repeat=run(base)
        assert repeat["duplicates"]==180 and repeat["events_created"]==0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
