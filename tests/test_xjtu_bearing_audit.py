import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from research.xjtu_bearing_audit import EXPECTED, archive_members, vibration_features, prepare, evaluate


def test_vibration_features():
    x = np.tile([-2.,2.], 32)
    result = vibration_features(np.column_stack([x,np.zeros(64)]),expected_samples=64)
    assert result["horizontal_rms"] == 2.
    assert result["horizontal_crest"] == 1.
    assert result["horizontal_kurtosis"] == 1.
    assert result["horizontal_high_fraction"] == 1.
    assert result["vertical_crest"] == 0.
    with pytest.raises(ValueError):
        vibration_features(np.ones((64,3)),expected_samples=64)


def test_archive_members():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream,"w") as archive:
        for bearing in sorted(EXPECTED):
            for age in range(1,5):
                archive.writestr(f"data/{bearing}/{age}.csv","x,y\n1,2\n")
    with zipfile.ZipFile(stream) as archive:
        assert len(archive_members(archive)) == 60


def fixture():
    return pd.DataFrame([{"bearing":b,"condition":int(b[7]),"age":a,
                          "horizontal_rms":float(a),"vertical_rms":float(a*2)}
                         for b in sorted(EXPECTED) for a in range(1,9)])


def test_prefix_invariance():
    frame=fixture()
    full=prepare(frame)
    prefix=prepare(frame.loc[frame.age<=4])
    pd.testing.assert_frame_equal(full.loc[full.age<=4].reset_index(drop=True),prefix)


def test_evaluation_isolation():
    report=evaluate(fixture())
    assert len(report["predictions"]) == 120
    for row in report["predictions"]:
        assert row["bearing"] not in row["fit_bearings"]
        if row["split"]=="condition":
            assert all(b[7]!=row["bearing"][7] for b in row["fit_bearings"])
    for split in ("bearing","condition"):
        assert report["summary"][split]["learned"]["all"]["endpoints"]==60
