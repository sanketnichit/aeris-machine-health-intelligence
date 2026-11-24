from threading import Event

import pytest

from src.anomaly import deviation_series
from src.monitor_worker import run_worker


def points(values):
    return [{"timestamp":str(i),"measurements":{} if v is None else {"signal":{"value":v}}}
            for i,v in enumerate(values)]


def test_deviation_uses_only_prior_observations():
    records=points([1,2,3,20,None,4,100])
    result=deviation_series(records,"signal",window=3,minimum=3)
    assert result[3]["baseline"]==2
    assert result[3]["score"]==pytest.approx(18/1.4826)
    assert result[4]["status"]=="missing_measurement"
    assert result[:5]==deviation_series(records[:5],"signal",window=3,minimum=3)
    assert all(r["score"] is None for r in result[:3])


def test_constant_baseline_abstains():
    result=deviation_series(points([2,2,2,100]),"signal",window=3,minimum=3)
    assert result[-1]["status"]=="unstable_scale"
    assert result[-1]["score"] is None


def test_worker_once_and_stop(tmp_path):
    calls=[]
    db=tmp_path/"telemetry.sqlite3"
    def scan(path):
        calls.append(path)
        return {"scanned_assets":0}
    run_worker(db,once=True,scan=scan)
    assert calls==[db]
    stop=Event()
    def stopping_scan(path):
        calls.append(path)
        stop.set()
        return {"scanned_assets":0}
    run_worker(db,interval=1,stop=stop,scan=stopping_scan)
    assert calls==[db,db]
    with pytest.raises(ValueError):
        run_worker(db,interval=0,once=True)
