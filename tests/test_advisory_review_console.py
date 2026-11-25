
import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.advisory_review import analyze_and_record, record_review
from src.capture_archive import archive_capture


def test_optional_review_journal_renders_computed_abstention(tmp_path,monkeypatch):
    archive=tmp_path/"capture.sqlite"
    journal=tmp_path/"journal.sqlite"
    pins=tmp_path/"pins"
    pins.mkdir()
    entry=archive_capture(archive,b"horizontal,vertical\n1,2\n2,3\n3,4\n4,5\n",
                          asset_id="fixture",start="2026-06-01T00:00:00Z",
                          sample_rate_hz=12000,window_samples=4,unit="m/s2",clipping_limit=10.)
    record=analyze_and_record(journal,archive,entry["capture_id"],"a"*64,pins)
    record_review(journal,record["advisory_id"],"fixture","Inspect context")
    monkeypatch.setenv("AERIS_ADVISORY_JOURNAL_PATH",str(journal))
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio(key="research_page").set_value("Calibration decision lab").run()
    assert not app.exception
    assert app.selectbox(key="capture_review_id").value==record["advisory_id"]
    assert any("Read-only local research review journal" in w.value for w in app.warning)


def test_journal_not_created_from_dashboard(tmp_path,monkeypatch):
    path=tmp_path/"nonexistent.sqlite"
    monkeypatch.setenv("AERIS_ADVISORY_JOURNAL_PATH",str(path))
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio(key="research_page").set_value("Calibration decision lab").run()
    assert not app.exception
    assert not path.exists()
    assert any("Advisory journal integrity" in e.value for e in app.error)
