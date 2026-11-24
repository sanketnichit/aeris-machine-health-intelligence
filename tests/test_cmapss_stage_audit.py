import numpy as np
import pandas as pd
import pytest

from research.cmapss_stage_audit import age_conditioned, relative_features, stage_rows, run
from src.prognostics import COLUMNS


def fixture():
    rows = []
    for unit in range(1, 11):
        length = 12 + unit
        for cycle in range(1, length + 1):
            rows.append([unit, cycle, 0., 0., 0.] +
                        [float(unit*100+cycle+j/10) for j in range(21)])
    return pd.DataFrame(rows, columns=COLUMNS)


def test_age_conditioned_reference():
    np.testing.assert_array_equal(age_conditioned([10, 20, 30], [5, 15, 31]), [15, 10, 0])
    with pytest.raises(ValueError):
        age_conditioned([], [2])


def test_relative_features_prefix_invariant():
    data = fixture()
    whole = relative_features(data)
    prefix = data.loc[data.cycle <= 5].reset_index(drop=True)
    pd.testing.assert_frame_equal(whole.loc[data.cycle <= 5].reset_index(drop=True),
                                  relative_features(prefix))
    assert whole.loc[data.cycle == 1, "sensor_1_relative"].eq(0).all()


def test_stage_pipeline(tmp_path):
    data = fixture()
    stages = stage_rows(data)
    assert len(stages) == 40
    assert stages.groupby("unit").size().eq(4).all()
    data.to_csv(tmp_path / "train_FD001.txt", sep=" ", header=False, index=False)
    report = run(tmp_path)
    rows = pd.DataFrame(report["predictions"])
    assert len(rows) == 240
    assert rows.groupby("unit").fold.nunique().eq(1).all()
    assert len(report["metrics"]) == 6
    assert all(len(m["by_stage"]) == 4 for m in report["metrics"].values())
    assert "official_test" not in report
