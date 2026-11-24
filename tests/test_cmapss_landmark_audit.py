import numpy as np
import pandas as pd

from research.cmapss_landmark_audit import evaluate, landmark_indices
from src.prognostics import COLUMNS


def fixture():
    rows = []
    for unit in range(1, 46):
        length = 12 + unit % 7
        for cycle in range(1, length + 1):
            rows.append([unit, cycle, 0., 0., 0.] +
                        [float(length-cycle+j/10) for j in range(21)])
    return pd.DataFrame(rows, columns=COLUMNS)


def test_landmark_only_uses_observed_age():
    data = fixture()
    indices = landmark_indices(data, [1, 2], 5)
    assert data.loc[indices, "cycle"].tolist() == [5, 5]
    assert data.loc[indices, "unit"].tolist() == [1, 2]
    assert len(landmark_indices(data, [1, 2], 100)) == 0


def test_independent_populations_and_sparse_landmarks():
    data = fixture()
    report = evaluate(data, landmarks=(5, 18, 100))
    assert report["summary"]["5"]["evaluated_engines"] == 45
    assert report["summary"]["5"]["interval_evaluated_engines"] == 45
    assert report["summary"]["100"]["evaluated_engines"] == 0
    assert report["summary"]["18"]["interval_evaluated_engines"] == 0
    for fold in report["folds"]["5"]:
        fit, cal, ev = (set(fold[k]) for k in ("fit_units", "calibration_units", "evaluation_units"))
        assert not (fit & cal or fit & ev or cal & ev)
        assert len(fit | cal | ev) == 45
        assert np.isfinite(fold["radius_cycles"])
