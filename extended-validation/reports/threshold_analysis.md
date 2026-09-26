# Threshold and Calibration Analysis

Thresholds are selected using out-of-fold predictions from the training partition only, then evaluated once on the untouched test partition.

| Objective | OOF threshold | Test precision | Test recall | Test F1 |
|---|---:|---:|---:|---:|
| F0.5 | 0.626 | 0.947 | 0.794 | 0.864 |
| F1 | 0.265 | 0.873 | 0.809 | 0.840 |
| F2 | 0.106 | 0.803 | 0.838 | 0.820 |

## Calibrated risk model

- PR-AUC: **0.899**
- Precision @ 0.50: **0.965**
- Recall @ 0.50: **0.809**
- F1 @ 0.50: **0.880**
- Brier score: **0.0075**

The visualization keeps 0.50 as the default calibrated risk threshold. Different operational costs would justify a different threshold.
