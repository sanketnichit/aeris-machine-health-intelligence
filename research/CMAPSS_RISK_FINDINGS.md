# FD001 risk and paired analysis — 2026-11-24

Execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45426578792
Revision: 2cf61ab106a037f76b8b21c5d6cff5612f353374
Train SHA256: 963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8

## Paired engine bootstrap
Reference: age-conditioned median, 100 engines, 5000 draws, seed 42. MAE differences (candidate minus reference), in cycles:
| Candidate | Difference | Exploratory 95% interval | Engine win fraction |
|---|---:|---|---:|
| Relative HGB | -8.035 | [-11.047, -5.044] | .66 |
| Snapshot HGB | -4.444 | [-7.433, -1.620] | .59 |
| Causal HGB | -4.028 | [-7.033, -1.193] | .56 |
| Age-only HGB | 3.443 | [2.141, 4.703] | .32 |
| Constant | 23.188 | [19.705, 26.415] | .10 |

Intervals resample engines, retaining within-engine dependence, conditional on fixed out-of-fold predictions. No full refitting uncertainty, multiplicity correction or independent confirmation.

## Risk audit, observable ages
| Age | Engines | Age reference MAE | Mean ML MAE | Adaptive MAE | q25 MAE | Mean severe overprediction | q25 severe overprediction |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 100 | 34.330 | 39.995 | 34.330 | 36.243 | .30 | .18 |
| 100 | 100 | 34.330 | 27.998 | 30.146 | 26.914 | .25 | .07 |
| 150 | 94 | 32.649 | 13.168 | 13.168 | 13.570 | .0532 | 0 |
| 200 | 48 | 33.073 | 8.152 | 8.152 | 11.072 | 0 | 0 |

Severe overprediction means predicted minus observed RUL >20 cycles. At cycle 100 q25 has worse NASA penalty than mean ML (626907.23 vs 109611.61), despite fewer severe overpredictions. Do not treat a lower quantile as a safety guarantee.

| Age | Raw interval coverage | Raw width | CQR coverage | CQR width |
|---:|---:|---:|---:|---:|
| 50 | .46 | 52.737 | .94 | 185.906 |
| 100 | .54 | 47.105 | .94 | 149.829 |
| 150 | .532 | 24.619 | .979 | 115.455 |
| 200 | .542 | 15.769 | .958 | 57.782 |

Raw quantiles substantially undercover. CQR uses nonnegative correction at nominal 90% and remains broad. Pooled fold coverage is descriptive. The age ramp was informed by previous development observations. No official test labels, real maintenance costs, or prospective validation. Next: cost-sensitive simulated replay, preserving one terminal outcome per unit and explicit lead-time semantics.
