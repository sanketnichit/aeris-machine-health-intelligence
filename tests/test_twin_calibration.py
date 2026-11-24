import numpy as np
import pandas as pd
import pytest

from research.pronostia_replication import FIT, TEST
from research.twin_calibration import evaluate, weighted_quantile, states


def fixture():
    return pd.DataFrame([{"bearing":b,"condition":int(b[7]),"age":a,
                          "horizontal_rms":float(np.exp(a/100)),
                          "vertical_rms":float(np.exp(a/200))}
                         for b in sorted(FIT|TEST) for a in range(1,121)])


def test_weighted_quantiles():
    assert weighted_quantile([0,1,2],[10,1,1],.5)==0
    with pytest.raises(ValueError):
        weighted_quantile([1],[0],.5)


def test_frozen_population_and_bounds():
    result=evaluate(fixture(),landmarks=(50,100))
    assert set(result["fit"]["fit_bearings"])==FIT
    assert set(result["evaluation_bearings"])==TEST
    assert result["summary"]["all"]["condition_drift"]["endpoints"]==22
    assert result["summary"]["all"]["condition_drift"]["mae"]<1e-10
    assert all(0<=p["lower"]<=p["upper"] for p in result["predictions"])


def test_held_out_future_cannot_change_fits_or_forecasts():
    data=fixture()
    original=evaluate(data,landmarks=(50,100))
    data.loc[data.bearing.isin(TEST)&data.age.gt(50),"horizontal_rms"]*=2
    modified=evaluate(data,landmarks=(50,100))
    assert original["fit"]==modified["fit"]
    assert original["condition_fit"]==modified["condition_fit"]
    a=[p for p in original["predictions"] if p["age"]==50]
    b=[p for p in modified["predictions"] if p["age"]==50]
    for first,second in zip(a,b):
        assert {k:v for k,v in first.items() if k!="actual"}=={k:v for k,v in second.items() if k!="actual"}


def test_invalid_history():
    data=fixture()
    with pytest.raises(ValueError,match="Noncontiguous"):
        states(data.drop(index=10))
