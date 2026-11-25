# Capture provenance archive (development add-on)

The local archive preserves exact raw vibration CSV bytes together with the canonical analysis JSON and normalized telemetry batch. This is a separate SQLite database from the edge queue and telemetry server; it is not a modification of the v0.1.0 release.

## Workflow

Use the same CSV and declared acquisition metadata described in [vibration acquisition](vibration_acquisition.md). A capture can be archived offline:

```bash
python -m src.capture_archive --archive captures.sqlite3 add capture.csv --asset capture-demo --start 2026-01-01T00:00:00Z --rate 1024 --window 1024 --unit m/s2 --spectrum
python -m src.capture_archive --archive captures.sqlite3 list
python -m src.capture_archive --archive captures.sqlite3 show CAPTURE_ID
python -m src.capture_archive --archive captures.sqlite3 stage CAPTURE_ID --queue edge.sqlite3
python -m src.edge_buffer --queue edge.sqlite3 drain
```

Replace CAPTURE_ID with the returned 64-character identifier. Register the asset with the local API before draining. Use a complete capture of the declared window size (the example assumes 1024 samples per window).

The archive stores the raw input, the complete report including declared clock and units, quality flags, optional spectra, and exact normalized batch. The capture ID hashes the raw SHA-256 digest and the report SHA-256 digest together. Repeated identical bytes and canonical analysis are idempotent; different units, times, analysis parameters or numerical results may create a different identity. Raw byte hashing alone cannot distinguish analysis settings.

Raw bytes and report are committed together. Retrieval, listing and staging check integrity. Flagged captures may be retained for diagnosis, but cannot be staged. Invalid captures are rejected before archive insertion. The stage operation preserves the original batch instead of silently recomputing historical results with a later algorithm.

## Boundaries

The archive is bounded to 100 captures and 64 MiB of raw plus report bytes (database overhead is additional). Capacity exhaustion rejects new captures without deleting existing ones. No deletion, compaction or retention policy is exposed. Local files are not encrypted; use nonconfidential recordings and keep files out of version control. Hashes detect accidental alterations, not authenticity against a party that can rewrite the entire archive.

Archiving, staging and API delivery are separate transactions. No automatic archive-to-server delivery receipt or remote provenance join exists. A successful stage acknowledges the queue insertion, not server storage. Use the separate queue drain result for delivery status. Archive and queue must be different files. This version does not capture a software revision or hardware calibration certificate automatically. The metadata and quality flags remain descriptive, not evidence of physical validity.

Next: verified local read-only waveform and spectral visualization, followed by independent measured-signal evaluation.
