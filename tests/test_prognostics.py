import numpy as np
import pandas as pd
import pytest

from src.prognostics import (COLUMNS, SENSORS, validate_trajectories, training_targets,
                             causal_features, endpoint_indices, endpoint_targets, load_trajectories)


def sample():
    rows = []
    for unit, length in [(1, 4), (2, 3)]:
        for cycle in range(1, length + 1):
            rows.append([unit, cycle] + [0.] * 3 + [float(unit * 100 + cycle)] * 21)
    return pd.DataFrame(rows, columns=COLUMNS)


def test_targets_and_endpoints():
    data = validate_trajectories(sample())
    assert training_targets(data).tolist() == [3, 2, 1, 0, 2, 1, 0]
    assert endpoint_indices(data).tolist() == [3, 6]


def test_prefix_invariance_and_unit_isolation():
    data = sample()
    whole = causal_features(data, window=3)
    prefix = causal_features(data.loc[data.cycle <= 2], window=3)
    pd.testing.assert_frame_equal(whole.loc[[0, 1, 4, 5]].reset_index(drop=True), prefix)
    assert whole.loc[4, "sensor_1_mean"] == 201.
    assert whole.loc[2, "sensor_1_delta"] == 2.
    assert "unit" not in whole.columns


@pytest.mark.parametrize("kind", ["duplicate", "gap", "fractional", "nonfinite"])
def test_invalid_trajectories(kind):
    data = sample()
    if kind == "duplicate":
        data = pd.concat([data, data.iloc[[0]]])
    elif kind == "gap":
        data = data.drop(index=1)
    elif kind == "fractional":
        data["cycle"] = data.cycle.astype(float)
        data.loc[0, "cycle"] = 1.5
    else:
        data.loc[0, SENSORS[0]] = np.inf
    with pytest.raises(ValueError):
        validate_trajectories(data)


def test_files_and_official_offsets(tmp_path):
    path = tmp_path / "train.txt"
    sample().to_csv(path, sep=" ", index=False, header=False)
    data = load_trajectories(path)
    offsets = tmp_path / "RUL.txt"
    offsets.write_text("12\n30\n")
    assert endpoint_targets(data, offsets).tolist() == [12, 30]
    offsets.write_text("12\n")
    with pytest.raises(ValueError):
        endpoint_targets(data, offsets)
