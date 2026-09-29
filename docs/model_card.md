# Model Notes

## What this project is

AERIS is a BTech project where I am experimenting with a small predictive-maintenance pipeline using the AI4I 2020 dataset.

It currently covers:

- binary machine-failure prediction
- calibrated risk scores
- SHAP/permutation-based explanations
- a small Streamlit interface
- separate failure-mode experiments

## What it is not

I would not use this model for:

- real maintenance decisions
- safety-critical control
- an unknown production fleet
- claims about any specific industrial company or Formula 1 team

## Data

The model is trained on the AI4I 2020 Predictive Maintenance Dataset from UCI.

The dataset is synthetic. That matters when reading the results: the model is being tested on a controlled benchmark, not on live machine telemetry.

## Model inputs

Observed inputs:

- machine product type
- air temperature
- process temperature
- rotational speed
- torque
- tool wear

Derived inputs:

- temperature difference = process temperature - air temperature
- mechanical power = torque x rotational speed / 9549.2966

These derived features only use the observed inputs.

The following are excluded from the binary failure model:

- UDI
- Product ID
- TWF
- HDF
- PWF
- OSF
- RNF
- machine_failure

The failure-mode flags are target-side information, so using them for the main prediction would leak the answer.

## Main metrics

The main metric is average precision / PR-AUC because the failure class is small.

The current seed-42 result is:

- PR-AUC: 0.899
- Precision @ 0.50: 0.965
- Recall @ 0.50: 0.809
- F1 @ 0.50: 0.880
- Brier score: 0.0075

## Limitations

1. AI4I is synthetic.
2. The data is not a real longitudinal machine fleet.
3. Failure events are rare, so some smaller groups have little data.
4. Good benchmark performance does not prove physical causality.
5. Failure-mode labels can overlap.
6. The current risk score is a benchmark estimate, not a production probability.
7. The two derived features improve benchmark performance, but that may partly come from structure built into the synthetic dataset.
8. SHAP and permutation importance explain the model, not the physical machine.

## Checks in the repo

I also included:

- bootstrap intervals
- split-sensitivity checks
- calibration checks
- held-out error analysis
- feature-importance stability

These help show how sensitive the benchmark result is, but they are not a substitute for testing on real industrial data.
