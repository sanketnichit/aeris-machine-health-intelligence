import numpy as np
import pandas as pd
import pytest
from src.prognostics import COLUMNS
from src.regime_prognostics import RegimeFeatures, finite_radius, forecast_gate
from research.cmapss_regime_development import split_units, summarize


def frame(n=50,cycles=8):
    return pd.DataFrame([[u,t,float(t%2)*10,0.,0.]+[float(u+t+j) for j in range(21)]
                         for u in range(1,n+1) for t in range(1,cycles+1)],columns=COLUMNS)


def test_split_is_unit_disjoint():
    f=frame()
    s=split_units(f)
    assert len(s["fit"])==30 and len(s["calibration"])==len(s["evaluation"])==10
    assert len(set(sum(s.values(),[])))==50


def test_transform_is_prefix_causal():
    f=frame(3)
    model=RegimeFeatures(2).fit(f)
    full,d=model.transform(f)
    early=f[f.cycle<=4].reset_index(drop=True)
    prefix,p=model.transform(early)
    np.testing.assert_allclose(full.loc[f.cycle<=4].to_numpy(),prefix.to_numpy())
    np.testing.assert_allclose(d[f.cycle<=4],p)


def test_settings_shift_detectable():
    f=frame(3)
    model=RegimeFeatures(2).fit(f)
    _,normal=model.transform(f)
    shifted=f.copy()
    shifted["setting_1"]+=100
    _,outside=model.transform(shifted)
    assert outside.min()>normal.max()


def test_finite_radius_needs_nine_units():
    assert finite_radius(np.arange(8)) is None
    assert finite_radius(np.arange(9))==8


@pytest.mark.parametrize("args,reason",[
    ((20,0,1,2,False),"declared_domain_mismatch"),
    ((20,0,None,2,True),"insufficient_calibration"),
    ((20,2,1,2,True),"settings_outside_calibrated_support"),
    ((100,0,1,50,True),"interval_too_wide")])
def test_gate_withholds(args,reason):
    p,d,s,i,match=args
    result=forecast_gate(p,d,s,i,domain_matches=match)
    assert result["reason"]==reason and result["forecast"] is None
    assert result["interval"] is None and not result["operational_authorization"]


def test_conditional_forecast_never_authorizes_operation():
    result=forecast_gate(5,0,1,10,domain_matches=True)
    assert result["interval"]==[0.,15.] and result["forecast"]==5
    assert not result["operational_authorization"]


def test_empty_selection_has_undefined_error():
    assert summarize([])["accepted_mae"] is None
