import math

import numpy as np
import pytest

from src.vibration_spectrum import spectral_summary


def tone(n, rate, frequency, amplitude=1):
    return amplitude * np.sin(2 * np.pi * frequency * np.arange(n) / rate)


@pytest.mark.parametrize("taper", ["rectangular", "hann"])
def test_known_tone(taper):
    signal = 12 + tone(1024, 1024, 80, 3)
    result = spectral_summary(signal, 1024, taper=taper, band_edges_hz=[0, 40, 120, 512])
    assert result["dominant_frequency_hz"] == 80
    assert result["bin_spacing_hz"] == 1
    assert result["mean_square_m2_s4"] == pytest.approx(4.5)
    assert result["spectral_rms_m_s2"] == pytest.approx(3 / math.sqrt(2))
    assert result["bands"][1]["fraction"] == pytest.approx(1)
    assert 0 <= result["normalized_entropy"] <= 1


@pytest.mark.parametrize("n", [63, 64, 127, 128])
def test_rectangular_parseval(n):
    signal = np.random.default_rng(42).normal(size=n) + 5
    result = spectral_summary(signal, 1000, taper="rectangular")
    assert result["mean_square_m2_s4"] == pytest.approx(np.var(signal))
    assert sum(b["mean_square_m2_s4"] for b in result["bands"]) == pytest.approx(np.var(signal))
    assert sum(b["bin_count"] for b in result["bands"]) == n // 2 + 1
    assert sum(b["fraction"] for b in result["bands"]) == pytest.approx(1)


def test_two_tones_and_band_boundary():
    signal = tone(512, 512, 32, 2) + tone(512, 512, 128, 1)
    result = spectral_summary(signal, 512, taper="rectangular", band_edges_hz=[0, 32, 128, 256])
    assert result["dominant_frequency_hz"] == 32
    assert [b["fraction"] for b in result["bands"]] == pytest.approx([0, .8, .2])
    assert result["centroid_hz"] == pytest.approx(51.2)


def test_nyquist_not_doubled():
    result = spectral_summary(3 * (-1.0) ** np.arange(64), 64, taper="rectangular")
    assert result["dominant_frequency_hz"] == 32
    assert result["mean_square_m2_s4"] == pytest.approx(9)
    assert result["bands"][-1]["fraction"] == pytest.approx(1)


def test_constant_abstains():
    result = spectral_summary([2.3] * 64, 1000)
    assert result["mean_square_m2_s4"] == 0
    assert result["dominant_frequency_hz"] is None
    assert result["centroid_hz"] is None
    assert result["normalized_entropy"] is None
    assert all(b["fraction"] is None for b in result["bands"])


@pytest.mark.parametrize("values,rate,options", [
    ([1] * 15, 100, {}),
    ([float("nan")] * 16, 100, {}),
    ([1e7] * 16, 100, {}),
    ([[1, 2]] * 16, 100, {}),
    ([1] * 16, True, {}),
    ([1] * 16, 0, {}),
    ([1] * 16, 100, {"taper": "unsupported"}),
    ([1] * 16, 100, {"band_edges_hz": [0, 20, 20, 50]}),
    ([1] * 16, 100, {"band_edges_hz": [1, 50]}),
    ([1] * 16, 100, {"band_edges_hz": [0, 51]}),
    ([1] * 16, 100, {"band_edges_hz": [0, float("inf"), 50]}),
])
def test_reject_invalid_spectral_inputs(values, rate, options):
    with pytest.raises(ValueError):
        spectral_summary(values, rate, **options)
