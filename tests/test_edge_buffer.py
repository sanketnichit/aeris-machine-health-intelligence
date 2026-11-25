import copy
import socket
from threading import Thread

import pytest

from scripts.demo_fleet import submit
from src import edge_buffer as edge
from src.api import make_server


def batch():
    return {"schema_version": 1, "records": [{
        "asset_id": "edge-test", "timestamp": "2026-01-01T00:00:00Z",
        "measurements": {"horizontal_vibration_rms": {"value": 1.2, "unit": "m/s2"}},
    }]}


def test_queue_validation_and_capacity(tmp_path, monkeypatch):
    queue = tmp_path / "queue.sqlite3"
    monkeypatch.setattr(edge, "MAX_PENDING", 1)
    data = batch()
    assert edge.enqueue(queue, data)["queued"]
    equivalent = copy.deepcopy(data)
    equivalent["records"][0]["timestamp"] = "2026-01-01T05:30:00+05:30"
    assert edge.enqueue(queue, equivalent)["duplicate_pending"]
    different = copy.deepcopy(data)
    different["records"][0]["timestamp"] = "2026-01-01T00:00:01Z"
    with pytest.raises(ValueError, match="Queue full"):
        edge.enqueue(queue, different)
    data["records"][0]["measurements"]["horizontal_vibration_rms"]["unit"] = "g"
    with pytest.raises(ValueError):
        edge.enqueue(queue, data)
    assert edge.status(queue)["pending_batches"] == 1


@pytest.mark.parametrize("url", ["https://127.0.0.1:8080", "http://example.com:8080",
                                "http://127.0.0.1", "http://127.0.0.1:8080/path",
                                "http://user@127.0.0.1:8080"])
def test_reject_nonlocal_endpoints(url):
    with pytest.raises(ValueError):
        edge.local_endpoint(url)


def test_outage_and_replay(tmp_path, monkeypatch):
    queue = tmp_path / "queue.sqlite3"
    token = "edge-test-" + "x" * 32
    monkeypatch.setenv("AERIS_API_TOKEN", token)
    edge.enqueue(queue, batch())
    # A bound but non-listening port reliably refuses connections.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        result = edge.drain(queue, f"http://127.0.0.1:{sock.getsockname()[1]}")
        assert result["blocked"] == "unconfirmed_delivery"
        assert result["pending_batches"] == 1
    server = make_server(port=0, database=tmp_path / "telemetry.sqlite3", token=token)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        blocked = edge.drain(queue, base)
        assert blocked["blocked"] == "http_404"
        assert blocked["pending_batches"] == 1
        submit(base, "/v1/assets", {"asset_id": "edge-test", "name": "Edge test",
                                   "expected_measurements": ["horizontal_vibration_rms"]})
        # Simulate a server commit before the client's acknowledgement arrived.
        assert submit(base, "/v1/telemetry/ingest", batch())["inserted"] == 1
        delivered = edge.drain(queue, base)
        assert delivered["delivered_batches"] == 1
        assert delivered["pending_batches"] == 0
        assert submit(base, "/v1/telemetry/ingest", batch())["duplicates"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
