"""Descriptive single-window FFT features, not a machine fault classifier."""
import math
import numpy as np

MIN_SAMPLES = 16
MAX_SAMPLES = 8192
MAX_MAGNITUDE = 1e6


def spectral_summary(values, sample_rate_hz, *, taper="hann", band_edges_hz=None, include_bins=False):
    """Estimate one-sided AC mean-square spectrum; bands partition FFT bins.

    Hann weighting uses mean-square window normalization, not amplitude
    correction. A rectangular taper exactly preserves demeaned mean square.
    """
    if type(sample_rate_hz) is not int or not 1 <= sample_rate_hz <= 100_000:
        raise ValueError("Invalid declared sample rate")
    if type(include_bins) is not bool:
        raise ValueError("include_bins must be boolean")
    if taper not in ("hann", "rectangular"):
        raise ValueError("Unsupported taper")
    try:
        x = np.asarray(values, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Invalid signal") from exc
    if (x.ndim != 1 or not MIN_SAMPLES <= len(x) <= MAX_SAMPLES
            or not np.isfinite(x).all() or np.any(np.abs(x) > MAX_MAGNITUDE)):
        raise ValueError("Expected 16 to 8192 bounded finite samples")
    n = len(x)
    nyquist = sample_rate_hz / 2
    edges = [0.0, nyquist / 4, nyquist / 2, nyquist] if band_edges_hz is None else band_edges_hz
    if not isinstance(edges, (tuple, list)) or not 2 <= len(edges) <= 17:
        raise ValueError("Expected 2 to 17 band edges")
    if any(type(e) not in (int, float) for e in edges):
        raise ValueError("Band edges must be numeric")
    try:
        edges = [float(e) for e in edges]
    except OverflowError as exc:
        raise ValueError("Band edge too large") from exc
    if (not all(math.isfinite(e) for e in edges) or edges[0] != 0
            or edges[-1] != nyquist or any(b <= a for a, b in zip(edges, edges[1:]))):
        raise ValueError("Band edges must strictly partition zero to Nyquist")
    frequencies = np.fft.rfftfreq(n, d=1 / sample_rate_hz)
    # Compute AC about the window-weighted mean, removing the windowed DC bin.
    weights = np.ones(n) if taper == "rectangular" else np.hanning(n + 1)[:-1]
    if np.all(x == x[0]):
        centered = np.zeros(n)
    else:
        centered = (x - np.dot(x, weights) / weights.sum()) * weights
    power = np.abs(np.fft.rfft(centered)) ** 2 / (n * np.dot(weights, weights))
    if n % 2 == 0:
        power[1:-1] *= 2
    else:
        power[1:] *= 2
    power[0] = 0.0
    total = float(power.sum())
    if total > 0:
        probabilities = power[1:] / total
        positive = probabilities[probabilities > 0]
        peak = float(frequencies[1 + np.argmax(power[1:])])
        centroid = float(np.dot(frequencies, power) / total)
        entropy = float(-np.dot(positive, np.log(positive)) / math.log(len(probabilities)))
        entropy = max(0.0, min(1.0, entropy))
    else:
        peak = centroid = entropy = None
    bands = []
    for i, (low, high) in enumerate(zip(edges, edges[1:])):
        # Integer bin indices avoid a rounded Nyquist frequency escaping the last band.
        upper = frequencies <= high if i == len(edges) - 2 else frequencies < high
        mask = (frequencies >= low) & upper
        if i == len(edges) - 2:
            mask[-1] = frequencies[-1] >= low
        amount = float(power[mask].sum())
        bands.append({"low_hz": low, "high_hz": high, "bin_count": int(mask.sum()),
                      "mean_square_m2_s4": amount, "fraction": amount / total if total else None})
    result = {"taper": taper, "sample_count": n, "sample_rate_hz": sample_rate_hz,
            "bin_spacing_hz": sample_rate_hz / n, "nyquist_hz": nyquist,
            "mean_square_m2_s4": total, "spectral_rms_m_s2": math.sqrt(total),
            "dominant_frequency_hz": peak, "centroid_hz": centroid,
            "normalized_entropy": entropy, "bands": bands,
            "scope": "descriptive_spectrum_not_fault_diagnosis"}
    if include_bins:
        result["frequency_bins_hz"] = frequencies.tolist()
        result["bin_mean_square_m2_s4"] = power.tolist()
    return result
