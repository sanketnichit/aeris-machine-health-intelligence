from research.technical_report import generate_report
from research.verify_evidence import verify


def test_report_is_deterministic_and_traceable():
    report=generate_report()
    assert report==generate_report()
    for row in verify():
        assert row["file"] in report
        assert row["run_url"] in report
        assert row["revision"] in report
        assert row["blob_sha"] in report
    assert "17.346" in report
    assert "508.888" in report
    assert "did not replicate" in report
    assert "No forecasts were accepted" in report
    assert "Hypothetical cost units only" in report
