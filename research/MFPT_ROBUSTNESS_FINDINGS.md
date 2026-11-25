# MFPT sensor robustness — findings v1

[Protocol](MFPT_ROBUSTNESS_PROTOCOL.md) · [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45576809182) · [Evidence](evidence/mfpt_robustness_summary.json)

Fourteen scenarios applied separately to the same 17 observed MFPT recordings (238 recording-scenario assessments, 952 window-scenario evaluations). Source fingerprints verified; clean reference reproduced. No threshold refit.

| Scenario | Correct accepted | Incorrect accepted | Withheld faults | Correct accepted after gate |
|---|---:|---:|---:|---:|
| Clean | 14 | 0 | 0 | 14 |
| Noise 20 dB | 14 | 0 | 0 | 14 |
| Noise 10 dB | 14 | 0 | 0 | 14 |
| Noise 0 dB | 13 | 0 | 1 | 13 |
| Clip 2 RMS | 14 | 0 | 0 | 0 |
| Clip 0.5 RMS | 8 | 0 | 6 | 0 |
| Speed -5% | 4 | 5 | 5 | 4 |
| Speed -1% | 14 | 0 | 0 | 14 |
| Speed +1% | 13 | 0 | 1 | 13 |
| Speed +5% | 0 | 1 | 13 | 0 |
| Clock proxy -1% | 13 | 0 | 1 | 13 |
| Clock proxy +1% | 14 | 0 | 0 | 14 |
| Missing 1% | 14 | 0 | 0 | 0 |
| Missing 10% | 14 | 0 | 0 | 0 |

Each row has 14 fault recordings. No normal control received a fault suggestion in these scenarios. The explicit metadata gate removes 50 otherwise correct accepted suggestions across four clipping/missing scenarios and prevents zero observed incorrect suggestions. This is a conservative validity policy, not demonstrated accuracy improvement. Retained error is undefined when no suggestion is accepted.

The principal failure is order localization under shaft-speed error: -5% yields 5/9 incorrect accepted and +5% yields 1/1 incorrect accepted. High relative spectral margin does not protect against wrong frequency metadata. No safe speed tolerance follows from this finite retrospective grid. Future work should require independently justified speed/clock uncertainty and test stability across the entire plausible range before issuing a suggestion; a sampled sensitivity grid alone is not a continuous guarantee. Do not tune on this observed population and claim independent confirmation.

Perturbations are artificial and applied after resampling. Clock perturbation is only a frequency-center proxy. Missing data uses naive zero filling, not recommended imputation. Repeated scenario assessments are correlated; no new independent assets, field error rate, analog hardware robustness or operational safety is established. Source license CC BY-NC-SA 4.0, attribution in summary; no raw waveform redistribution. Original release unchanged.
