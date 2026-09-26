# AERIS Risk Model

## Model

HistGradientBoostingClassifier with deterministic engineering-derived features and sigmoid probability calibration using 5-fold cross-validation on the training partition.

Derived features:
- `temp_delta_k`: process temperature minus air temperature.
- `mechanical_power_kw`: torque × rotational speed / 9549.2966.

## Held-out test results

- Precision @ 0.50: **0.965**
- Recall @ 0.50: **0.809**
- F1 @ 0.50: **0.880**
- PR-AUC: **0.899**
- Brier score: **0.0075**

## Calibration choice

For the same held-out test set:

- Sigmoid calibration Brier score: **0.00752**
- Isotonic calibration Brier score: **0.00742**

Sigmoid was retained for v1 because ranking performance is essentially unchanged while the calibration mapping remains simpler and less flexible for a small positive class.

## Decision threshold

A threshold is a deployment decision, not a property of the trained model.

Using out-of-fold predictions from the training partition, the raw-model thresholds below produced the following untouched-test results:

| Objective | OOF threshold | Test precision | Test recall | Test F1 |
|---|---:|---:|---:|---:|
| F0.5 | 0.626 | 0.947 | 0.794 | 0.864 |
| F1 | 0.265 | 0.873 | 0.809 | 0.840 |
| F2 | 0.106 | 0.803 | 0.838 | 0.820 |

AERIS keeps **0.50 on the calibrated risk score** as the default UI decision threshold because it is simple to interpret and separates the continuous risk estimate from an application-specific alert policy.

## Interpretation

The displayed AERIS risk is a calibrated model estimate for the positive machine-failure label under this benchmark. It is not a physical measurement of machine health and should not be represented as a guaranteed production failure probability.

The improvement from the engineered features is encouraging, but AI4I is synthetic. A real deployment would require prospective validation, calibration checks on the target population, drift monitoring, and threshold selection against explicit maintenance costs.
