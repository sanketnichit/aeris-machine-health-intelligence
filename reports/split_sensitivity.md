# AERIS Split-Sensitivity Audit

This audit evaluates the **fixed v1 calibrated HGB model** across five independent stratified 80/20 train/test splits. The model hyperparameters and 0.50 threshold are held fixed; the alternate splits are not used to tune the model or replace the primary held-out evaluation.

## Results by split

| Seed | Test failures | PR-AUC | Precision | Recall | F1 | Brier |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 68 | 0.849 | 0.926 | 0.735 | 0.820 | 0.0108 |
| 7 | 68 | 0.792 | 0.909 | 0.588 | 0.714 | 0.0132 |
| 21 | 68 | 0.809 | 0.839 | 0.691 | 0.758 | 0.0127 |
| 84 | 68 | 0.875 | 0.904 | 0.691 | 0.783 | 0.0101 |
| 123 | 68 | 0.801 | 0.807 | 0.676 | 0.736 | 0.0130 |

## Fixed-model summary

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| PR-AUC | 0.8252 | 0.0355 | 0.7920 | 0.8753 |
| Precision | 0.8770 | 0.0511 | 0.8070 | 0.9259 |
| Recall | 0.6765 | 0.0540 | 0.5882 | 0.7353 |
| F1 | 0.7623 | 0.0411 | 0.7143 | 0.8197 |
| Brier | 0.0120 | 0.0014 | 0.0101 | 0.0132 |

## Interpretation

The ranking and classification metrics move across splits, which is expected with a relatively small positive class. The point of this audit is not to manufacture a single more impressive score; it is to show that performance is sensitive to which observations land in the test partition. The seed-42 split remains the project's primary held-out evaluation for consistency with the model-selection record.
