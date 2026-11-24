# FD001 development findings — 2026-11-24

Execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45425367337
Revision: fcb4cce9cee4eb40f4f09c671044e147af7dc763
Artifact: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45425367337/artifacts/14936133219
NASA archive SHA256: 74bef434a34db25c7bf72e668ea4cd52afe5f2cf8e44367c55a82bfd91a5a34f
Train FD001 SHA256: 963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8

## Point forecasting (80 fit engines, 20 validation engines)

| Candidate | MAE | RMSE | NASA score |
|---|---:|---:|---:|
| Constant | 21.55 | 25.51 | 272.11 |
| Ridge snapshot | 27.34 | 32.17 | 1618.63 |
| HGB snapshot | 26.52 | 31.61 | 1145.04 |
| HGB causal | 32.64 | 43.72 | 418958.43 |

The selected candidate is constant. The learned models fail to beat it on these middle-life development prefixes. The asymmetric score reveals severe overprediction errors; inspect individual errors before making any mechanistic interpretation.

## Uncertainty (60 fit, 20 calibration, 20 evaluation engines)

Fixed causal HGB: MAE 33.61, RMSE 43.45, NASA score 24094.36. Nominal 90% split conformal radius 76.40 cycles; empirical coverage 19/20 (95%), mean interval width 152.17 cycles. Marginal support heuristic retained all 20 at every tested threshold; there is no demonstrated selective risk benefit.

## Limitations and next protocol

These are simulated training-set development experiments, not the official test. The original protocol samples only the middle third of full histories and is not a broad estimate of forecasting capability. The two experiments use different unit partitions; their scores are not directly comparable. No official test targets were evaluated. Preserve these findings. Next: group-disjoint cross-validation across early/mid/late prefixes, age-conditioned survival baseline, per-engine causal normalization and explicit age ablation. Compare against the simple baseline before claiming learned value. This is a new development experiment informed by earlier findings, not independent confirmation.
