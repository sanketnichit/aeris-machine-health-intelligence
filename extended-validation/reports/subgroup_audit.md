# Subgroup Audit

AERIS was checked separately across the three AI4I product types using the current calibrated v1 model.

| Type | Test rows | Test failures | PR-AUC | Precision @ 0.50 | Recall @ 0.50 | F1 |
|---|---:|---:|---:|---:|---:|---:|
| H | 214 | 5 | 0.967 | 1.000 | 0.800 | 0.889 |
| L | 1170 | 38 | 0.889 | 0.938 | 0.789 | 0.857 |
| M | 616 | 25 | 0.898 | 1.000 | 0.840 | 0.913 |

## Interpretation

The product-type results are directionally similar, but the H subgroup contains only **five positive test examples**. Its recall estimate is therefore statistically fragile and should not be treated as a meaningful production comparison.

This audit is retained to demonstrate that aggregate metrics are not sufficient by themselves.
