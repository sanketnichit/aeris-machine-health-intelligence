from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_virtual_laboratory_renders():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio[0].set_value("Virtual degradation laboratory").run()
    assert not app.exception
    assert any("Paired maintenance comparison" in t.value for t in app.subheader)
    assert any("Synthetic digital-twin prototype" in w.value for w in app.warning)
    assert app.selectbox(key="twin_trace").value=="reactive"
    assert any(m.label=="Held-out endpoints" and int(m.value)==54 for m in app.metric)
    assert any("does not establish superiority" in w.value for w in app.warning)
