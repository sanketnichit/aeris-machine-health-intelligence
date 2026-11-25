import pytest

from research.cwru_selective import FILES, decide, fit, assess, rank


def row(i, kind, inner, outer, ball):
    return {"file_id":i,"fault":kind,
            "median_fractions":{"envelope":{"inner":inner,"outer":outer,"ball":ball}}}


def test_abstention_reasons_and_acceptance():
    assert decide({"inner":.01,"outer":.001,"ball":.002},.01,.5)["reason"]=="weak_order_evidence"
    assert decide({"inner":.2,"outer":.2,"ball":.1},.01,0)["reason"]=="tied_orders"
    assert decide({"inner":.2,"outer":.15,"ball":.1},.01,.5)["reason"]=="competing_orders"
    assert decide({"inner":.2,"outer":.01,"ball":.01},.01,.5)["suggestion"]=="inner"
    assert decide({"inner":.2,"outer":.01,"ball":.01},.01,None)["suggestion"] is None


def test_fitting_and_held_out_error():
    dev=[row(i,"normal",.01,.005,.005) for i in range(4)]
    dev += [row(i+4,"inner",.5,.05,.05) for i in range(4)]
    dev += [row(i+8,"outer",.3,.2,.05) for i in range(12)]
    policy=fit(dev)
    assert policy["score_floor"]==.01
    assert policy["margin_threshold"]==.9
    assert policy["development_fault_assessment"]["accepted"]==4
    assert policy["development_fault_assessment"]["incorrect_accepted"]==0
    results=assess([row(99,"outer",.5,.05,.05),row(100,"inner",.1,.09,.08)],
                   policy["score_floor"],policy["margin_threshold"])
    assert results["accepted"]==1
    assert results["incorrect_accepted"]==1
    assert results["retained_error"]==1
    assert results["coverage"]==.5


def test_no_eligible_rule_and_null_risk():
    dev=[row(i,"normal",.01,.005,.005) for i in range(4)]
    dev += [row(i+4,"outer",.5,.05,.05) for i in range(16)]
    policy=fit(dev)
    assert policy["margin_threshold"] is None
    assert policy["development_fault_assessment"]["accepted"]==0
    assert policy["development_fault_assessment"]["retained_error"] is None


@pytest.mark.parametrize("fractions",[{},{"inner":1.1,"outer":0,"ball":0},
                                      {"inner":float("nan"),"outer":0,"ball":0}])
def test_invalid_inputs(fractions):
    with pytest.raises(ValueError):
        rank(fractions)


def test_frozen_evaluation_population():
    assert len(FILES)==12
    assert len({x[0] for x in FILES})==12
    assert min(x[0] for x in FILES)==209
    assert {x[2] for x in FILES}=={.021}
