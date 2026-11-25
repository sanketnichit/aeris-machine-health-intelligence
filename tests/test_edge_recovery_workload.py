"""Bounded synthetic outage workload against a real local AERIS server."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import socket
from threading import Thread

from scripts.demo_fleet import submit
from src.api import make_server
from src.edge_buffer import drain, enqueue, status
from src.telemetry_store import history

ASSETS = tuple(f"edge-workload-{i}" for i in range(4))
SIGNAL = "horizontal_vibration_rms"
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_batch(index):
    return {"schema_version": 1, "records": [
        {"asset_id": asset,
         "timestamp": (START + timedelta(seconds=10 * index + offset)).isoformat(),
         "measurements": {SIGNAL: {"value": float(index * 10 + offset + j), "unit": "m/s2"}}}
        for offset in range(10) for j, asset in enumerate(ASSETS)
    ]}


def test_offline_workload_recovery(tmp_path, monkeypatch):
    queue = tmp_path / "edge.sqlite3"
    database = tmp_path / "server.sqlite3"
    token = "edge-workload-" + "x" * 32
    monkeypatch.setenv("AERIS_API_TOKEN", token)
    batches = [make_batch(i) for i in range(30)]
    # Four concurrent acquisition workers; every submitted batch repeated.
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda payload: enqueue(queue, payload), batches + batches))
    assert sum(row["queued"] for row in outcomes) == 30
    assert sum(row["duplicate_pending"] for row in outcomes) == 30
    with socket.socket() as unavailable:
        unavailable.bind(("127.0.0.1", 0))
        endpoint = f"http://127.0.0.1:{unavailable.getsockname()[1]}"
        assert drain(queue, endpoint)["blocked"] == "unconfirmed_delivery"
    assert status(queue)["pending_batches"] == 30

    server = make_server(port=0, database=database, token=token)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        for asset in ASSETS:
            submit(base, "/v1/assets", {"asset_id": asset, "name": asset,
                                      "expected_measurements": [SIGNAL]})
        # The server already committed these records before acknowledgement.
        assert submit(base, "/v1/telemetry/ingest", batches[0])["inserted"] == 40
        first = drain(queue, base, limit=7)
        assert first["delivered_batches"] == 7
        assert first["pending_batches"] == 23
        assert first["blocked"] is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
    assert not thread.is_alive()

    # Restart on the same durable server and queue files.
    server = make_server(port=0, database=database, token=token)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        result = drain(queue, base)
        assert result["delivered_batches"] == 23
        assert result["pending_batches"] == 0
        assert result["blocked"] is None
        for j, asset in enumerate(ASSETS):
            records = history(database, asset, limit=1000)
            assert len(records) == 300
            assert [datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) for r in records] == [
                START + timedelta(seconds=i)
                for i in range(300)]
            assert [r["measurements"][SIGNAL]["value"] for r in records] == [
                float(i + j) for i in range(300)]
        assert drain(queue, base)["delivered_batches"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
    assert not thread.is_alive()
