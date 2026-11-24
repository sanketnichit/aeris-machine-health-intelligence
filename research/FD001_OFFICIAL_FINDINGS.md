# FD001 official endpoint findings — frozen v1

Execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45427268184
Frozen implementation: ca631cfa5f444cefce671f3e84878bb1f987d0d2
Protocol: [FD001_OFFICIAL_PROTOCOL.md](FD001_OFFICIAL_PROTOCOL.md)
Exact reported metrics and fingerprints: [official_summary.json](evidence/official_summary.json)

All five candidates were evaluated at the final observed cycle of each of the 100 official simulated test engines, after freezing the protocol. No candidate was selected or tuned on these labels.

| Model | MAE | RMSE | NASA penalty | Mean signed error | Overprediction >20 cycles |
|---|---:|---:|---:|---:|---:|
| Age reference | 29.160 | 36.122 | 7600.14 | 0.830 | .29 |
| Constant | 39.080 | 49.820 | 166570.54 | 27.480 | .47 |
| Snapshot HGB | 20.021 | 27.355 | 10445.82 | 10.436 | .30 |
| Relative HGB (primary) | 17.346 | 25.061 | 12852.02 | 8.344 | .24 |
| Adaptive mean (secondary) | 15.328 | 21.358 | 1635.71 | 6.762 | .22 |

Primary versus age reference: MAE difference -11.814 cycles (exploratory percentile 95% paired bootstrap interval [-16.814, -6.878]); engine win fraction .71. The primary model improves MAE but worsens the asymmetric NASA penalty versus the age reference. The adaptive comparator achieves the lowest reported MAE, RMSE and NASA penalty. Preserve primary designation; do not tune the blend or select a deployment model on these test outcomes.

The official test set is now observed and cannot serve as an untouched confirmation set for future modifications. Uncertainty coverage and maintenance decisions were not evaluated by this official protocol. FD001 is simulated and the results do not establish physical fleet performance, safety, novelty or state-of-the-art status.
