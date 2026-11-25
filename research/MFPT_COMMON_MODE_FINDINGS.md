# MFPT common-mode measurement error — findings

[Protocol](MFPT_COMMON_MODE_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45613822665) | [Evidence](evidence/mfpt_common_mode_summary.json)

120 scenarios reuse 17 physical recordings (2,040 recording-scenario comparisons, 1,680 fault and 360 normal). All zero-common fusion aggregates reproduced. The full numerical audit and 52 targeted tests passed at the recorded revision.

| Assumed common error | Fault assessments | Correct accepted | Incorrect accepted | Compatible without reference | Accepted outside reference | Differential conflicts |
|---:|---:|---:|---:|---:|---:|---:|
| 0% | 560 | 348 | 0 | 170 | 74 | 0 |
| 1% | 560 | 205 | 0 | 68 | 0 | 34 |
| 5% | 560 | 0 | 0 | 0 | 0 | 170 |

All 72 scenarios in which the declared error decomposition was valid contained the reference (1,224 repeated assessments); 464 of 1,008 fault assessments were correctly accepted. No wrong accepted suggestions or normal false suggestions were observed on this grid. Across all scenarios, the 1% common-mode bound removed the observed 74 acceptances outside reference containment, but 68 compatible intersections still excluded the reference under invalid assumptions. The 5% bound removed all false agreement here, but withheld every fault suggestion. Neither result establishes a generally safe bound.

Differential disagreement can identify conflicts hidden by simply widening each channel's error interval. Shared bias is not inferable from agreement alone. A validated external reference remains necessary. The same measured records recur across artificial metadata perturbations; no new sensor recordings, calibrated instrumentation, independent fault population, or field safety claim.

The post-audit calibration enrollment and capture-to-advisory implementation are separately tested engineering components, not claims validated by this numerical run.
