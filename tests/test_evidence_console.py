from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.evidence_console import maintenance_table, read_report


@pytest.mark.parametrize("ratio", [5,10,25])
def test_verified_replay_table(ratio):
    report = read_report("maintenance_summary.json")
    table = maintenance_table(report,ratio)
    assert len(table)==13
    assert table.Cost.is_monotonic_increasing
    assert (table.Planned + table.Late + table.Missed).eq(100).all()
    baseline = table.loc[table.Model=="run_to_failure"].iloc[0]
    assert baseline.Cost==100*ratio


def test_research_workspace_renders_without_dataset():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30)
    app.run()
    assert not app.exception
    assert app.sidebar.radio[0].value=="Research intelligence"
    assert any("Research Intelligence" in t.value for t in app.title)
    assert not app.select_slider
    app.sidebar.radio(key="research_page").set_value("Maintenance replay").run()
    app.select_slider[0].set_value(25).run()
    assert not app.exception


def test_published_telemetry_and_truth_toggle():
    report = read_report("telemetry.json")
    assert sum(len(t["points"]) for t in report["traces"]) == 655
    for trace in report["traces"]:
        assert trace["unit"] not in trace["fit_units"]
        assert trace["points"][-1]["cycle"] == trace["failure_cycle"]-1
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio(key="research_page").set_value("Temporal replay").run()
    assert not any(m.label=="Actual remaining cycles" for m in app.metric)
    app.slider(key="replay_cycle_1").set_value(10).run()
    assert not app.exception
    app.checkbox(key="replay_truth_1").set_value(True).run()
    assert not app.exception
    metric=next(m for m in app.metric if m.label=="Actual remaining cycles")
    assert int(metric.value)==182


def test_bearing_comparison_preserves_models_and_units():
    from src.evidence_console import bearing_comparison
    report = {"summary": {"condition": {
        "age_reference": {"by_bearing": {"Bearing1_1": {"mae": 8., "rmse": 9., "endpoints": 4}}},
        "learned": {"by_bearing": {"Bearing1_1": {"mae": 5., "rmse": 6., "endpoints": 4}}},
    }}}
    table = bearing_comparison(report, "condition")
    assert table.Model.tolist() == ["age_reference", "learned"]
    assert table.MAE.tolist() == [8., 5.]
    assert table.Endpoints.tolist() == [4, 4]
    with pytest.raises(ValueError):
        bearing_comparison(report, "invalid")


def test_published_physical_evidence_workspace():
    report=read_report("xjtu_summary.json")
    assert len(report["snapshot_counts"])==15
    assert sum(report["snapshot_counts"].values())==9216
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio(key="research_page").set_value("Physical bearings").run()
    assert any(m.label=="Vibration snapshots" and int(m.value)==9216 for m in app.metric)
    app.radio(key="bearing_split").set_value("condition").run()
    assert not app.exception
    app.radio(key="bearing_detail").set_value("by_stage").run()
    assert not app.exception


def test_adaptive_reliability_workspace_reports_zero_acceptance():
    gate=read_report("xjtu_gate_summary.json")
    review=read_report("xjtu_reliability_summary.json")
    assert gate["summary"]["bearing"]["stage"]["all"]["switch_2x"]["mae"] < gate["summary"]["bearing"]["stage"]["all"]["learned"]["mae"]
    for split in ("bearing","condition"):
        assert sum(v["endpoints"] for v in review["summary"][split].values())==56
        assert all(v["accepted"]==0 and v["retained_mae"] is None for v in review["summary"][split].values())
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio(key="research_page").set_value("Adaptive reliability").run()
    app.radio(key="reliability_split").set_value("condition").run()
    assert not app.exception
    assert any(m.label=="Accepted forecasts" and int(m.value)==0 for m in app.metric)


def test_console_verifies_evidence_before_rendering(monkeypatch):
    import src.evidence_console as console
    def reject(_):
        raise ValueError("test fingerprint mismatch")
    monkeypatch.setattr(console,"verify",reject)
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    assert any("Research evidence integrity check failed" in e.value for e in app.error)
    assert not any(r.key=="research_page" for r in app.sidebar.radio)


def test_independent_replication_workspace():
    report=read_report("pronostia_summary.json")
    assert len(report["fit_bearings"])==6
    assert len(report["evaluation_bearings"])==11
    assert not set(report["fit_bearings"]) & set(report["evaluation_bearings"])
    assert report["primary"]=="switch_2x"
    assert report["summary"]["stage"]["all"]["switch_2x"]["endpoints"]==44
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio(key="research_page").set_value("Independent replication").run()
    assert any(m.label=="Evaluation bearings" and int(m.value)==11 for m in app.metric)
    app.radio(key="replication_breakdown").set_value("landmark").run()
    assert not app.exception


def test_command_center_uses_published_evidence():
    official=read_report("official_summary.json")
    xjtu=read_report("xjtu_summary.json")
    pronostia=read_report("pronostia_summary.json")
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    metrics={m.label:m.value for m in app.metric}
    assert int(metrics["Official NASA engines"])==official["engines"]
    assert int(metrics["Physical bearing histories"])==len(xjtu["snapshot_counts"])+len(pronostia["snapshot_counts"])
    assert int(metrics["Physical vibration recordings"].replace(",",""))==sum(xjtu["snapshot_counts"].values())+sum(pronostia["snapshot_counts"].values())
    assert any("0/112 advisory forecasts" in w.value for w in app.warning)
    assert any("did not outperform" in w.value for w in app.warning)


def test_technical_report_page_renders_on_demand():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio(key="research_page").set_value("Technical report").run()
    assert not app.exception
    assert any("Technical evidence report" in t.value for t in app.subheader)
    assert any("did not replicate" in m.value for m in app.markdown)
