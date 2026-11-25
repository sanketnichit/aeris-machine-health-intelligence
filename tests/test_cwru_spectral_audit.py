import numpy as np
import pytest

from research.cwru_spectral_audit import RATE, WINDOW, ORDERS, FILES, fractions, compare_window, normalize


def test_protocol_population():
    assert len(FILES) == 8
    assert len({file_id for file_id, _, _ in FILES}) == 8
    for kind in ORDERS:
        assert {load for _, label, load in FILES if label == kind} == {0, 1, 2, 3}


def test_known_modulation():
    t = np.arange(WINDOW) / RATE
    rpm = 1800
    defect_hz = ORDERS["inner"] * rpm / 60
    x = (1 + .5 * np.cos(2 * np.pi * defect_hz * t)) * np.sin(2 * np.pi * 3000 * t)
    result = compare_window(x, rpm)
    assert result["envelope"]["inner"] > .85
    assert result["envelope"]["inner"] > result["raw"]["inner"]
    assert result["envelope"]["inner"] > result["envelope"]["outer"]
    assert fractions(x, rpm) == pytest.approx(fractions(x * 100, rpm), abs=1e-12)


@pytest.mark.parametrize("values", [np.zeros(WINDOW), np.ones(WINDOW), np.ones(WINDOW-1),
                                    np.full(WINDOW, np.nan)])
def test_invalid_window(values):
    with pytest.raises(ValueError):
        normalize(values)
