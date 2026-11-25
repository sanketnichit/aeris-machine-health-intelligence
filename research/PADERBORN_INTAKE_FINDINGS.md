# Paderborn source-intake findings

[Protocol](PADERBORN_INTAKE_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45616628635) | [Evidence](evidence/paderborn_intake_summary.json)

All three original publisher archives matched the versioned mirror MD5; SHA-256 and byte counts are registered. All 240 expected filenames were inventoried and 12 selected MAT waveforms inspected, with 12 targeted tests passing. All selected waveforms are finite, nonconstant and explicitly named vibration_1. All 12 have non-nominal sample counts (256001 to 258669); the recorded vibration Unit field is empty and Raster is HostService. No sample clock, units or duration inferred from those counts. The first failed run is retained in the protocol. No diagnostic score or fault-class performance was computed.

The publisher describes four-second measurements and the recorded auxiliary speed channel. Next inspect actual time-axis data, raster references, measured speed and metadata, without assuming that every time vector represents the vibration channel or that nominal settings are calibrated values. Geometry and calibration remain separate gates.
