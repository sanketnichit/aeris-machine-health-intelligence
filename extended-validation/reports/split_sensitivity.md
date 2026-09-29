# Split Sensitivity

I ran the same calibrated HGB setup on five different stratified 80/20 splits. The model settings and 0.50 threshold stayed fixed.

## Results by split

| Seed | Test failures | PR-AUC | Precision | Recall | F1 | Brier |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 68 | 0.899 | 0.965 | 0.809 | 0.880 | 0.0075 |
| 7 | 68 | 0.849 | 0.933 | 0.618 | 0.743 | 0.0109 |
| 21 | 68 | 0.871 | 0.981 | 0.765 | 0.860 | 0.0083 |
| 84 | 68 | 0.914 | 0.982 | 0.794 | 0.878 | 0.0071 |
| 123 | 68 | 0.873 | 0.942 | 0.721 | 0.817 | 0.0094 |

## Fixed-model summary

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| PR-AUC | 0.8813 | 0.0254 | 0.8495 | 0.9144 |
| Precision | 0.9607 | 0.0222 | 0.9333 | 0.9818 |
| Recall | 0.7412 | 0.0768 | 0.6176 | 0.8088 |
| F1 | 0.8355 | 0.0575 | 0.7434 | 0.8800 |
| Brier | 0.0087 | 0.0015 | 0.0071 | 0.0109 |

## Interpretation

The scores move between splits, which is not surprising because there are only 68 positive examples in each test set. The useful part of this check is seeing how much the result depends on which rows end up in the test set. I still use seed 42 as the main result so the project stays consistent.
