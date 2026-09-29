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

## Which model I kept

I kept HistGradientBoosting based on the training-side cross-validation results. Random Forest was close on PR-AUC, but HGB had better recall and F1. I did not use the test-set numbers to make that choice.

## What this means

The derived features improve the benchmark result. That does not prove the transformations are physically causal, and AI4I is synthetic.

## Where I use it

The same HGB setup is reused for the calibrated risk model, explanations and Streamlit app. The alert threshold is kept separate from probability calibration.
