import numpy as np
import pytest

from src.order_uncertainty import interval_fractions, stable_suggestion
from research.cwru_selective import decide

CENTERS = {"inner": 118.875, "outer": 81.125, "ball": 127.82}


def test_bounds_contain_sampled_exact_fractions():
    f = np.arange(4097)*12000/8192
    rng = np.random.default_rng(42)
    p = rng.random(len(f))
    p[0] = 0
    tol = 2*12000/8192
    bounds = interval_fractions(f,p,CENTERS,(.95,1.05),tol)
    for scale in np.linspace(.95,1.05,301):
        for name,center in CENTERS.items():
            mask = np.zeros(len(f),dtype=bool)
            for h in (1,2,3):
                mask |= np.abs(f-h*center*scale)<=tol
            score = p[mask].sum()/p.sum()
            assert bounds[name]["lower"] <= score <= bounds[name]["upper"]


def test_stable_winner_implies_sampled_point_decisions():
    f = np.arange(4097)*12000/8192
    p = np.zeros_like(f)
    p[np.argmin(abs(f-CENTERS["outer"]))] = 1
    tol = 2*12000/8192
    bounds = interval_fractions(f,p,CENTERS,(.99,1.01),tol)
    result = stable_suggestion([bounds]*4,.00974446327636002,.8)
    assert result["suggestion"] == "outer"
    for s in np.linspace(.99,1.01,101):
        fractions = {}
        for k,c in CENTERS.items():
            mask = np.zeros(len(f),dtype=bool)
            for h in (1,2,3):
                mask |= abs(f-h*c*s)<=tol
            fractions[k] = float(p[mask].sum()/p.sum())
        assert decide(fractions,.00974446327636002,.8)["suggestion"] == "outer"
    broad = interval_fractions(f,p,CENTERS,(.9,1.1),tol)
    assert stable_suggestion([broad]*4,.00974446327636002,.8)["suggestion"] is None


def test_median_bounds_and_competing_upper():
    a = {"inner":{"lower":.3,"upper":.4},"outer":{"lower":.01,"upper":.05},
         "ball":{"lower":.01,"upper":.03}}
    assert stable_suggestion([a]*4,.01,.8)["suggestion"]=="inner"
    b = {**a,"outer":{"lower":.01,"upper":.1}}
    assert stable_suggestion([b]*4,.01,.8)["suggestion"] is None


@pytest.mark.parametrize("interval",[None,(1.01,1.02),(.9,float("nan")),(.9,1.6)])
def test_invalid_uncertainty_rejected(interval):
    with pytest.raises(ValueError):
        interval_fractions([0,1,2],[0,1,1],{"inner":1,"outer":1,"ball":1},interval,1)


def test_missing_or_inverted_bounds_rejected():
    with pytest.raises(ValueError):
        stable_suggestion([], .01, .8)
    with pytest.raises(ValueError):
        stable_suggestion([{"inner":{"lower":.5,"upper":.4}}], .01,.8)
