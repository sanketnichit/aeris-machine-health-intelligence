# MFPT cross-platform transfer — findings v1

[Protocol](MFPT_TRANSFER_PROTOCOL.md) · [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45562653072) · [Evidence](evidence/mfpt_transfer_summary.json)

The frozen CWRU policy (score floor 0.00974446327636002, relative margin 0.80) was applied without threshold adjustment to 17 MFPT recordings, with geometry-specific frequency centers taken from source metadata. Four complete effective windows per recording: 68 windows, 557056 resampled samples.

| Condition | Recordings | Correct accepted fault suggestions | Incorrect accepted fault suggestions | Withheld |
|---|---:|---:|---:|---:|
| Inner race | 7 | 7 | 0 | 0 |
| Outer race | 7 | 7 | 0 | 0 |
| Normal baseline | 3 | Not applicable | 0 | 3 |

Fault-only coverage 14/14; observed retained error 0/14. Forced ranking also had zero errors among the 14 faults. Selectivity preserved fault coverage rather than improving fault ranking, and withheld all three normal recordings. Abstention is not a healthy-state diagnosis. All 17 source Git blob fingerprints match the pinned repository tree; the execution records SHA-256, source revision and policy fingerprint. Full window-level evidence and environment are linked in the summary.

This is a positive independent-rig method transfer on a selected laboratory population. No ball-defect controls were included, repeated loads may share physical hardware, and three normal recordings are insufficient to establish field false-alarm risk. No calibrated probabilities, unknown-fault detection, RUL or operational safety validation. MFPT results are now observed and cannot be reused as untouched confirmation of a revised method.

Source: Eric Bechhoefer, Condition Based Maintenance Fault Database for Testing Diagnostics and Prognostic Algorithms (2013), MathWorks redistribution, https://github.com/mathworks/RollingElementBearingFaultDiagnosis-Data/tree/d3efefb6ce84fa1ee6c0311f80f7c89cf903ad1d (CC BY-NC-SA 4.0). Raw waveforms are not redistributed by AERIS. Derived numerical evidence is provided with source attribution; the upstream dataset is not relicensed under MIT. The DOI-archived v0.1.0 is unchanged.
