import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from src.api import make_server
from src.telemetry_contract import validate_batch


def batch():
    return {"schema_version":1,"records":[{"asset_id":"bearing-1",
        "timestamp":"2026-11-24T20:00:00+05:30",
        "measurements":{"horizontal_vibration_rms":{"value":1.25,"unit":"m/s2"}}}]}


def test_normalization():
    result=validate_batch(batch())
    assert result["records"][0]["timestamp"]=="2026-11-24T14:30:00Z"
    assert result["validated_records"]==1
    assert result["persisted"] is False and result["forecast"] is None


@pytest.mark.parametrize("value",[True,float("nan"),float("inf"),-1,"1"])
def test_invalid_measurement(value):
    data=batch()
    data["records"][0]["measurements"]["horizontal_vibration_rms"]["value"]=value
    with pytest.raises(ValueError):
        validate_batch(data)


def test_duplicate_timestamp_and_wrong_unit():
    data=batch()
    data["records"].append(data["records"][0].copy())
    with pytest.raises(ValueError,match="strictly increase"):
        validate_batch(data)
    data=batch()
    data["records"][0]["measurements"]["horizontal_vibration_rms"]["unit"]="g"
    with pytest.raises(ValueError,match="contract"):
        validate_batch(data)


@pytest.fixture
def service():
    server=make_server(port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_health_evidence_schema(service):
    for route in ("/health","/v1/evidence","/v1/schema"):
        with urlopen(service+route,timeout=5) as response:
            assert response.status==200
            result=json.load(response)
            if route=="/v1/evidence":
                assert len(result["evidence"])>=8


def test_http_validation_and_rejection(service):
    def request(raw):
        return urlopen(Request(service+"/v1/telemetry/validate",data=raw,
            headers={"Content-Type":"application/json"}),timeout=5)
    with request(json.dumps(batch()).encode()) as response:
        assert json.load(response)["status"]=="validated_only"
    for raw in (b'{"schema_version":1,"schema_version":1,"records":[]}',b'{"x":NaN}',b"{}"):
        with pytest.raises(HTTPError) as exc:
            request(raw)
        assert exc.value.code==400
