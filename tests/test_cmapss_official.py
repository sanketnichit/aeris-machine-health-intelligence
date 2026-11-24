import hashlib
import numpy as np
import pandas as pd
import pytest

from research.cmapss_official import verify, predict_endpoints, paired_delta
from src.prognostics import COLUMNS


def fixture(lengths):
    return pd.DataFrame([
        [unit, cycle, 0., 0., 0.] + [float(length-cycle+j/10) for j in range(21)]
        for unit,length in enumerate(lengths,1)
        for cycle in range(1,length+1)
    ],columns=COLUMNS)


def test_fingerprint(tmp_path):
    path=tmp_path/"fixture.txt"
    path.write_bytes(b"example")
    assert verify(path,hashlib.sha256(b"example").hexdigest())
    with pytest.raises(ValueError):
        verify(path,"bad")


def test_one_prediction_per_engine_without_targets():
    units,ages,pred=predict_endpoints(fixture(range(10,20)),fixture([4,6,9]))
    assert units.tolist()==[1,2,3]
    assert ages.tolist()==[4,6,9]
    assert set(pred)=={"age_reference","constant","snapshot_hgb","relative_hgb","adaptive_mean"}
    assert all(v.shape==(3,) and np.isfinite(v).all() and (v>=0).all() for v in pred.values())


def test_paired_comparison():
    report=paired_delta(np.array([10.,20.]),np.array([11.,21.]),np.array([13.,23.]))
    assert report["mae_delta"]==-2.
    assert report["percentile_95_interval"]==[-2.,-2.]
    assert report["win_fraction"]==1.
