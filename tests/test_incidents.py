from datetime import datetime, timezone
import json
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest

from src.api import make_server
from src.telemetry_store import initialize, register, ingest, history, Conflict
from src.incidents import configure_freshness, scan_freshness, list_incidents, transition
from scripts.telemetry_backup import copy_verified


def test_lifecycle_and_freshness(tmp_path):
    db=tmp_path/"store.sqlite3"
    initialize(db)
    register(db,{"asset_id":"a","name":"Asset","expected_measurements":["horizontal_vibration_rms"]})
    configure_freshness(db,"a",60)
    now=datetime(2026,1,1,tzinfo=timezone.utc)
    assert scan_freshness(db,now)["opened"]==1
    assert scan_freshness(db,now)["opened"]==0
    incident=list_incidents(db)["incidents"][0]
    assert incident["detail"]["reason"]=="no_data"
    key=incident["incident_id"]
    with pytest.raises(Conflict):
        transition(db,key,"resolve","Not acknowledged")
    assert transition(db,key,"acknowledge","Review initiated")["status"]=="acknowledged"
    assert transition(db,key,"resolve","Reviewed")["status"]=="resolved"
    assert scan_freshness(db,now)["opened"]==1
    assert len(list_incidents(db)["incidents"])==2


def test_backup_and_restore(tmp_path):
    source=tmp_path/"source.sqlite3"
    initialize(source)
    register(source,{"asset_id":"a","name":"Asset","expected_measurements":["horizontal_vibration_rms"]})
    ingest(source,{"schema_version":1,"records":[{"asset_id":"a","timestamp":"2026-01-01T00:00:00Z",
        "measurements":{"horizontal_vibration_rms":{"value":1,"unit":"m/s2"}}}]})
    backup=copy_verified(source,tmp_path/"backup.sqlite3")
    restored=copy_verified(backup,tmp_path/"restored.sqlite3")
    initialize(restored)
    assert history(restored,"a")==history(source,"a")
    with pytest.raises(ValueError):
        copy_verified(source,backup)


def test_bearer_access(tmp_path):
    token="test-token-"+"x"*32
    server=make_server(port=0,database=tmp_path/"store.sqlite3",token=token)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        base=f"http://127.0.0.1:{server.server_port}"
        with urlopen(base+"/health",timeout=5) as response:
            assert response.status==200
        with pytest.raises(HTTPError) as exc:
            urlopen(base+"/v1/assets",timeout=5)
        assert exc.value.code==401
        with urlopen(Request(base+"/v1/assets",headers={"Authorization":"Bearer "+token}),timeout=5) as response:
            assert json.load(response)["total_assets"]==0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
