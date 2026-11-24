import numpy as np
import pandas as pd
import pytest

from research.cmapss_uncertainty import partition_units, prefix_endpoints, support_scores, selective_summary, run
from src.prognostics import COLUMNS


def test_partitions_are_disjoint_and_reproducible():
    ids = np.arange(1, 101)
    groups = partition_units(ids)
    assert [len(g) for g in groups] == [60, 20, 20]
    assert len(np.unique(np.concatenate(groups))) == 100
    for a, b in zip(groups, partition_units(ids)):
        np.testing.assert_array_equal(a, b)
    with pytest.raises(ValueError):
        partition_units(np.arange(44))


def test_support_and_empty_retention():
    train = pd.DataFrame({"x": [0., 10.], "constant": [2., 2.]})
    test = pd.DataFrame({"x": [5., 15., 5.], "constant": [2., 2., 3.]})
    support = support_scores(train, test)
    np.testing.assert_allclose(support, [0., .5, np.inf])
    actual = np.array([5., 10., 15.])
    pred = np.array([4., 7., 1.])
    assert selective_summary(actual, pred, support, 0.)["retained_mae"] == 1.
    assert selective_summary(actual, pred, support, -1.)["retained_mae"] is None


def test_integrated_development_pipeline(tmp_path):
    rows = []
    for unit in range(1, 46):
        length = 10 + unit % 8
        for cycle in range(1, length + 1):
            rows.append([unit, cycle, 0., 0., 0.] + [float(length-cycle+j/10) for j in range(21)])
    pd.DataFrame(rows, columns=COLUMNS).to_csv(tmp_path / "train_FD001.txt", sep=" ", header=False, index=False)
    report = run(tmp_path)
    assert report["interval_metrics"]["endpoints"] == 9
    assert 0 <= report["interval_metrics"]["coverage"] <= 1
    assert report["radius_cycles"] >= 0
    assert "official_test" not in report
    assert len(set(report["training_units"] + report["calibration_units"] + report["evaluation_units"])) == 45
