# Subgroup Audit

AERIS was checked separately across the three AI4I product types.

| Type | Test rows | Test failures | PR-AUC | Precision @ 0.50 | Recall @ 0.50 | F1 |
|---|---:|---:|---:|---:|---:|---:|
| H | 214 | 5 | 0.858 | 1.000 | 0.400 | 0.571 |
| L | 1170 | 38 | 0.840 | 0.903 | 0.737 | 0.812 |
| M | 616 | 25 | 0.871 | 0.952 | 0.800 | 0.870 |

## Interpretation

Overall ranking performance is reasonably consistent across product types, but the H subgroup contains only **five positive test examples**. Its recall estimate is therefore too statistically fragile to treat as a meaningful production comparison.

This audit is retained to demonstrate that aggregate metrics are not sufficient by themselves.
