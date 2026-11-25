import numpy as np
import pytest

from research.mfpt_robustness import SCENARIOS, WINDOW, RATE, perturb, summarize, evaluate_record
from research.mfpt_transfer import WINDOWS

CENTERS = {"inner":118.875,"outer":81.125,"ball":127.82}


def signal():
    t=np.arange(WINDOW)/RATE
    return (1+.5*np.cos(2*np.pi*CENTERS["outer"]*t))*np.sin(2*np.pi*3000*t)


def test_paired_noise_exact_snr():
    x=signal()
    a,_,q=perturb(x,CENTERS,("noise_db",20),42)
    b,_,_=perturb(x,CENTERS,("noise_db",0),42)
    assert np.allclose(b-x,10*(a-x))
    assert 10*np.log10(np.var(x)/np.var(a-x))==pytest.approx(20)
    assert not q["flags"]
    assert len(SCENARIOS)==14


def test_metadata_errors_preserve_waveform():
    x=signal()
    y,f,q=perturb(x,CENTERS,("speed_error",.05),42)
    assert np.array_equal(x,y)
    assert f["inner"]==pytest.approx(CENTERS["inner"]*1.05)
    assert not q["flags"]
    y,f,q=perturb(x,CENTERS,("clock_error",-.01),42)
    assert np.array_equal(x,y)
    assert f["inner"]==pytest.approx(CENTERS["inner"]/.99)


def test_explicit_missing_and_clipping():
    x=signal()
    y,_,q=perturb(x,CENTERS,("missing",.1),42)
    n=int(WINDOW*.1)
    assert np.all(y[WINDOW//4:WINDOW//4+n]==0)
    assert q["affected_fraction"]==n/WINDOW
    assert q["flags"]==["declared_missing_samples"]
    y,_,q=perturb(x,CENTERS,("clip_rms",.5),42)
    assert np.max(np.abs(y-x.mean()))<=.5*np.std(x)+1e-12
    assert q["flags"]==["declared_clipping_limit_reached"]


def test_gate_preserves_ungated_evidence_and_withholds():
    x=np.tile(signal(),WINDOWS)
    clean=evaluate_record(x,CENTERS,("clean",0),0,"demo","outer")
    assert clean["ungated"]["suggestion"]=="outer"
    assert clean["gated"]==clean["ungated"]
    damaged=evaluate_record(x,CENTERS,("missing",.01),0,"demo","outer")
    assert damaged["gated"]["suggestion"] is None
    assert damaged["gated"]["reason"]=="explicit_quality_metadata"
    summary=summarize([damaged],"gated")
    assert summary["coverage"]==0
    assert summary["retained_error"] is None


def test_guard_does_not_count_abstention_as_correct():
    rows=[{"truth":"inner","ungated":{"candidate":"outer","suggestion":"outer"},
           "gated":{"suggestion":None}},
          {"truth":"normal","ungated":{"candidate":"inner","suggestion":"inner"},
           "gated":{"suggestion":None}}]
    a=summarize(rows,"ungated")
    b=summarize(rows,"gated")
    assert a["incorrect_accepted"]==a["normal_incorrect_accepted"]==1
    assert b["correct_accepted"]==b["incorrect_accepted"]==b["normal_incorrect_accepted"]==0
    assert b["abstained"]==1
