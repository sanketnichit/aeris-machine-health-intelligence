# MFPT continuous order uncertainty — findings v1

[Protocol](MFPT_ORDER_UNCERTAINTY_PROTOCOL.md) · [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45577604589) · [Evidence](evidence/mfpt_order_uncertainty_summary.json)

Ten scenario combinations on the same 17 observed MFPT recordings: 170 repeated recording-scenario comparisons. The original CWRU thresholds are unchanged. The point comparator reproduces the earlier speed-error outcomes.

| Declared speed error | Point correct / incorrect | ±1% guard correct / incorrect | ±5% guard correct / incorrect |
|---|---:|---:|---:|
| -5% | 4 / 5 | 1 / 0 | 0 / 0 |
| -1% | 14 / 0 | 8 / 0 | 0 / 0 |
| 0% | 14 / 0 | 11 / 0 | 0 / 0 |
| +1% | 13 / 0 | 7 / 0 | 0 / 0 |
| +5% | 0 / 1 | 0 / 0 | 0 / 0 |

Each row has 14 fault recordings. All remaining cases are withheld. No normal control received a fault suggestion. The narrow guard retained 27 correct suggestions over 70 repeated fault assessments, sacrificing 18 correct point suggestions; the wide guard retained none, sacrificing 45. Each guard withheld all six incorrect point suggestions. Across the two repeated grids there were 12 prevented incorrect and 63 lost correct suggestions, not independent errors or assets.

The narrow declared interval excludes the reference speed at ±5% actual error. Its rejection of those erroneous suggestions is an observed outcome, not a guarantee outside the interval. For the wide guard, retained error is undefined, not zero: it accepts nothing. With accurate declared speed and ±1% uncertainty, 11/14 faults retain suggestions.

Guaranteed/possible harmonic masks provide a sufficient but potentially loose stability condition in the fixed-spectrum scalar model. Independent lower and upper extrema may occur at different scales. A tighter future method could partition the continuous interval at bin-membership change points and check the original rule across each region and boundary, with explicit conservative handling of numerical ties. This is a proposed development response, not an independently validated improvement.

No safe speed tolerance, calibrated error probability, hardware uncertainty measurement, variable-speed tracking, or field performance is established. This is a retrospective response to previously observed failures, not confirmatory testing. Raw MFPT waveforms are not redistributed; source attribution and CC BY-NC-SA 4.0 restrictions are recorded in the evidence. The original DOI release is unchanged.
