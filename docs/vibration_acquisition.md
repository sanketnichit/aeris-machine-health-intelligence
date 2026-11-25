# Vibration capture acquisition (development add-on)

The adapter converts an offline two-axis acceleration CSV into version-1 telemetry that can be staged in the durable edge queue. It does not connect a physical device or establish sensor calibration.

## Input contract

- UTF-8 CSV with the exact header horizontal,vertical; signed finite numeric samples in acquisition order.
- Both channels use an explicit common unit: m/s2 or g (standard gravity conversion 9.80665 m/s2 per g).
- Supply the timezone-aware timestamp of the first sample, integer sample rate (1–100000 Hz) and window size (2–8192 samples).
- A capture is assumed uniformly sampled, synchronous across axes and gap-free. The CSV cannot independently establish these properties.
- Limits: 4 MiB, 100000 samples and 1000 complete nonoverlapping windows. Incomplete windows and missing/nonfinite samples are rejected. Numerical magnitude bound is not a physical safety limit.

Example capture:

```csv
horizontal,vertical
-1,-2
1,2
-3,-4
3,4
```

Analyze locally:

```bash
python -m src.vibration_acquisition capture.csv --asset capture-demo --start 2026-01-01T00:00:00Z --rate 10 --window 2 --unit g
```

Add --queue edge.sqlite3 to stage eligible observations. Register the asset in the local API with expected horizontal_vibration_rms and vertical_vibration_rms before draining. See [edge buffer](edge_buffer.md) and [API](api.md). Keep captures and databases outside version control.

## Features and quality

RMS includes DC; the analysis separately reports mean, AC RMS (demeaned), absolute peak and crest factor. The timestamp corresponds to the last sample in each window, derived from the declared sample clock with microsecond rounding. Source bytes are hashed using SHA-256.

An exactly constant axis or an axis reaching an optional declared absolute clipping limit (specified in the input unit using --clip-limit) flags the window. A capture with any flagged window is not queued; analysis still returns the diagnostics. Constant acceleration can be physically legitimate, and the clipping threshold is only a user-declared range. Neither flag is a calibrated fault detector. Without a declared range the adapter does not assess saturation. Sampling jitter, dropped rows, aliasing, sensor orientation and calibration are not validated by this file format.

Save the JSON analysis separately if provenance is required; only the normalized RMS measurements and timestamps are persisted in the queue and API. Raw samples, quality diagnostics and capture digest are not attached to the telemetry schema. No operational life estimate or equipment control is provided.

## Next gates

Validate complete capture-to-queue-to-API replay, frequency-domain processing against known synthetic signals, provenance retention and independent measured sensor captures. The published v0.1.0 archive is unchanged.
