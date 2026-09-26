# Model Comparison

## Evaluation design

- 80/20 stratified train/test split (random seed 42).
- Model selection uses only 5-fold stratified CV on the training set.
- The final test set is evaluated once after model selection.
- Primary metric: average precision (PR-AUC/AP), because failures are rare.
- Secondary metrics: precision, recall, F1 and ROC-AUC.

## Results

| Model | CV PR-AUC | CV Recall | CV F1 | Test PR-AUC | Test Precision | Test Recall | Test F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| HistGradientBoosting | 0.800 ± 0.041 | 0.764 | 0.732 | 0.843 | 0.873 | 0.706 | 0.780 |
| Random Forest | 0.758 ± 0.026 | 0.384 | 0.544 | 0.773 | 0.935 | 0.426 | 0.586 |
| Logistic Regression | 0.435 ± 0.028 | 0.804 | 0.235 | 0.396 | 0.144 | 0.824 | 0.245 |

## Selection

HistGradientBoosting is the current model to carry forward. It gives the strongest cross-validated PR-AUC in this experiment without requiring an external XGBoost dependency.

## Next step

Calibrate the selected model's probabilities for the risk score, then add feature-level explanations. Threshold selection remains a separate decision from probability calibration.
