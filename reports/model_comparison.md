# Model Comparison

## Evaluation design

- 80/20 stratified train/test split, random seed 42.
- Model selection uses only 5-fold stratified cross-validation on the training partition.
- The final test partition is not used for model selection.
- Primary metric: average precision (PR-AUC/AP), because machine failures are rare.
- Secondary metrics: precision, recall, F1 and ROC-AUC.
- No failure-mode flags are used as input features; they are target-side information.

## Results

| Model | CV PR-AUC | CV Recall | CV F1 | Test PR-AUC | Test Precision | Test Recall | Test F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **HistGradientBoosting** | **0.803 ± 0.038** | 0.646 | **0.726** | **0.843** | 0.873 | 0.706 | 0.780 |
| Random Forest | 0.758 ± 0.026 | 0.384 | 0.544 | 0.773 | **0.935** | 0.426 | 0.586 |
| Logistic Regression | 0.435 ± 0.028 | **0.804** | 0.235 | 0.396 | 0.144 | **0.824** | 0.245 |

## Interpretation

HistGradientBoosting is the current v1 model because it provides the strongest precision-recall ranking performance and a much better balance between missed failures and false alarms than the other tested baselines.

Random Forest is highly precise at the default 0.50 threshold but misses many failures. Logistic Regression catches more failures but produces an unacceptable false-alarm burden at that threshold.

The final AERIS risk score uses the HistGradientBoosting family with probability calibration.
