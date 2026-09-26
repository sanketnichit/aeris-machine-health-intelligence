# AERIS 90-Second Demo Script

## 0-10 seconds — problem

Say:

> "AERIS is an explainable predictive-maintenance prototype. It takes a machine operating state and estimates failure risk, then shows which input signals are driving the model and which benchmark failure modes deserve attention."

## 10-25 seconds — input

Use this held-out test-set failure example:

- Product type: **L**
- Air temperature: **300.8 K**
- Process temperature: **309.9 K**
- Rotational speed: **1312 rpm**
- Torque: **65.3 Nm**
- Tool wear: **192 min**

This is an actual observation from the untouched benchmark test partition. Do not edit the values during the demo.

## 25-45 seconds — risk

Point to:

- failure-risk score
- current state
- alert threshold

Say:

> "The risk score is calibrated for the AI4I benchmark. I deliberately separate the continuous score from the alert threshold because the operating cost of false negatives versus false positives is a deployment decision."

## 45-65 seconds — explanation

Point to the SHAP chart.

Say:

> "This is the local explanation. Positive contributions push the underlying model toward the failure class; negative contributions push it away. These are model attributions, not claims of physical causality."

## 65-80 seconds — failure modes

Point to HDF / PWF / OSF.

Say:

> "The source data permits overlapping failure mechanisms, so I report separate mode scores instead of forcing the machine into one diagnosis. I also deliberately excluded sparse or unstable modes from the v1 panel."

## 80-90 seconds — engineering judgement

Finish with:

> "The interesting part is not the dashboard. It is the evaluation discipline behind it: severe class imbalance, PR-AUC as the primary metric, held-out testing, probability calibration, threshold analysis, leakage controls and explicit dataset limitations."

## Backup example

For a low-risk demonstration:

- Product type: **L**
- Air temperature: **297.6 K**
- Process temperature: **308.6 K**
- Rotational speed: **1576 rpm**
- Torque: **32.7 Nm**
- Tool wear: **83 min**

This observation is also from the untouched test partition and is labelled non-failure in the benchmark.
