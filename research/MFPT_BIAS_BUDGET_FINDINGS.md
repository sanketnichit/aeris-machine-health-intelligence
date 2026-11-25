# MFPT declared bias budget — findings

[Protocol](MFPT_BIAS_BUDGET_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45612729793) | [Evidence](evidence/mfpt_bias_budget_summary.json)

45 scenarios repeat 17 recordings (765 record-scenarios). Each assumed bias bound repeats 210 fault and 45 normal assessments. All previously registered repeatability-only aggregates reproduced. Zero unknown-bias acceptances, normal false suggestions, partition-budget abstentions, or newly accepted suggestions after composition.

| Assumed systematic bound | Correct accepted | Incorrect accepted | Fault abstentions | Correct withheld relative to repeatability-only |
|---:|---:|---:|---:|---:|
| 0% | 115 | 6 | 89 | 0 |
| 1% | 70 | 0 | 140 | 45 |
| 5% | 0 | 0 | 210 | 115 |

The 1% assumption eliminated six errors in this particular retrospective grid, even though it did not contain every injected bias. This is not evidence that the 1% assumption is safe for uncalibrated instruments. At the 1% bound, 66 of 126 fault assessments with reference containment were correctly accepted; four other correct acceptances were outside containment. The 5% assumption covered all injected bias levels but withheld every suggestion. All six errors at zero assumed bias occurred outside reference containment.

The new guard uses a declared deterministic error budget, not a statistically calibrated confidence interval. The same records recur throughout, and no real tachometer calibration, sensor noise simulation, or external population validation has been performed. A narrower bound is justified only by independent measurement evidence. Next: evaluate a second independent measurement channel through interval intersection, retaining conflicts as abstentions and explicitly auditing false bounds.
