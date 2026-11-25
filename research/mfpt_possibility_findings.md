# MFPT possible-suggestion outer sets — findings v1

[Protocol](mfpt_possibility_protocol.md) · [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45611640755) · [Evidence](evidence/mfpt_possibility_summary.json)

Retrospective research on the same 17 observed recordings, 14 fault and 3 normal, across ten scenarios (170 repeated recording-scenario comparisons). All previous point, global, refined and counterexample aggregates reproduced. Every observed non-null nominal, refined and witnessed suggestion was included in the outer sets. No partition-budget fallback occurred.

| Declared speed error | Width | Empty | One label | Two labels | Three labels | Fault truth included / 14 |
|---:|---:|---:|---:|---:|---:|---:|
| -5% | 1% | 3 | 10 | 4 | 0 | 7 |
| -5% | 5% | 3 | 5 | 3 | 6 | 14 |
| -1% | 1% | 3 | 14 | 0 | 0 | 14 |
| -1% | 5% | 3 | 7 | 3 | 4 | 14 |
| 0% | 1% | 3 | 14 | 0 | 0 | 14 |
| 0% | 5% | 3 | 7 | 7 | 0 | 14 |
| 1% | 1% | 3 | 14 | 0 | 0 | 14 |
| 1% | 5% | 3 | 8 | 6 | 0 | 14 |
| 5% | 1% | 10 | 6 | 1 | 0 | 2 |
| 5% | 5% | 3 | 6 | 8 | 0 | 14 |

Overall outer-set sizes: 37, 91, 32, 10 for sizes zero through three. Of the 137 withheld record-scenarios, the respective set sizes are 37, 58, 32, 10. Closed-cell bounds narrow the global outer set in 101/170 cases. Fault truth membership is 121/140; when the reference speed lies within the declared scale interval it is 112/112. No normal control had a nonempty set in 30 repeated assessments.

A singleton is not a stable suggestion, and an empty set does not establish health. These are necessary-condition outer sets, not exact attainable sets, confidence sets, probabilities or diagnoses. No independent population or field validation was performed.

The next development audit should vary declared uncertainty around fixed speed centers, separating cases in which the reference speed is contained from intentionally misbounded cases. Narrower intervals may establish stability without establishing correctness. No hardware accuracy requirement can be inferred directly from this synthetic metadata perturbation.
