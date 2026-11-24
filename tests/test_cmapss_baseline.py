import numpy as np
import pandas as pd
import pytest

from research.cmapss_baseline import run, scores
from src.prognostics import COLUMNS


def write_trajectories(path, lengths):
    rows = []
    for unit, length in enumerate(lengths, 1):
        for cycle in range(1, length + 1):
            rows.append([unit, cycle, 0., 0., 0.] +
                        [float(length - cycle + j / 10) for j in range(21)])
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, sep=" ", header=False, index=False)


def test_asymmetric_penalty():
    early = scores([50], [40])
    late = scores([50], [60])
    assert early["mae"] == late["mae"] == 10
    assert early["rmse"] == late["rmse"] == 10
    assert late["nasa_score"] > early["nasa_score"]
    assert scores([50], [50])["nasa_score"] == 0


def test_temporal_pipeline(tmp_path):
    write_trajectories(tmp_path / "train_FD001.txt", list(range(12, 22)))
    development = run(tmp_path)
    assert not set(development["fit_units"]) & set(development["validation_units"])
    assert len(development["validation_units"]) == 2
    assert "official_test" not in development
    assert len(development["validation"]) == 4
    assert development["selected"] in development["validation"]
    write_trajectories(tmp_path / "test_FD001.txt", [8, 10])
    (tmp_path / "RUL_FD001.txt").write_text("4\n7\n")
    final = run(tmp_path, official=True)
    assert final["selected"] == development["selected"]
    assert all(np.isfinite(v) for v in final["official_test"].values())
    assert len(final["labels_sha256"]) == 64
