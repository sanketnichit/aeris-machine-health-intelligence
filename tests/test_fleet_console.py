from pathlib import Path
from urllib.error import URLError

from streamlit.testing.v1 import AppTest
import src.fleet_console as console


def open_fleet():
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=30).run()
    app.sidebar.radio[0].set_value("Telemetry fleet").run()
    assert not app.exception
    return app


def test_fleet_observations(monkeypatch):
    def fake(route,params=None):
        if route=="/v1/assets":
            return {"total_assets":1,"truncated":False,"assets":[
                {"asset_id":"demo","name":"Demo","observations":1,"quality":"incomplete",
                 "latest_timestamp":"2026-11-24T12:00:00Z","missing_latest":["vertical_vibration_rms"],
                 "expected_measurements":["horizontal_vibration_rms","vertical_vibration_rms"]}]}
        return {"records":[{"timestamp":"2026-11-24T12:00:00Z",
                "measurements":{"horizontal_vibration_rms":{"value":1.25,"unit":"m/s2"}}}]}
    monkeypatch.setattr(console,"fetch",fake)
    app=open_fleet()
    metrics={m.label:m.value for m in app.metric}
    assert int(metrics["Registered assets"])==1
    assert int(metrics["Complete latest records"])==0
    assert app.selectbox(key="fleet_signal").value=="horizontal_vibration_rms"


def test_fleet_api_unavailable(monkeypatch):
    def fail(*args,**kwargs):
        raise URLError("offline")
    monkeypatch.setattr(console,"fetch",fail)
    app=open_fleet()
    assert any("API unavailable" in i.value for i in app.info)
