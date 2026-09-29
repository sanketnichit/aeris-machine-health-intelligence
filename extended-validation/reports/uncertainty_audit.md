# Uncertainty Check

This is an extra check on the main result. It does not change the model, threshold or test split.

## Held-out test composition

- Test rows: **2,000**
- Failures: **68**
- Non-failures: **1,932**

## Point estimates at calibrated threshold 0.50

- PR-AUC: **0.899**
- Precision: **0.965**
- Recall: **0.809**
- F1: **0.880**
- Brier score: **0.0075**

## 95% stratified bootstrap intervals

The bootstrap keeps the same number of positive and negative examples in each resample. The intervals show uncertainty around this test-set result; they are not guarantees for real machines.

| Metric | Estimate | 95% interval |
|---|---:|---:|
| PR-AUC | 0.8986 | [0.8350, 0.9533] |
| Precision | 0.9649 | [0.9153, 1.0000] |
| Recall | 0.8088 | [0.7206, 0.8971] |
| F1 | 0.8800 | [0.8167, 0.9375] |
| Brier score | 0.0075 | [0.0050, 0.0102] |

## Confusion matrix at 0.50

| | Predicted 0 | Predicted 1 |
|---|---:|---:|
| Actual 0 | 1930 | 2 |
| Actual 1 | 13 | 55 |

## Error profile

- False positives: **2** — normal observations flagged above the current threshold.
- False negatives: **13** — failures not flagged above the current threshold.
- Threshold changes therefore represent an explicit precision/recall trade-off rather than a universally correct operating point.

## What this means

The main metrics look strong on this split, but the intervals show they can move. There are only 68 failures in the test set, so I would not treat the displayed numbers as fixed constants.
