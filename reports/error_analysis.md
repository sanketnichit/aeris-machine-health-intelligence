# AERIS Error Analysis

This analysis uses the same primary seed-42 held-out test set as the risk-model report. It is descriptive only: no threshold or model change is made from these observations.

## Test-set outcome counts

- True positives: **55**
- False positives: **2**
- False negatives: **13**
- True negatives: **1,930**

## False-negative profile

- False-negative count: **13**
- Median model risk on false negatives: **0.063**
- Highest false-negative risk: **0.404**
- Lowest false-negative risk: **0.002**
- Failure-mode flags among false negatives:
  - TWF: **9**
  - HDF: **0**
  - PWF: **1**
  - OSF: **1**
  - RNF: **0**
  - Multiple mode flags: **0**

## False-positive profile

- False-positive count: **2**
- Median model risk on false positives: **0.631**
- Highest false-positive risk: **0.740**

## Interpretation

False negatives are the principal miss class at the 0.50 threshold. Their model scores remain below the alert cutoff even though the benchmark target is positive, which illustrates why a production alert policy would need an explicit cost for missed failures.

The concentration of false negatives in the TWF flag is useful diagnostic evidence for future work. It supports keeping TWF as a limitation/extension rather than presenting the current mode layer as universally strong.

## Ranking check

Overall held-out average precision remains **0.899**. Error analysis is intentionally kept downstream of the fixed evaluation so it does not become an untracked tuning loop.
