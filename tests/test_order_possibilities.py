import numpy as np
import pytest

import src.order_possibilities as op
from research.cwru_selective import decide


def example():
    f = np.arange(151, dtype=float)
    p = np.zeros_like(f)
    p[9:12] = 1
    return f, p, {"outer": 10., "inner": 40., "ball": 45.}


def test_unique_possible_is_not_a_diagnosis():
    f, p, c = example()
    result = op.possible_suggestions(f, [p], c, (.9, 1.1), 1.1, .5, .8)
    assert result["possible_suggestions"] == ["outer"]
    assert "suggestion" not in result


def test_budget_fallback_preserves_global_outer_set(monkeypatch):
    f, p, c = example()
    monkeypatch.setattr(op, "breakpoint_partition", lambda *a: None)
    result = op.possible_suggestions(f, [p], c, (.9, 1.1), 1.1, .5, .8)
    assert result["possible_suggestions"] == result["global_possible"]
    assert "outer" in result["possible_suggestions"]
    assert result["reason"] == "global_fallback_budget"


def test_weak_evidence_can_exclude_all_labels():
    f, p, c = example()
    p[:] = 0
    p[149] = 1
    result = op.possible_suggestions(f, [p], c, (.99, 1.01), .1, .5, .8)
    assert result["possible_suggestions"] == []


def test_sampled_accepted_suggestions_are_contained():
    f, _, c = example()
    rng = np.random.default_rng(273)
    for _ in range(8):
        p = rng.random((3, len(f)))
        p[:, 0] = 0
        result = op.possible_suggestions(f, list(p), c, (.9, 1.1), 1.1, .02, .1)
        assert set(result["possible_suggestions"]) <= set(result["global_possible"])
        for s in np.linspace(.9, 1.1, 101):
            fractions = {}
            for k, center in c.items():
                mask = np.zeros(len(f), dtype=bool)
                for h in (1, 2, 3):
                    mask |= abs(f-h*(center*s)) <= 1.1
                fractions[k] = float(np.median(p[:, mask].sum(axis=1)/p.sum(axis=1)))
            label = decide(fractions, .02, .1)["suggestion"]
            if label is not None:
                assert label in result["possible_suggestions"]


def test_invalid_spectrum_is_rejected():
    f, p, c = example()
    with pytest.raises(ValueError):
        op.possible_suggestions(f, [p*0], c, (.9, 1.1), 1.1, .5, .8)
