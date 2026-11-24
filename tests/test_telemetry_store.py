import pytest

from src.telemetry_store import initialize, register, ingest, fleet, history, Conflict, UnknownAsset


def asset():
    return {"asset_id":"bearing-1","name":"Bearing one",
            "expected_measurements":["horizontal_vibration_rms","vertical_vibration_rms"]}


def batch(stamp="2026-11-24T12:00:00Z",value=1.25,asset_id="bearing-1"):
    return {"schema_version":1,"records":[{"asset_id":asset_id,"timestamp":stamp,
        "measurements":{"horizontal_vibration_rms":{"value":value,"unit":"m/s2"}}}]}


@pytest.fixture
def db(tmp_path):
    path=tmp_path/"telemetry.sqlite3"
    initialize(path)
    return path


def test_registration_and_persistence(db):
    assert register(db,asset())["created"]
    assert not register(db,asset())["created"]
    assert fleet(db)["assets"][0]["quality"]=="no_data"
    assert ingest(db,batch())["inserted"]==1
    initialize(db)
    assert len(history(db,"bearing-1"))==1
    assert fleet(db)["assets"][0]["missing_latest"]==["vertical_vibration_rms"]
    assert fleet(db)["assets"][0]["quality"]=="incomplete"
    assert ingest(db,batch("2026-11-24T17:30:00+05:30"))["duplicates"]==1
    with pytest.raises(Conflict):
        ingest(db,batch(value=3))
    assert len(history(db,"bearing-1"))==1


def test_atomic_batch_and_out_of_order_history(db):
    register(db,asset())
    mixed=batch()
    mixed["records"]+=batch(asset_id="unknown")["records"]
    with pytest.raises(UnknownAsset):
        ingest(db,mixed)
    assert history(db,"bearing-1")==[]
    ingest(db,batch("2026-11-24T12:00:00.5Z"))
    ingest(db,batch("2026-11-24T12:00:00Z"))
    assert [r["timestamp"] for r in history(db,"bearing-1")]==[
        "2026-11-24T12:00:00.000000Z","2026-11-24T12:00:00.500000Z"]
    assert len(history(db,"bearing-1",1))==1


def test_asset_metadata_conflict_and_complete_record(db):
    register(db,asset())
    with pytest.raises(Conflict):
        register(db,{**asset(),"name":"Different"})
    data=batch()
    data["records"][0]["measurements"]["vertical_vibration_rms"]={"value":2,"unit":"m/s2"}
    ingest(db,data)
    assert fleet(db)["assets"][0]["quality"]=="complete"
