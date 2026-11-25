# MFPT breakpoint refinement — findings v1

[Protocol](MFPT_BREAKPOINT_PROTOCOL.md) · [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45578426202) · [Evidence](evidence/mfpt_breakpoint_summary.json)

The frozen retrospective experiment completed on 17 previously observed recordings (14 fault, 3 normal), across ten scenarios, or 170 repeated recording-scenario comparisons. Point and global-bound aggregates match the registered prior uncertainty audit. CWRU thresholds remain unchanged.

| Declared speed error | Point correct / incorrect | Global ±1% | Refined ±1% | Global ±5% | Refined ±5% |
|---|---:|---:|---:|---:|---:|
| -5% | 4 / 5 | 1 / 0 | 4 / 0 | 0 / 0 | 0 / 0 |
| -1% | 14 / 0 | 8 / 0 | 8 / 0 | 0 / 0 | 0 / 0 |
| 0% | 14 / 0 | 11 / 0 | 13 / 0 | 0 / 0 | 0 / 0 |
| +1% | 13 / 0 | 7 / 0 | 8 / 0 | 0 / 0 | 0 / 0 |
| +5% | 0 / 1 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

The narrow guard recovers six of 18 previously lost correct point suggestions: three at -5%, two at accurate speed, and one at +1%. It retains 33/70 repeated fault assessments versus 27/70 previously. No new incorrect or normal fault suggestions were observed. No partition-budget abstentions occurred. The wide guard recovers none of the 45 previously lost correct suggestions; retained error remains undefined because it accepts nothing. Across both grids, six of 63 previously lost correct suggestions are recovered.

The -5% speed-error narrow-interval recovery is outside reference-speed containment, so it is not evidence of robustness to a correctly bounded uncertainty interval. With accurate declared speed, the narrow guard retains 13/14 versus 11/14. These are repeated observations on the same recordings, not independent samples. The sufficient closed-cell method does not prove that every unresolved case is genuinely unstable; the next diagnostic experiment should distinguish an explicit conflicting point decision from unresolved numerical/bound conservatism. A finite point counterexample can falsify stability, but agreement on sampled points cannot certify it.

No field performance, safe speed tolerance, calibrated risk, hardware uncertainty, variable-speed tracking or independent validation is established. Raw MFPT data are not redistributed. See the registered evidence for attribution and provenance. The original DOI release is unchanged.
