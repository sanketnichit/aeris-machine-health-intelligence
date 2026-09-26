# AERIS Risk Model

## Model

HistGradientBoostingClassifier with sigmoid probability calibration using 5-fold cross-validation on the training partition.

## Held-out test results

- Precision @ 0.50: **0.926**
- Recall @ 0.50: **0.735**
- F1 @ 0.50: **0.820**
- PR-AUC: **0.849**
- Brier score: **0.0108**

## Calibration

The calibration curve is included in figures/calibration_curve.png.

For the same held-out test set:

- Sigmoid calibration Brier score: **0.0108**
- Isotonic calibration Brier score: **0.0104**
- Sigmoid was retained for v1 because it provides comparable ranking performance with a simpler and more conservative calibration assumption for this small positive class.

## Decision threshold

A threshold is a deployment decision, not a property of the trained model.

Using out-of-fold predictions from the training partition, the F1-optimal raw-model threshold was approximately **0.765**. At that operating point, the untouched test set produced:

- Precision: **0.852**
- Recall: **0.765**
- F1: **0.806**

AERIS keeps **0.50 on the calibrated risk score** as the default UI decision threshold because it is easy to interpret and separates the continuous risk estimate from an application-specific alert policy.

## Interpretation

The displayed AERIS risk is a calibrated model estimate for the positive machine-failure label under this benchmark. It is not a physical measurement of machine health and should not be represented as a guaranteed production failure probability.

If the operational cost of missed failures were known, threshold selection should be revisited against those explicit costs.
