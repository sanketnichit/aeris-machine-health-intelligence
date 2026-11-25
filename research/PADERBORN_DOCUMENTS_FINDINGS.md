# Paderborn document audit findings

[Protocol](PADERBORN_DOCUMENTS_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45618162260) | [Evidence](evidence/paderborn_documents_summary.json)

All 34 pinned PDFs from 17 specimens were extracted successfully. Six targeted tests passed. All fact sheets have unique text candidates for pitch diameter (13 at 29.05 mm, four at 28.55 mm), rolling-element diameter (6.75 mm), and pressure angle (0 degrees). Rolling-element count was unresolved by the original parser on every specimen. All measurement logs have a sampling-rate keyword on page 1, not a verified timebase interpretation. No visual review or calibrated geometry is claimed. No waveform scoring occurred.

A subsequent conditional study extends the count-unit parser to accept the piece-count abbreviation, but must independently reproduce the other extracted geometry fields and block scoring of any incomplete candidate. This is a conditional text-derived model, not a visually reviewed geometry table or verified instrument calibration.
