import sqlite3

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from src.capture_archive import list_captures
from src.vibration_console import selected_window, synthetic_capture


def test_selected_window_preserves_saved_analysis():
    raw, analysis = synthetic_capture()
    for index in (0, 1):
        for axis, peak in (("horizontal", 48), ("vertical", 80)):
            time, values, stats, spectrum = selected_window(raw, analysis, index, axis)
            assert len(time) == len(values) == 512
            assert time[0] == 0
            assert time[-1] == 511 / 1024
            assert spectrum["frequency_bins_hz"][np.argmax(spectrum["bin_mean_square_m2_s4"])] == peak
            assert sum(spectrum["bin_mean_square_m2_s4"]) == pytest.approx(stats["spectrum"]["mean_square_m2_s4"])
            assert "frequency_bins_hz" not in stats["spectrum"]
    with pytest.raises(ValueError):
        selected_window(raw, analysis, 2, "horizontal")


def test_missing_archive_not_created(tmp_path):
    path = tmp_path / "nonexistent.sqlite3"
    with pytest.raises(sqlite3.OperationalError):
        list_captures(path)
    assert not path.exists()


def test_interactive_synthetic_workspace(monkeypatch):
    monkeypatch.delenv("AERIS_CAPTURE_ARCHIVE_PATH", raising=False)
    at = AppTest.from_string("from src.vibration_console import render_vibration\nrender_vibration()").run(timeout=30)
    assert not at.exception
    assert at.title[0].value == "AERIS | Vibration Laboratory"
    assert at.radio[0].options == ["Synthetic demonstration"]
    assert any(m.label == "Recorded dominant frequency" and m.value == "48 Hz" for m in at.metric)
    at.radio[1].set_value("vertical").run(timeout=30)
    assert not at.exception
    assert any(m.label == "Recorded dominant frequency" and m.value == "80 Hz" for m in at.metric)
