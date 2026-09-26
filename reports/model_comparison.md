# Model Comparison

## Evaluation design
- 80/20 stratified train/test split (random seed 42).
- Model selection uses only 5-fold stratified cross-validation on the training set.
- The final test set is evaluated once after model selection.
- Primary metric: average precision (PR-AUC/AP), because failures are rare.
- Secondary metrics: precision, recall, F1 and ROC-AUC.
- Logistic Regression uses numeric standardization; tree models use raw numeric scales.

## Feature set

AERIS v1 uses the six observed operating inputs plus two deterministic engineering-derived signals:

- `temp_delta_k` = process temperature - air temperature
- `mechanical_power_kw` = torque × rotational speed / 9549.2966

The derived signals use only observed input variables and do not use machine-failure or failure-mode labels.

## Results

| Model | CV PR-AUC | CV Recall | CV F1 | Test PR-AUC | Test Precision | Test Recall | Test F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| HistGradientBoosting | 0.871 ± 0.030 | 0.727 | 0.810 | 0.895 | 0.931 | 0.794 | 0.857 |
| Random Forest | 0.872 ± 0.029 | 0.668 | 0.792 | 0.857 | 0.941 | 0.706 | 0.807 |
| Logistic Regression | 0.484 ± 0.025 | 0.823 | 0.274 | 0.466 | 0.177 | 0.868 | 0.294 |

## Selection

HistGradientBoosting is the current model carried forward based on the training-partition cross-validation record. Random Forest is nearly tied on CV PR-AUC, while HGB has higher CV recall and F1. The held-out test results are reported for final comparison only and are not used to tune or select the model.

## Engineering interpretation

The derived features materially improve the benchmark model. This should be interpreted as a benchmark result, not proof that these two transformations are physically causal or sufficient for a real machine fleet. AI4I is synthetic, and its target generation can contain structured relationships between the operating variables and failure labels.

## Downstream use

The selected HGB architecture is carried into the calibrated risk model, explainability workflow and Streamlit console. Threshold selection remains a separate deployment decision from probability calibration.
