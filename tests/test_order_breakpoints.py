import numpy as np

import src.order_breakpoints as bp
from src.order_uncertainty import interval_fractions, stable_suggestion
from research.cwru_selective import decide


def example():
    f = np.arange(151,dtype=float)
    p = np.zeros_like(f)
    p[9:12] = 1
    centers = {"outer":10., "inner":40., "ball":45.}
    return f,p,centers


def test_partition_covers_closed_interval_without_gaps():
    f,p,c = example()
    cells = bp.breakpoint_partition(f,c,(.9,1.1),1.1)
    assert cells[0][0] == .9
    assert cells[-1][1] == 1.1
    assert all(a <= b for a,b in cells)
    assert all(a[1] == b[0] for a,b in zip(cells,cells[1:]))


def test_recovers_stable_winner_when_global_bounds_are_loose():
    f,p,c = example()
    broad = interval_fractions(f,p,c,(.9,1.1),1.1)
    assert stable_suggestion([broad],.5,.8)["suggestion"] is None
    result = bp.verify_breakpoints(f,[p],c,(.9,1.1),1.1,.5,.8)
    assert result["suggestion"] == "outer"
    assert result["cells_checked"] == result["cell_count"] > 0
    for s in np.linspace(.9,1.1,1001):
        fractions = {}
        for k,center in c.items():
            mask = np.zeros(len(f),dtype=bool)
            for h in (1,2,3):
                mask |= abs(f-h*center*s)<=1.1
            fractions[k] = float(p[mask].sum()/p.sum())
        assert decide(fractions,.5,.8)["suggestion"]=="outer"


def test_abstains_when_stability_not_established():
    f,p,c = example()
    result=bp.verify_breakpoints(f,[p],c,(.9,1.1),.1,.5,.8)
    assert result["suggestion"] is None
    assert result["reason"]=="cell_stability_not_established"


def test_complexity_limit_abstains_not_sparse_samples(monkeypatch):
    f,p,c = example()
    monkeypatch.setattr(bp,"MAX_CELLS",1)
    result=bp.verify_breakpoints(f,[p],c,(.9,1.1),1.1,.5,.8)
    assert result["suggestion"] is None
    assert result["reason"]=="partition_budget_exceeded"


def test_preserves_global_sufficient_winner():
    f,p,c=example()
    result=bp.verify_breakpoints(f,[p],c,(1.,1.),1.1,.5,.8)
    assert result["suggestion"]=="outer"
    assert result["reason"]=="global_bound_sufficient"
