# AERIS Uncertainty & Error Audit

This is a **secondary robustness audit**. It does not change the model, threshold, or held-out test split. The final 20% test partition remains untouched during training and model selection.

## Held-out test composition
- Test rows: **2,000**
- Failures: **68**
- Non-failures: **1,932**

## Point estimates at calibrated threshold 0.50
- PR-AUC: **0.849**
- Precision: **0.926**
- Recall: **0.735**
- F1: **0.820**
- Brier score: **0.0108**

## 95% stratified bootstrap intervals
Bootstrap resamples preserve the observed number of positive and negative test examples in each resample. Intervals describe sampling uncertainty around this held-out evaluation; they are not guarantees of real-world performance.

| Metric | Estimate | 95% interval |
|---|---:|---:|
| PR-AUC | 0.8490 | [0.7760, 0.9143] |
| Precision | 0.9259 | [0.8519, 0.9818] |
| Recall | 0.7353 | [0.6324, 0.8382] |
| F1 | 0.8197 | [0.7434, 0.8889] |
| Brier score | 0.0108 | [0.0080, 0.0138] |

## Confusion matrix at 0.50

| | Predicted 0 | Predicted 1 |
|---|---:|---:|
| Actual 0 | 1928 | 4 |
| Actual 1 | 18 | 50 |

## Error profile
- False positives: **4** — normal observations flagged above the current threshold.
- False negatives: **18** — failures not flagged above the current threshold.
- Threshold changes therefore represent an explicit precision/recall trade-off rather than a universally correct operating point.

## Engineering interpretation
The headline risk-model metrics are useful, but the confidence intervals show that they should not be treated as exact constants. The positive class is small even in the held-out test set, so uncertainty matters. A real deployment would require prospective validation, drift monitoring, and threshold selection against explicit maintenance costs.
