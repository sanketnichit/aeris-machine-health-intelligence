# AERIS Risk Model

## Model

HistGradientBoostingClassifier with the two derived features and sigmoid probability calibration using 5-fold cross-validation on the training data.

Derived features:

- temp_delta_k: process temperature minus air temperature
- mechanical_power_kw: torque × rotational speed / 9549.2966

## Test results

- Precision @ 0.50: **0.965**
- Recall @ 0.50: **0.809**
- F1 @ 0.50: **0.880**
- PR-AUC: **0.899**
- Brier score: **0.0075**

## Calibration

For the same test set:

- Sigmoid calibration Brier score: **0.00752**
- Isotonic calibration Brier score: **0.00742**

I kept sigmoid because the ranking is almost the same and the mapping is simpler for this small positive class.

## Thresholds

I picked the example thresholds below from out-of-fold predictions on the training data and then checked them once on the test set.

| Objective | OOF threshold | Test precision | Test recall | Test F1 |
|---|---:|---:|---:|---:|
| F0.5 | 0.626 | 0.947 | 0.794 | 0.864 |
| F1 | 0.265 | 0.873 | 0.809 | 0.840 |
| F2 | 0.106 | 0.803 | 0.838 | 0.820 |

The Streamlit demo uses **0.50** as the default threshold. That is just the current demo setting; a real maintenance system would need its own threshold.

## Notes

The displayed risk is a model estimate for the AI4I machine-failure label. It is not a physical measurement of machine health.

The derived features improve the benchmark result, but AI4I is synthetic. Testing on real machine data would be needed before using the model for maintenance decisions.
