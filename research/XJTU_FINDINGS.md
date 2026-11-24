# XJTU-SY physical bearing development findings

Execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45429314185
Revision: 47e84a0adc590491b6bb5bf819d9fc65cc707557
Archive SHA256: 3cc815649a315ac7da202980c489f33db44ca2db0317bbe3bcb9dcf415375e10
Protocol: [XJTU_PROTOCOL.md](XJTU_PROTOCOL.md)
Exact results: [xjtu_summary.json](evidence/xjtu_summary.json)

All 15 expected bearing histories and 9216 snapshots were acquired and processed from the pinned third-party mirror. This corresponds to 603979776 individual vibration samples (32768 samples per snapshot, two channels). The mirror fingerprint does not establish byte equivalence with the original inaccessible author archive.

## Development results
Each split has 60 scoring endpoints (four retrospective stages per bearing). Errors are measured in remaining recorded snapshots until the last observation.

| Split | Reference MAE | Learned MAE | Reference RMSE | Learned RMSE |
|---|---:|---:|---:|---:|
| Leave one bearing out | 381.233 | 400.831 | 524.177 | 649.756 |
| Leave one condition out | 593.600 | 399.396 | 849.027 | 728.963 |

| Stage | Bearing reference MAE | Bearing learned MAE | Condition reference MAE | Condition learned MAE |
|---|---:|---:|---:|---:|
| 25% | 170.767 | 577.880 | 493.300 | 745.136 |
| 50% | 402.800 | 548.804 | 666.067 | 551.727 |
| 75% | 444.367 | 252.471 | 599.367 | 170.348 |
| 90% | 507.000 | 224.169 | 615.667 | 130.375 |

The learned model is worse overall on held-out bearings, and better on both aggregate MAE and RMSE in the held-out-condition comparison. It is worse at the 25% stage in both comparisons. The 90% stage shows large improvements in both, but stage is defined using future lifetime for evaluation only, and is not an available operational switching signal. The baseline is unweighted empirical median of remaining lives among surviving training bearings; the HGB model uses equal-bearing training weights.

## Limitations and next questions
Only 15 physical assets and three operating conditions; endpoints within each bearing are dependent. All results are exploratory development evidence, not an untouched test set. Relative RMS and other vibration features are task-specific; no transfer of NASA weights occurred. Laboratory accelerated degradation and last-recording proxy are not equivalent to factory deployment or independently timed failure. Large between-bearing lifetime differences, early-life errors and possible distribution shift merit examination. Compare normalized per-bearing errors, condition-level differences and observable signal-based gating, rather than choosing a policy by true lifetime fraction. Future model changes require independent confirmation on additional assets. No state-of-the-art, industrial safety or realized savings claim.
