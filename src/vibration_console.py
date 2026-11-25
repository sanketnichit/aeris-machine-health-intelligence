"""Read-only vibration laboratory; synthetic default, trusted local archive opt-in."""
import json
import os
import sqlite3

import numpy as np
import pandas as pd
import streamlit as st

from src.capture_archive import list_captures, load_capture
from src.vibration_acquisition import analyze_capture, read_capture
from src.vibration_spectrum import spectral_summary


def synthetic_capture():
    rate, n = 1024, 512
    t = np.arange(2 * n) / rate
    h = 2 * np.sin(2 * np.pi * 48 * t) + 0.5 * np.sin(2 * np.pi * 160 * t)
    v = np.sin(2 * np.pi * 80 * t)
    raw = ("horizontal,vertical\n" + "".join(f"{a:.12g},{b:.12g}\n" for a, b in zip(h, v))).encode()
    return raw, analyze_capture(raw, asset_id="synthetic-vibration", start="2026-01-01T00:00:00Z",
                                sample_rate_hz=rate, window_samples=n, unit="m/s2", spectrum=True)


def selected_window(raw, analysis, index, axis):
    if type(index) is not int or not 0 <= index < len(analysis["windows"]) or axis not in ("horizontal", "vertical"):
        raise ValueError("Invalid window or axis selection")
    window = analysis["windows"][index]
    samples = read_capture(raw, analysis["input_unit"])
    if len(samples) != analysis["sample_count"]:
        raise ValueError("Capture sample count mismatch")
    first, last = window["first_sample_index"], window["last_sample_index"]
    if not 0 <= first <= last < len(samples) or last - first + 1 != analysis["window_samples"]:
        raise ValueError("Invalid archived window bounds")
    values = np.asarray(samples[first:last + 1])[:, 0 if axis == "horizontal" else 1]
    time = np.arange(len(values)) / analysis["sample_rate_hz"]
    stats = window["axes"][axis]
    spectrum = None
    if not stats["quality_flags"] and stats.get("spectrum") is not None:
        saved = stats["spectrum"]
        edges = [b["low_hz"] for b in saved["bands"]] + [saved["bands"][-1]["high_hz"]]
        spectrum = spectral_summary(values, analysis["sample_rate_hz"], taper=saved["taper"],
                                    band_edges_hz=edges, include_bins=True)
    return time, values, stats, spectrum


def render_vibration():
    st.title("AERIS | Vibration Laboratory")
    st.caption("Read-only waveform and frequency inspection. No operational fault diagnosis or machine control.")
    archive_path = os.environ.get("AERIS_CAPTURE_ARCHIVE_PATH")
    source = st.radio("Capture source", ["Synthetic demonstration"] + (["Local capture archive"] if archive_path else []),
                      horizontal=True)
    try:
        if source == "Synthetic demonstration":
            raw, analysis = synthetic_capture()
            st.info("Synthetic demonstration: known 48 Hz and 160 Hz horizontal components; 80 Hz vertical component.")
        else:
            st.warning("Trusted local archive. Anyone with dashboard access can read these captures.")
            rows = list_captures(archive_path)
            if not rows:
                st.info("No archived captures.")
                return
            labels = {r["capture_id"]: f'{r["asset_id"]} | {r["start_utc"]} | {r["capture_id"][:12]}' for r in rows}
            ident = st.selectbox("Archived capture", list(labels), format_func=labels.__getitem__)
            raw, analysis = load_capture(archive_path, ident)
            st.caption(f"Capture ID: {ident}")
        a, b, c = st.columns(3)
        a.metric("Samples", analysis["sample_count"])
        b.metric("Declared sample rate", f'{analysis["sample_rate_hz"]} Hz')
        c.metric("Flagged windows", analysis["flagged_windows"])
        st.caption(f'Asset: {analysis["asset_id"]} · Start (UTC): {analysis["start_utc"]}')
        index = st.selectbox("Analysis window", list(range(analysis["window_count"])),
                             format_func=lambda i: f"Window {i + 1}")
        axis = st.radio("Vibration axis", ["horizontal", "vertical"], horizontal=True)
        time, values, stats, spectrum = selected_window(raw, analysis, index, axis)
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError, IndexError):
        st.error("Capture inspection failed. Verify the local archive and acquisition metadata.")
        return

    st.subheader("Acceleration waveform")
    st.line_chart(pd.DataFrame({"Elapsed seconds": time, "Acceleration (m/s²)": values}),
                  x="Elapsed seconds", y="Acceleration (m/s²)")
    a, b, c = st.columns(3)
    a.metric("RMS (m/s²)", f'{stats["rms_m_s2"]:.4g}')
    b.metric("AC RMS (m/s²)", f'{stats["ac_rms_m_s2"]:.4g}')
    c.metric("Peak (m/s²)", f'{stats["peak_m_s2"]:.4g}')
    flags = stats["quality_flags"]
    if flags:
        st.warning("Signal quality flags: " + ", ".join(flags))
    else:
        st.caption("No configured quality flag for this axis; physical signal validity is not established.")
    st.subheader("Frequency spectrum")
    if spectrum is None:
        st.info("Spectrum withheld or not recorded for this axis.")
    else:
        st.caption("FFT bins recomputed for display using saved analysis settings; archived summary remains unchanged.")
        st.line_chart(pd.DataFrame({"Frequency (Hz)": spectrum["frequency_bins_hz"],
                                   "Bin mean square (m²/s⁴)": spectrum["bin_mean_square_m2_s4"]}),
                      x="Frequency (Hz)", y="Bin mean square (m²/s⁴)")
        saved = stats["spectrum"]
        peak = saved["dominant_frequency_hz"]
        st.metric("Recorded dominant frequency", "Undefined" if peak is None else f"{peak:g} Hz")
        st.dataframe(pd.DataFrame(saved["bands"]), hide_index=True)
    st.caption(f'Raw SHA-256: {analysis["capture_sha256"]}')
    st.download_button("Download preserved analysis", json.dumps(analysis, indent=2, allow_nan=False),
                       file_name="vibration-analysis.json", mime="application/json")
    st.caption("Declared sample clock is unverified. Spectra are descriptive; no field calibration or fault-frequency diagnosis.")
