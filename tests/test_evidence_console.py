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
