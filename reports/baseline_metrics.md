# AERIS Baseline - Random Forest Failure Detector

## Split

- Stratified train/test split: 80/20
- Random seed: 42
- Features: machine type + five process variables
- Excluded: UDI, Product ID, and failure-mode flags to avoid leakage

## Test metrics

- Precision: **0.935**
- Recall: **0.426**
- F1: **0.586**
- PR-AUC (average precision): **0.771**
- ROC-AUC (secondary): 0.962

## Confusion matrix

Rows = actual, columns = predicted.

Predicted 0 | Predicted 1
Actual 0      1930 | 2
Actual 1        39 | 29

## Top feature importances

- numeric__torque_nm: 0.3025
- numeric__rot_speed_rpm: 0.2956
- numeric__tool_wear_min: 0.2033
- numeric__air_temp_k: 0.1035
- numeric__process_temp_k: 0.0759
- categorical__type_L: 0.0089
- categorical__type_M: 0.0064
- categorical__type_H: 0.0039

## Interpretation

This is the first ugly-but-working baseline. It establishes a complete prediction path before model comparison, SHAP, or calibration. Metrics are evaluated with precision, recall, F1 and PR-AUC because failures are a small minority class.
