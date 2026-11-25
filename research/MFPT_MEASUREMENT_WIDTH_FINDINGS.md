# MFPT measurement-width sweep — findings

[Protocol](MFPT_MEASUREMENT_WIDTH_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45612220923) | [Evidence](evidence/mfpt_measurement_width_summary.json)

The 30 scenarios repeat 17 recordings (510 record-scenarios, 420 fault and 90 normal). Previously registered 1% and 5% point/global/refined results reproduced. No partition-budget abstention or narrower unresolved grid point was observed.

| Reference containment | Fault assessments | Correct accepted | Incorrect accepted | Withheld |
|---|---:|---:|---:|---:|
| contained | 196 | 88 | 0 | 108 |
| outside | 224 | 84 | 7 | 133 |

No normal false suggestion in 90 repeated normal assessments. All seven incorrect stable suggestions occurred outside containment: five at -5% bias and 0.1% width, one each at +5% bias and 0.1% or 0.25% width. At zero error all 14 fault records were correctly accepted at each of the 0.1%, 0.25% and 0.5% widths. These are retrospective repeated observations, not independent sample counts or a field error estimate.

The next experiment should model an explicitly supplied bound on systematic bias separately from repeatability, and compare using repeatability alone versus their conservative composition. The assumed bound is not inferred from the fault spectrum and must not be treated as a measured sensor specification.
