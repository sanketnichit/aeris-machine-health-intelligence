from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from src import capture_archive as archive
from src.edge_buffer import canonical_batch, status
from src.vibration_acquisition import analyze_capture

RAW = b"horizontal,vertical\n-1,-2\n1,2\n-3,-4\n3,4\n"
SETTINGS = {"asset_id": "archive-test", "start": "2026-01-01T00:00:00Z",
            "sample_rate_hz": 10, "window_samples": 2, "unit": "g"}


def test_concurrent_archive_and_replay(tmp_path):
    path = tmp_path / "archive.sqlite3"
    queue = tmp_path / "edge.sqlite3"
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: archive.archive_capture(path, RAW, **SETTINGS), range(8)))
    assert sum(result["created"] for result in results) == 1
    ident = results[0]["capture_id"]
    assert all(result["capture_id"] == ident for result in results)
    raw, analysis = archive.load_capture(path, ident)
    assert raw == RAW
    assert analysis == analyze_capture(RAW, **SETTINGS)
    rows = archive.list_captures(path)
    assert len(rows) == 1
    assert rows[0]["capture_id"] == ident
    assert rows[0]["eligible_for_queue"]
    assert archive.stage_capture(path, ident, queue)["queue_result"]["queued"]
    assert archive.stage_capture(path, ident, queue)["queue_result"]["duplicate_pending"]
    with sqlite3.connect(queue) as db:
        assert db.execute("SELECT payload FROM pending").fetchone()[0] == canonical_batch(analysis["batch"])
    assert status(queue)["pending_batches"] == 1
    with pytest.raises(ValueError, match="separate files"):
        archive.stage_capture(path, ident, path)


def test_identity_includes_analysis_settings(tmp_path):
    path = tmp_path / "archive.sqlite3"
    a = archive.archive_capture(path, RAW, **SETTINGS)
    b = archive.archive_capture(path, RAW, **{**SETTINGS, "unit": "m/s2"})
    c = archive.archive_capture(path, RAW, **{**SETTINGS, "start": "2026-01-01T05:30:00+05:30"})
    assert a["capture_id"] != b["capture_id"]
    assert c["capture_id"] == a["capture_id"]
    assert not c["created"]
    assert a["analysis"]["capture_sha256"] == b["analysis"]["capture_sha256"]


@pytest.mark.parametrize("field", ["raw", "report"])
def test_corruption_prevents_stage(tmp_path, field):
    path = tmp_path / "archive.sqlite3"
    queue = tmp_path / "queue.sqlite3"
    ident = archive.archive_capture(path, RAW, **SETTINGS)["capture_id"]
    with sqlite3.connect(path) as db:
        db.execute(f"UPDATE captures SET {field}=? WHERE capture_id=?", (b"altered", ident))
    with pytest.raises(ValueError, match="integrity"):
        archive.load_capture(path, ident)
    with pytest.raises(ValueError, match="integrity"):
        archive.stage_capture(path, ident, queue)
    with pytest.raises(ValueError, match="integrity"):
        archive.list_captures(path)
    assert not queue.exists()


def test_flagged_capture_preserved_but_not_staged(tmp_path):
    path = tmp_path / "archive.sqlite3"
    queue = tmp_path / "queue.sqlite3"
    raw = b"horizontal,vertical\n1,-1\n1,1\n"
    result = archive.archive_capture(path, raw, **SETTINGS)
    assert result["created"]
    assert not result["analysis"]["eligible_for_queue"]
    assert archive.load_capture(path, result["capture_id"])[0] == raw
    with pytest.raises(ValueError, match="flagged windows"):
        archive.stage_capture(path, result["capture_id"], queue)
    assert not queue.exists()


def test_capacity_preserves_existing_rows(tmp_path, monkeypatch):
    path = tmp_path / "archive.sqlite3"
    monkeypatch.setattr(archive, "MAX_CAPTURES", 1)
    first = archive.archive_capture(path, RAW, **SETTINGS)
    assert not archive.archive_capture(path, RAW, **SETTINGS)["created"]
    with pytest.raises(ValueError, match="archive full"):
        archive.archive_capture(path, RAW, **{**SETTINGS, "asset_id": "other"})
    assert archive.load_capture(path, first["capture_id"])[0] == RAW
    monkeypatch.setattr(archive, "MAX_STORAGE_BYTES", 1)
    with pytest.raises(ValueError, match="archive full"):
        archive.archive_capture(tmp_path / "small.sqlite3", RAW, **SETTINGS)
