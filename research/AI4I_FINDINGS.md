# AI4I research findings — 2026-11-24

Evidence: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45424734768
Execution revision: 329c4721fdba76b46e00dc48871439ff9730992b
Artifact: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45424734768/artifacts/14934528476
Dataset SHA256: dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e

## Rule comparison
| Method | Precision | Recall | F1 | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Published generator rules | 1.000 | .8382 | .912 | 1932 | 0 | 11 | 57 |
| Calibrated HGB | .9649 | .8088 | .880 | 1930 | 2 | 13 | 55 |

All HDF/PWF/OSF flags matched on this test partition. ML detected zero additional positive rows beyond the rule union at the fixed threshold. Rules detected two additional positives; both missed 11. The ML AP was .900970, versus the archived .8986; the confusion matrix is unchanged. Runtime/dependency and threading differences may contribute, but the cause has not been isolated. No overwrite of the original result.

## Sensor stress (mean AP across three seeds)
| Noise fraction of training SD | Missing probability | AP |
|---:|---:|---:|
| 0 | 0 | .901 |
| .05 | 0 | .774 |
| .10 | 0 | .636 |
| .25 | 0 | .434 |
| 0 | .05 | .829 |
| 0 | .10 | .767 |
| 0 | .25 | .565 |
| .10 | .10 | .541 |

## Held-out regime recall at 0.50
Low speed .202; high torque .360; high wear .285; low temperature delta .095; type L .455; type M .675; type H .667.

## Interpretation
Known generator rules outperform the learned classifier at this operating point. This is a negative finding for claims of added ML value on AI4I, not evidence of physical causality or field safety. Sensor perturbations are artificial and regime tests overlap. Preserve these findings and treat subsequent model development as a new experiment, not optimization against the already inspected test partition. Priority shifts to independent temporal evidence and uncertainty-aware decisions.
