# MFPT uncertainty: point-decision counterexample audit

Retrospective falsification-only experiment on the previously frozen 17 records and ten speed-error/uncertainty scenarios (170 record-scenarios, not independent observations). No threshold fitting or new external validation.

Of the 57 nominally correct suggestions withheld by breakpoint refinement, all 57 had a concrete evaluated point counterexample: 51 first witnessed an abstention and six first witnessed a different accepted suggestion. All 12 nominally incorrect withheld suggestions also had a witness: ten abstentions and two competing suggestions. There were 5,895 point evaluations across these searches. The first-witness type is not an exhaustive characterization of the interval.

Thus none of the 69 searched withheld suggestions could be accepted as an invariant nominal point decision over its declared interval. This does not establish the true fault at any particular speed, an independent error rate, or robustness outside the tested records. A competing suggestion need not be correct. No-witness outcomes, if encountered in future, would not constitute a proof of invariance.

Frozen protocol: source revision, source and prior evidence blob fingerprints, scenario grids, score floor and margin are preserved in [the registered summary](evidence/mfpt_counterexample_summary.json). The summary contains scenario aggregates; the workflow artifact contains the record-level witnesses.

- [Research workflow run](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45610868043)
- [Full CI](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45610867959)
- [Artifact](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45610868043/artifacts/15018544298)

The next question is whether a conservative set of possible point suggestions can expose ambiguity without replacing the existing fail-closed single-suggestion decision. Set membership must not be interpreted as a diagnosis or calibrated probability.
