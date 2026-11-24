from datetime import datetime, timedelta, timezone
import json
import threading
from urllib.request import urlopen

from src.api import make_server
from src.anomaly import deviation_series
from src.decision_engine import assess_asset, benchmark_context
from src.incidents import configure_freshness
from src.telemetry_store import initialize, register, ingest, configure_policy

NOW=datetime(2026,1,1,12,tzinfo=timezone.utc)
SIGNAL="horizontal_vibration_rms"


def setup(tmp_path):
    db=tmp_path/"telemetry.sqlite3"
    initialize(db)
    register(db,{"asset_id":"a","name":"Test","expected_measurements":[SIGNAL]})
    configure_freshness(db,"a",60)
    return db


def payload(values, start=NOW-timedelta(seconds=30)):
    return {"schema_version":1,"records":[{"asset_id":"a","timestamp":(start+timedelta(seconds=i)).isoformat(),
        "measurements":{SIGNAL:{"value":v,"unit":"m/s2"}}} for i,v in enumerate(values)]}


def withheld(result):
    assert result["forecast"]["status"]=="withheld"
    assert result["forecast"]["remaining_life"] is None
    assert result["forecast"]["failure_probability"] is None
    assert result["forecast"]["model_disagreement"] is None
    assert result["forecast"]["calibrated_interval"] is None


def test_no_data_and_stale_data(tmp_path):
    db=setup(tmp_path)
    result=assess_asset(db,"a",NOW)
    assert result["status"]=="insufficient_evidence"
    assert any(r["code"]=="no_observations" for r in result["data_reasons"])
    withheld(result)
    ingest(db,payload([1,2,3]*7))
    result=assess_asset(db,"a",NOW+timedelta(minutes=5))
    assert any(r["code"]=="stale_observation" for r in result["data_reasons"])
    withheld(result)


def test_review_priority_and_healthy_claim_prevented(tmp_path):
    db=setup(tmp_path)
    ingest(db,payload([1,2,3]*7))
    result=assess_asset(db,"a",NOW)
    assert result["status"]=="no_current_rule_trigger"
    withheld(result)
    configure_policy(db,"a",{"bounds":{SIGNAL:{"max":3}}})
    ingest(db,payload([20],NOW))
    result=assess_asset(db,"a",NOW)
    assert result["status"]=="review_required"
    codes={r["code"] for r in result["review_reasons"]}
    assert {"configured_bound_breach","exploratory_deviation","active_review_incident"}<=codes
    withheld(result)


def test_future_and_extreme_values(tmp_path):
    db=setup(tmp_path)
    ingest(db,payload([1e308]*12,NOW+timedelta(seconds=10)))
    result=assess_asset(db,"a",NOW)
    assert any(r["code"]=="future_timestamp" for r in result["data_reasons"])
    assert result["deviations"][SIGNAL]["score"] is None
    json.dumps(result,allow_nan=False)
    withheld(result)


def test_registered_benchmark_context():
    context=benchmark_context()
    reliability=context["xjtu_reliability"]
    assert reliability["accepted"]==0 and reliability["assessments"]==112
    assert reliability["finite_90_percent_intervals"]==0
    replication=context["pronostia_replication"]
    assert replication["primary_mae"]>replication["learned_mae"]


def test_advisory_http(tmp_path):
    db=setup(tmp_path)
    server=make_server(port=0,database=db)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/v1/advisory?asset_id=a",timeout=5) as response:
            report=json.load(response)
        assert report["asset_id"]=="a"
        assert report["benchmark_context"]["xjtu_reliability"]["accepted"]==0
        withheld(report)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
