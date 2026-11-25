from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.multiregime_console import endpoint_rows
from research.verify_evidence import verify


def test_endpoint_table_distinguishes_training_modes():
    metrics={"mae":2.,"rmse":3.,"nasa_score":4.,"mean_signed_error":1.,"overprediction_gt20_fraction":0.}
    report={"scenarios":[{"subset":"FD002","mode":m,"test_engines":259,"metrics":{"relative_hgb":metrics}}
                         for m in ("fd001_transfer","within_subset")]}
    rows=endpoint_rows(report,"FD002")
    assert rows["Test engines"].tolist()==[259,259]
    assert rows["Training mode"].tolist()==["fd001_transfer","within_subset"]


def test_nasa_research_page_never_fits_models():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio(key="research_page").set_value("NASA multi-regime evaluation").run()
    assert not app.exception
    names={r["file"] for r in verify()}
    if "cmapss_multiregime_summary.json" not in names:
        assert any("not yet registered" in i.value for i in app.info)
    else:
        assert any(m.label=="Distinct official endpoints" and m.value=="707" for m in app.metric)
        app.selectbox(key="cmapss_multiregime_subset").set_value("FD004").run()
        assert not app.exception
