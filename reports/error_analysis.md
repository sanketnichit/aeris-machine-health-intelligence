# AERIS Error Analysis

This analysis uses the same primary seed-42 held-out test set as the risk-model report. It is descriptive only: no threshold or model change is made from these observations.

## Test-set outcome counts
- True positives: **50**
- False positives: **4**
- False negatives: **18**
- True negatives: **1,928**

## False-negative profile
- False-negative count: **18**
- Median model risk on false negatives: **0.092**
- Highest false-negative risk: **0.489**
- Lowest false-negative risk: **0.001**
- Failure-mode flags among false negatives:
  - TWF: **9**
  - HDF: **5**
  - PWF: **1**
  - OSF: **1**
  - RNF: **0**
  - Multiple mode flags: **0**

## False-positive profile
- False-positive count: **4**
- Median model risk on false positives: **0.689**
- Highest false-positive risk: **0.771**

## Interpretation

False negatives are the principal miss class at the 0.50 threshold. Their model scores remain below the alert cutoff even though the benchmark target is positive, which illustrates why a production alert policy would need an explicit cost for missed failures. The failure-mode counts are descriptive only because the AI4I mode labels are synthetic benchmark indicators rather than physical root-cause measurements.

The concentration of false negatives in the TWF flag is useful diagnostic evidence for future work: it supports keeping TWF as a limitation/extension rather than presenting the current mode layer as universally strong.

## Ranking check

Overall held-out average precision remains **0.849**. Error analysis is intentionally kept downstream of the fixed evaluation so it does not become an untracked tuning loop.
