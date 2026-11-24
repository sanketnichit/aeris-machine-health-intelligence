# FD001 stage and landmark development findings — 2026-11-24

Sources:
- https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45425734153 (17600ca4cf7af1b47b9cfc0d225c017e3050b9b1)
- https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45425977497 (ea2c282504c431fd5121774d47d586daaff7a757)
- Train SHA256: 963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8

## Retrospective stage audit
Five group-disjoint folds, 100 engines, 400 endpoints per candidate.

| Candidate | MAE | RMSE | NASA penalty |
|---|---:|---:|---:|
| Constant | 50.880 | 59.294 | 1155071.11 |
| Age-conditioned | 27.693 | 38.279 | 564725.59 |
| Age-only HGB | 31.135 | 39.584 | 301444.37 |
| Snapshot HGB | 23.249 | 32.502 | 119154.96 |
| Causal HGB | 23.665 | 34.549 | 1044814.88 |
| Relative HGB | 19.658 | 30.012 | 253674.24 |

Relative features reduce MAE about 29% and RMSE about 22% versus the age-conditioned median; the snapshot model retains the best asymmetric penalty. Relative HGB MAE by stage: 38.305, 25.371, 10.570, 4.385 versus baseline 33.740, 33.360, 24.455, 19.215. Early-life degradation signals have not demonstrated added value.

## Observable landmarks
| Cycle | Survivors | Baseline MAE | Relative HGB MAE | Coverage | Mean interval width |
|---|---:|---:|---:|---:|---:|
| 50 | 100 | 34.330 | 39.995 | .940 | 208.953 |
| 100 | 100 | 34.330 | 27.998 | .940 | 148.318 |
| 150 | 94 | 32.649 | 13.168 | .979 | 126.167 |
| 200 | 48 | 33.073 | 8.152 | .979 | 68.395 |

All landmarks had finite calibration intervals in the reported execution. Coverage is descriptive, pooled across folds, not a new theoretical guarantee. Population changes with survival; differences between landmarks do not establish within-engine improvement. Intervals remain wide relative to point error. The stage and landmark audits have different fitting and calibration schemes and should not be conflated.

## Next evidence gate
Use paired engine-cluster bootstrap on the fixed stage predictions to quantify exploratory differences. The stage observations within one engine are correlated. The bootstrap does not capture full model-refitting uncertainty. Freeze an official endpoint protocol before evaluating the untouched official labels; no repeated tuning against them. Prioritize age-conditioned baselines, conservative prediction and calibration sharpness. These are development findings on simulated engines, not field validation or evidence of research novelty.
