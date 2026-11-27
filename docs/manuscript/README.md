# Frozen evidence and manuscript scope

Source archive: [AERIS v0.2.0](https://doi.org/10.5281/zenodo.24533914), revision 5e6aba8f01f0a35347698c4c45661b09db7a92ca. MFPT [summary](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/5e6aba8f01f0a35347698c4c45661b09db7a92ca/research/evidence/mfpt_common_mode_summary.json), [protocol](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/5e6aba8f01f0a35347698c4c45661b09db7a92ca/research/MFPT_COMMON_MODE_PROTOCOL.md), [run](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45613822665). Paderborn [findings](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/5e6aba8f01f0a35347698c4c45661b09db7a92ca/research/PADERBORN_CONDITIONAL_FINDINGS.md), [run](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45619064703).

Reaggregated archived MFPT summary (40 scenarios per bound, 14 fault and 3 normal recordings reused per scenario):

| Bound | Fault assessments | Correct | Wrong | Fault abstentions | Normal false suggestions | Feasible without reference | Accepted without reference |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0% | 560 | 348 | 0 | 212 | 0 | 170 | 74 |
| 1% | 560 | 205 | 0 | 355 | 0 | 68 | 0 |
| 5% | 560 | 0 | 0 | 560 | 0 | 0 | 0 |

There are 17 distinct recordings, not 2,040 independent measurements. Perturbations are synthetic metadata errors on measured waveforms. The reference is the benchmark reference used for injection, not a certified tachometer. Accepted-without-reference is a failure of declared containment, not necessarily a wrong fault label. At zero coverage retained error is undefined. No general safety bound follows.

Paderborn is a distinct conditional transfer case: 17 specimens, 68 recordings, 44 damaged and 24 healthy; 6 correct, 0 wrong damaged suggestions, 38 damaged abstentions, 3 healthy false suggestions per timing hypothesis. Agreement 68/68, including 59 paired abstentions. 56 nonpilot recordings, 3 correct of 36 damaged, 33 damaged abstentions and 3/20 healthy false suggestions. All false suggestions on K003; 3/11 damaged specimens have any correct suggestion. No geometry visual review or clock calibration. The two time interpretations are paired, not independent sensor measurements, and do not test the common-mode model directly. They illustrate a related but distinct failure of decision agreement as evidence of validity.

## Manuscript decision

Proceed with a *retrospective bounded-error diagnostic reliability case study*, conditional on novelty review and author understanding. Proposed title: When sensor agreement is not enough: a bounded-error case study of selective bearing fault diagnosis. Core contribution: explicit distinction between reference feasibility, decision invariance and label correctness, supported by a scalar shared-error projection and reproducible negative transfer case. Not a new general metrology theorem; not a claim of validated sensors, field-ready system, statistically independent replicated outcomes or a novel universal classifier.

Next: citation-chain review, author/expert review of proof, verify full record-level provenance and breakpoint guard, produce figures and write manuscript. No further AERIS release development or threshold tuning. If a new confirmatory experiment becomes necessary, treat it as a separate preregistered scope and do not silently reuse observed outcomes as validation. No preprint submission until author approval and rights review.
