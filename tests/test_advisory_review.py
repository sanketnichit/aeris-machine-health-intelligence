import sqlite3

import pytest

from src.capture_archive import archive_capture
from src.advisory_review import analyze_and_record, list_advisories, record_review


@pytest.fixture
def inputs(tmp_path):
    archive=tmp_path/"capture.sqlite"
    raw=b"horizontal,vertical\n1,2\n2,3\n3,4\n4,5\n"
    entry=archive_capture(archive,raw,asset_id="fixture",start="2026-06-01T00:00:00Z",
                          sample_rate_hz=12000,window_samples=4,unit="m/s2",clipping_limit=10.)
    pins=tmp_path/"pins"
    pins.mkdir()
    return tmp_path/"journal.sqlite",archive,entry["capture_id"],"a"*64,pins


def test_computed_abstention_is_retained_and_deduplicated(inputs):
    first=analyze_and_record(*inputs)
    second=analyze_and_record(*inputs)
    assert first["created"] and not second["created"]
    assert first["advisory_id"]==second["advisory_id"]
    rows=list_advisories(inputs[0])
    assert len(rows)==1 and rows[0]["review_status"]=="pending"
    assert rows[0]["report"]["suggestion"] is None
    assert rows[0]["report"]["reason"]=="measurement_context_unverified"
    assert not rows[0]["report"]["operational_authorization"]


def test_review_is_one_time_and_does_not_change_advisory(inputs):
    first=analyze_and_record(*inputs)
    ident=first["advisory_id"]
    result=record_review(inputs[0],ident,"fixture reviewer","Missing measurement context; request evidence.")
    assert not result["operational_authorization"]
    row=list_advisories(inputs[0])[0]
    assert row["review_status"]=="reviewed" and row["report"]==first["report"]
    with pytest.raises(ValueError,match="already reviewed"):
        record_review(inputs[0],ident,"another","Do not overwrite")


def test_tampered_report_blocks_read_and_review(inputs):
    first=analyze_and_record(*inputs)
    with sqlite3.connect(inputs[0]) as db:
        db.execute("UPDATE advisories SET report=?",(b"{}",))
    with pytest.raises(ValueError,match="fingerprint"):
        list_advisories(inputs[0])
    with pytest.raises(ValueError,match="fingerprint"):
        record_review(inputs[0],first["advisory_id"],"reviewer","test")


def test_journal_cannot_be_capture_archive(inputs):
    _,archive,capture,context,pins=inputs
    with pytest.raises(ValueError,match="separate"):
        analyze_and_record(archive,archive,capture,context,pins)
