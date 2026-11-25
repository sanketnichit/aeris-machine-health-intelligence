# MFPT sensor robustness — frozen v1

This is a paired retrospective stress test on the same 17 previously observed MFPT recordings, not a new independent dataset or prospective validation. Source revision, waveform extraction, resampling, four 8192-sample windows, fixed bandpass and envelope processing, geometry and CWRU rejection parameters are inherited from MFPT_TRANSFER_PROTOCOL.md. Verify every raw file against the registered MFPT SHA-256 before processing. No threshold refitting.

Apply each scenario separately to the effective 12 kHz windows (not to the upstream analog sensor). Clean reference plus the following fixed perturbations:

- Add zero-mean Gaussian noise at target AC SNR 20, 10, 0 dB, using seed 42 plus recording index times 100 plus window index. Normalize each generated noise vector to exact sample AC RMS; reuse the same vector across SNRs.
- Symmetric clipping about the original window mean at 2 and 0.5 times original AC RMS. Record fraction of samples changed.
- Declared shaft speed error -5%, -1%, +1%, +5%: scale all three nominal harmonic centers, do not change waveform.
- Declared sampling clock error -1%, +1%: emulate a frequency-axis scaling by dividing all harmonic centers by 1+error. This is only an order-localization sensitivity proxy; it does not emulate filter changes or hardware jitter.
- Missing samples: zero-fill a contiguous 1% or 10% block starting at one-quarter window, using floor-rounded sample count. This is an intentionally naive comparator, not a proposed imputation strategy.

For each recording and scenario take per-order medians, apply the unchanged selective policy. Report forced errors on fault records, accepted correct/incorrect, abstentions, coverage, retained error (null when zero accepted), and accepted fault suggestions on normal controls. Compare to a metadata-aware gate: if any window has explicitly declared missing samples or reached a declared clipping limit, withhold the entire recording before interpreting scores. The gate does not infer missing samples, clipping, speed uncertainty, or noise from unannotated data. For other perturbations, gate and ungated decisions are identical. Report guard-induced lost correct suggestions as well as prevented incorrect suggestions. No hidden quality threshold, no post-hoc promotion of a scenario or sensor limit.

14 scenarios × 17 recordings = 238 recording-scenario assessments; 952 window-scenario evaluations, repeated data not independent samples. Keep all decisions and source provenance in the artifact. No statistical significance, field error rate, hardware calibration, unknown-fault robustness, or deployment recommendation. Data attribution and restrictions follow the MFPT protocol; no raw waveform redistribution.
