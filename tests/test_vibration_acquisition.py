from datetime import datetime, timezone
import hashlib

import pytest

from src.edge_buffer import status
from src.vibration_acquisition import analyze_capture, queue_capture

RAW = b"horizontal,vertical\n-1,-2\n1,2\n-3,-4\n3,4\n"
DEFAULT = {"asset_id": "capture-test", "start": "2026-01-01T05:30:00+05:30",
           "sample_rate_hz": 10, "window_samples": 2, "unit": "g"}


def analyze(raw=RAW, **overrides):
    return analyze_capture(raw, **{**DEFAULT, **overrides})


def test_explicit_units_and_endpoints(tmp_path):
    result = analyze()
    assert result["capture_sha256"] == hashlib.sha256(RAW).hexdigest()
    assert result["sample_count"] == 4
    assert result["window_count"] == 2
    assert result["eligible_for_queue"]
    records = result["batch"]["records"]
    assert [datetime.fromisoformat(r["timestamp"]) for r in records] == [
        datetime(2026, 1, 1, 0, 0, 0, 100000, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 0, 0, 300000, tzinfo=timezone.utc)]
    assert records[0]["measurements"]["horizontal_vibration_rms"]["value"] == pytest.approx(9.80665)
    assert records[1]["measurements"]["vertical_vibration_rms"]["value"] == pytest.approx(4 * 9.80665)
    assert result["windows"][0]["axes"]["horizontal"]["ac_rms_m_s2"] == pytest.approx(9.80665)
    queue = tmp_path / "capture.sqlite3"
    assert queue_capture(queue, result)["queued"]
    assert queue_capture(queue, result)["duplicate_pending"]
    assert status(queue)["pending_batches"] == 1


def test_dc_component_and_quality_flags(tmp_path):
    result = analyze(b"horizontal,vertical\n2,-1\n4,1\n", unit="m/s2")
    h = result["windows"][0]["axes"]["horizontal"]
    assert h["mean_m_s2"] == 3
    assert h["rms_m_s2"] == pytest.approx(10 ** 0.5)
    assert h["ac_rms_m_s2"] == 1
    clipped = analyze(clipping_limit=4)
    assert clipped["flagged_windows"] == 1
    assert not clipped["eligible_for_queue"]
    flat = analyze(b"horizontal,vertical\n1,-1\n1,1\n")
    assert flat["windows"][0]["axes"]["horizontal"]["quality_flags"] == ["constant_axis"]
    queue = tmp_path / "flagged.sqlite3"
    for invalid in (clipped, flat):
        with pytest.raises(ValueError, match="flagged windows"):
            queue_capture(queue, invalid)
    assert not queue.exists()


@pytest.mark.parametrize("raw", [
    b"horizontal,vertical\n1,2\n", b"horizontal,vertical\n1,2\n2,3\n3,4\n",
    b"x,y\n1,2\n2,3\n", b"horizontal,vertical\n1,\n2,3\n",
    b"horizontal,vertical\nnan,2\n2,3\n",
    b"horizontal,vertical\n1e309,2\n2,3\n",
    b"horizontal,vertical\n1,2,3\n2,3\n",
    b"horizontal,vertical\n",
])
def test_invalid_capture(raw):
    with pytest.raises(ValueError):
        analyze(raw)


@pytest.mark.parametrize("overrides", [
    {"unit": "mm/s"}, {"start": "2026-01-01T00:00:00"},
    {"sample_rate_hz": 0}, {"sample_rate_hz": True}, {"sample_rate_hz": 100001},
    {"window_samples": 1}, {"clipping_limit": 0}, {"clipping_limit": float("nan")},
    {"asset_id": "bad asset"},
])
def test_invalid_metadata(overrides):
    with pytest.raises(ValueError):
        analyze(**overrides)


def test_capture_to_authenticated_api(tmp_path, monkeypatch):
    from threading import Thread
    from scripts.demo_fleet import submit
    from src.api import make_server
    from src.edge_buffer import drain
    from src.telemetry_store import history

    token = "capture-test-" + "x" * 32
    monkeypatch.setenv("AERIS_API_TOKEN", token)
    database = tmp_path / "telemetry.sqlite3"
    queue = tmp_path / "edge.sqlite3"
    analysis = analyze()
    queue_capture(queue, analysis)
    server = make_server(port=0, database=database, token=token)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        submit(base, "/v1/assets", {"asset_id": "capture-test", "name": "Capture test",
            "expected_measurements": ["horizontal_vibration_rms", "vertical_vibration_rms"]})
        result = drain(queue, base)
        assert result["blocked"] is None
        assert result["pending_batches"] == 0
        stored = history(database, "capture-test")
        expected = analysis["batch"]["records"]
        assert len(stored) == len(expected) == 2
        for record, source in zip(stored, expected):
            assert datetime.fromisoformat(record["timestamp"]) == datetime.fromisoformat(source["timestamp"])
            assert record["measurements"] == source["measurements"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
    assert not thread.is_alive()


def test_optional_spectrum_keeps_telemetry_contract():
    import math
    rows = ["horizontal,vertical"]
    for i in range(64):
        rows.append(f"{math.sin(2 * math.pi * 8 * i / 64)},{math.sin(2 * math.pi * 12 * i / 64)}")
    raw = ("\n".join(rows) + "\n").encode()
    plain = analyze(raw, sample_rate_hz=64, window_samples=64, unit="m/s2")
    extended = analyze(raw, sample_rate_hz=64, window_samples=64, unit="m/s2", spectrum=True)
    assert plain["batch"] == extended["batch"]
    assert plain["eligible_for_queue"] == extended["eligible_for_queue"]
    assert extended["windows"][0]["axes"]["horizontal"]["spectrum"]["dominant_frequency_hz"] == 8
    assert extended["windows"][0]["axes"]["vertical"]["spectrum"]["dominant_frequency_hz"] == 12


def test_spectrum_quality_withholding():
    raw = ("horizontal,vertical\n" + "1,-1\n1,1\n" * 16).encode()
    result = analyze(raw, sample_rate_hz=32, window_samples=32, spectrum=True)
    assert result["windows"][0]["axes"]["horizontal"]["spectrum"] is None
    assert result["windows"][0]["axes"]["vertical"]["spectrum"] is not None
    assert not result["eligible_for_queue"]
    with pytest.raises(ValueError, match="at least 16"):
        analyze(spectrum=True)
