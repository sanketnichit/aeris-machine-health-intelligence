import numpy as np
import pytest

import research.order_counterexamples as audit


def fixture():
    f = np.arange(151, dtype=float)
    p = np.zeros_like(f)
    p[10] = 1.
    return f, [p], {"outer": 10., "inner": 40., "ball": 45.}


def test_witness_is_inside_interval_and_changes_decision():
    f, p, c = fixture()
    out = audit.search_counterexample(f, p, c, (.9, 1.1), .1, .5, .8)
    assert out["status"] == "point_counterexample"
    assert .9 <= out["witness_scale"] <= 1.1
    assert out["nominal"]["suggestion"] == "outer"
    assert out["witness_decision"]["suggestion"] is None


def test_no_witness_does_not_issue_certificate():
    f, p, c = fixture()
    out = audit.search_counterexample(f, p, c, (.99, 1.01), 1.1, .5, .8)
    assert out["status"] == "no_witness_found"
    assert "suggestion" not in out
    assert out["points_checked"] > 1


def test_nominal_abstention_is_distinct():
    f, p, c = fixture()
    p[0][150] = 1.
    out = audit.search_counterexample(f, p, c, (.9, 1.1), .1, .75, .8)
    assert out["status"] == "nominal_abstention"


def test_budget_cannot_be_mistaken_for_stability(monkeypatch):
    f, p, c = fixture()
    monkeypatch.setattr(audit, "breakpoint_partition", lambda *args: None)
    out = audit.search_counterexample(f, p, c, (.9, 1.1), .1, .5, .8)
    assert out["status"] == "partition_budget_exceeded"


def test_invalid_spectrum_rejected():
    f, p, c = fixture()
    p[0][0] = 1.
    with pytest.raises(ValueError):
        audit.search_counterexample(f, p, c, (.9, 1.1), .1, .5, .8)
