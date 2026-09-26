# AERIS Risk Model

## Model

HistGradientBoostingClassifier with sigmoid probability calibration using 5-fold cross-validation on the training set.

## Held-out test results

- Precision @ 0.50: **0.926**
- Recall @ 0.50: **0.735**
- F1 @ 0.50: **0.820**
- PR-AUC: **0.849**
- Brier score: **0.0108** (lower is better)

## How to interpret the AERIS risk score

The score is a calibrated model probability estimate for the positive failure label under this benchmark. It is not a physical measurement of machine health and should not be presented as a guaranteed failure probability in a production setting.

## Why calibration

A risk score is more useful than a raw class label when the application needs a graded level of concern. Calibration is therefore evaluated separately from ranking metrics such as PR-AUC.
