import pandas as pd
import numpy as np
from research.pronostia_replication import FIT, TEST
from research.pronostia_replay import DEMO, replay


def fixture():
    return pd.DataFrame([{"bearing":b,"condition":int(b[7]),"age":a,
                          "horizontal_rms":float(1+a/5),"vertical_rms":float(2+a/5),
                          "horizontal_crest":2.,"vertical_crest":3.}
                         for b in sorted(FIT|TEST) for a in range(1,31)])


def test_replay_held_out_and_last_observation_excluded():
    report=replay(fixture(),cadence=10)
    assert set(report["fit_bearings"])==FIT
    assert {t["bearing"] for t in report["traces"]}==set(DEMO)
    for trace in report["traces"]:
        assert trace["bearing"] not in report["fit_bearings"]
        assert [p["age"] for p in trace["points"]]==[1,2,3,4,5,10,20,29]
        assert trace["last_recorded_age"]==30
        assert all(p["ratio"]>=1 for p in trace["points"])
        assert all(p["switch_2x"]==(p["learned"] if p["ratio"]>=2 else p["age_reference"]) for p in trace["points"])


def test_held_out_future_features_cannot_change_prefix():
    data=fixture()
    first=replay(data,cadence=5)
    data.loc[data.bearing.isin(DEMO)&data.age.gt(15),"horizontal_rms"]*=100
    second=replay(data,cadence=5)
    for a,b in zip(first["traces"],second["traces"]):
        assert [p for p in a["points"] if p["age"]<=15]==[p for p in b["points"] if p["age"]<=15]
