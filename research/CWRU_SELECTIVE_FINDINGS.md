# CWRU selective diagnosis findings — frozen v1

[Protocol](CWRU_SELECTIVE_PROTOCOL.md) · [Successful execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45561620601) · [Registered summary](evidence/cwru_selective_summary.json)

The frozen development procedure selected an envelope score floor of 0.00974446327636002 and relative margin threshold 0.80. On the 16 development fault recordings, four suggestions were accepted, all inner-race and all correct. All four development normal recordings were withheld by construction. These are selection outcomes, not independent validation.

On 12 previously unevaluated 0.021-inch seeded-fault recordings (72 windows, 589824 samples), forced top-order ranking produced 8 correct and 4 incorrect suggestions. The frozen selective rule retained six correct suggestions, zero incorrect suggestions, and withheld six (including two otherwise correct inner-race suggestions).

| Fault | Forced correct | Accepted correct | Incorrect accepted | Withheld |
|---|---:|---:|---:|---:|
| Inner | 4 | 2 | 0 | 2 |
| Ball | 0 | 0 | 0 | 4 |
| Outer | 4 | 4 | 0 | 0 |
| Total | 8 | 6 | 0 | 6 |

Coverage 50%; observed retained error 0/6. This is not a zero-risk guarantee. All four rolling-element cases remain unresolved. No held-out normal controls were evaluated. Same-rig repeated loads and windows are correlated; six accepted recordings are not six independent physical bearings. No calibrated probabilities, operational alarm thresholds, independent-platform generalization, or remaining-life prediction are established. Do not tune the policy on this observed severity group and call the result confirmatory.

Record-level evidence is extracted from the successful run's printed output, and the full per-window artifact and environment are linked in the summary. Original v0.1.0 archive is unchanged. Future work: independent rig evaluation with documented bearing geometry and sampling, independent normal controls, and explicit unknown-fault abstention. No operational policy is promoted.
