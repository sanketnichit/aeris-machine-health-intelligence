# Threshold Analysis

The model produces a continuous score. The classification threshold controls the precision/recall trade-off and should be chosen based on operating costs.

Thresholds below were selected using **out-of-fold predictions on the training partition only** and then evaluated once on the untouched test partition.

| Selection objective | OOF threshold | Test precision | Test recall | Test F1 |
|---|---:|---:|---:|---:|
| F0.5 (precision-weighted) | 0.923 | 0.941 | 0.706 | **0.807** |
| F1 balanced | 0.765 | 0.852 | 0.765 | **0.806** |
| F2 (recall-weighted) | 0.369 | 0.701 | 0.794 | **0.745** |

## Decision

For the portfolio demo, AERIS uses the **calibrated 0.50 risk threshold** in the UI and presents the continuous risk score alongside it.

The threshold study remains visible in the repository because it demonstrates that an alert threshold is an explicit engineering decision rather than an arbitrary model default.

The production threshold should depend on the relative cost of false negatives and false positives.
