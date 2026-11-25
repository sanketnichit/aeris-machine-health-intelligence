from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.evidence_console import read_report
from src.paderborn_console import timebase_rows


def test_registered_timebase_is_structural_only():
    rows=timebase_rows(read_report("paderborn_timebase_summary.json"))
    assert len(rows)==12
    assert rows["Raster/count/index consistent"].all()
    assert not rows["Diagnostic eligible"].any()
    assert not rows["Physical clock verified"].any()
    assert rows["Max relative step deviation"].min()>.05
    assert rows["Max relative step deviation"].max()>3


def test_paderborn_workspace_renders_verified_evidence():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio(key="research_page").set_value("Paderborn acquisition").run()
    assert not app.exception
    assert any(m.label=="Internally consistent channel links" and m.value=="12" for m in app.metric)
    assert any("remains blocked" in w.value for w in app.warning)
