import copy

import pytest

from research.cmapss_paired_analysis import paired_analysis


def records():
    return [
        dict(unit=unit, stage=stage, fold=unit % 2, model=model, actual=10.,
             predicted=10.+error)
        for unit in range(1, 5)
        for stage in (.25, .75)
        for model, error in (("age_conditioned", 3.), ("candidate", 1.))
    ]


def test_paired_bootstrap_constant_difference():
    result = paired_analysis(records(), draws=200)
    candidate = result["comparisons"]["candidate"]
    assert result["engines"] == 4
    assert candidate["engine_weighted_mae_delta"] == -2.
    assert candidate["percentile_95_interval"] == [-2., -2.]
    assert candidate["engine_win_fraction"] == 1.
    assert result == paired_analysis(records(), draws=200)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "truth", "fold"])
def test_reject_invalid_pairing(mutation):
    data = copy.deepcopy(records())
    if mutation == "duplicate":
        data.append(data[0])
    elif mutation == "missing":
        data.pop()
    elif mutation == "truth":
        data[0]["actual"] = 11.
    elif mutation == "fold":
        data[0]["fold"] = 10
    with pytest.raises(ValueError):
        paired_analysis(data, draws=200)
