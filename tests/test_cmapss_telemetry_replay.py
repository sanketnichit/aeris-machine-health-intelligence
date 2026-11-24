import numpy as np
import pandas as pd
import pytest
from research.cmapss_telemetry_replay import export_traces, SENSOR_COLUMNS
from src.prognostics import COLUMNS


def fixture():
    return pd.DataFrame([
        [unit, cycle, 0., 0., 0.] + [float(unit+cycle+j/10) for j in range(21)]
        for unit in range(1,11)
        for cycle in range(1,unit+12)
    ], columns=COLUMNS)


def test_demo_traces_are_held_out_and_pre_failure():
    traces = export_traces(fixture())
    assert [t["unit"] for t in traces] == [1,2,3]
    for trace in traces:
        assert trace["unit"] not in trace["fit_units"]
        assert [p["cycle"] for p in trace["points"]] == list(range(1,trace["failure_cycle"]))
        for point in trace["points"]:
            assert set(SENSOR_COLUMNS).issubset(point)
            assert np.isfinite(point["adaptive_mean"])
            assert point["adaptive_mean"] >= 0
            assert "actual" not in point


def test_unknown_unit():
    with pytest.raises(ValueError):
        export_traces(fixture(), units=(99,))
