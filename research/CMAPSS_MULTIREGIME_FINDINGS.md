# NASA C-MAPSS multi-regime evaluation — findings

[Protocol](CMAPSS_MULTIREGIME_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45614582324) | [Evidence](evidence/cmapss_multiregime_summary.json)

The exact original NASA archive and all twelve extracted members were fingerprinted. All five FD001 MAEs reproduced with zero drift; all FD001 reported risk metrics reproduced. 707 distinct official subset/test-unit identities, 607 newly evaluated endpoints, 1,314 repeated scenario endpoint comparisons. Eight targeted tests passed.

| Subset | Training mode | Test engines | Age MAE | Snapshot MAE | Frozen primary MAE | Adaptive MAE | Primary overprediction >20 cycles |
|---|---|---:|---:|---:|---:|---:|---:|
| FD001 | fd001_transfer | 100 | 29.160 | 20.021 | 17.346 | 15.328 | 24.0% |
| FD002 | fd001_transfer | 259 | 30.668 | 53.195 | 66.747 | 57.289 | 80.7% |
| FD002 | within_subset | 259 | 30.840 | 20.028 | 21.247 | 20.612 | 23.9% |
| FD003 | fd001_transfer | 100 | 30.095 | 36.461 | 33.209 | 28.876 | 57.0% |
| FD003 | within_subset | 100 | 32.725 | 25.185 | 20.692 | 18.759 | 24.0% |
| FD004 | fd001_transfer | 248 | 41.421 | 51.489 | 63.278 | 55.236 | 73.8% |
| FD004 | within_subset | 248 | 44.282 | 27.301 | 27.697 | 27.553 | 36.3% |

Direct FD001 transfer fails to beat the age-only comparator in MAE on all three new subsets. The paired primary-minus-age MAE bootstrap interval excludes zero in the unfavorable direction for FD002 and FD004, but includes zero for FD003. FD002 direct primary transfer overpredicts by more than 20 cycles on 80.7% of endpoints and has NASA score 65,804,619; FD004 has 73.8% overprediction and score 46,971,541. These are major asymmetric-risk failures, not deployment candidates.

Using each subset's own complete training trajectories, the frozen primary improves MAE over age-only for all three new subsets. Snapshot HGB has lower MAE than relative HGB on FD002 and FD004; adaptive blending has lower MAE than relative HGB on all three. This is descriptive comparison, not post-test candidate selection. Lower MAE alone does not imply lower asymmetric risk. See the evidence for the complete metrics and paired intervals; record-level forecasts are preserved in the workflow artifact.

No claims of independent simulator, physical asset, calibrated uncertainty or prospective field performance. All official test labels for these subsets are now observed; never tune on them. Future work should use training-unit-disjoint development folds and a genuinely untouched external population, and require an explicit operating-regime applicability gate rather than deploying an FD001 model on unfamiliar regimes.
