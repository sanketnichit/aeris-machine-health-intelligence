from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.calibration_console import demo_advisory


def test_synthetic_advisory_fail_closed():
    for scenario in ("Missing","Expired","Altered enrollment"):
        result=demo_advisory(0.,0.,.01,scenario)
        assert result["suggestion"] is None
        assert result["next_action"]=="obtain_applicable_calibration_evidence"
        assert not result["operational_authorization"]


def test_synthetic_advisory_conflict():
    result=demo_advisory(-.05,.05,.05,"Consistent")
    assert result["suggestion"] is None
    assert result["next_action"]=="reconcile_measurement_conflict"


def test_calibration_lab_navigation_and_missing_record():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio(key="research_page").set_value("Calibration decision lab").run()
    assert not app.exception
    app.radio(key="cal_record").set_value("Missing").run()
    assert not app.exception
    assert any(m.label=="Research suggestion" and m.value=="Withheld" for m in app.metric)
