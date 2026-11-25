# Next research candidate — acceptance, not publication

The original v0.1.0 source tag, DOI and release assets remain unchanged. Main contains post-release research. Candidate bundles use candidate-<revision> filenames without changing VERSION. The separate next-candidate-acceptance workflow never publishes or tags a release and has read-only repository permissions. It is triggered when registered NASA multi-regime evidence changes, or manually dispatched.

Required gates: registered evidence integrity and preflight, full regression in checkout and extracted archive, deterministic report, exact revision and checksums, all research pages plus virtual/vibration laboratory browser smoke, authenticated synthetic fleet review, concurrent ingestion, freshness worker and verified database backup/recovery. The acceptance artifacts preserve the exact tested revision. An explicit later review and publication decision is required; this workflow cannot perform that step.

No new field or safety claim is implied. The offline capture advisory is separate from fleet monitoring decisions; real calibration enrollment, authenticated external sensors, prospective physical validation and production security review are outstanding.

A later registered training-only regime-development report also triggers the acceptance campaign, so the exact newer revision is independently tested. An earlier accepted revision is not evidence that a later revision passes.

## Offline candidate verification

Extract the uploaded candidate artifact into its own directory, then from a trusted checkout run `python -m scripts.verify_candidate_bundle <directory> --expected-revision <full-commit-sha>`. The verifier checks the exact five checksum entries, revision, preflight report fingerprint, required source paths, archive path safety and CRC without extracting source files. It checks internal consistency, not authenticity or workflow success. Obtain the artifact and expected revision independently from the successful GitHub run. The verifier does not publish anything.
