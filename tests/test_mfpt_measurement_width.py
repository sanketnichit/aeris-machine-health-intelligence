import pytest

from research.mfpt_measurement_width import WIDTHS, profile


def test_grid_includes_frozen_widths():
    assert tuple(sorted(set(WIDTHS))) == WIDTHS
    assert .01 in WIDTHS and .05 in WIDTHS


def test_precise_but_biased_is_not_correct():
    out = profile((.001,.005,.01), ("inner","inner",None), .01, "outer")
    assert out["largest_tested_accepted_width"] == .005
    assert out["largest_tested_correct_width"] is None
    assert out["accepted_without_reference"] == 2
    assert out["incorrect_accepted_widths"] == [.001,.005]


def test_no_interpolation_or_monotonicity_assumption():
    out = profile((.001,.005,.01), (None,"outer",None), 0., "outer")
    assert out["largest_tested_correct_width"] == .005
    assert out["narrower_unresolved"] == 1


def test_all_abstentions():
    out = profile((.001,.005), (None,None), 0., "outer")
    assert out["largest_tested_accepted_width"] is None
    assert out["accepted_without_reference"] == 0


def test_conflicting_nested_winners_rejected():
    with pytest.raises(ValueError, match="Conflicting"):
        profile((.001,.005), ("inner","outer"), 0., "outer")


def test_reference_containment_boundary():
    out = profile((.005,.01), ("outer","outer"), .01, "outer")
    assert out["accepted_without_reference"] == 1
