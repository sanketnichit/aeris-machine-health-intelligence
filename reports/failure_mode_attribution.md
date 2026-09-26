# Failure-mode Attribution

AERIS v1 treats failure modes as a **multi-label attribution** problem rather than forcing every failed row into exactly one class.

The production-facing attribution layer currently covers HDF, PWF and OSF. TWF and RNF are deferred because their positive counts/label behaviour are not strong enough for a defensible model.

## Cross-validation evidence

| Mode | Positives | 5-fold mean PR-AUC | 5-fold mean Precision | 5-fold mean Recall | 5-fold mean F1 |
|---|---:|---:|---:|---:|---:|
| HDF | 115 | 0.986 ± 0.016 | 0.928 | 0.965 | 0.945 |
| PWF | 95 | 0.791 ± 0.037 | 0.648 | 0.832 | 0.728 |
| OSF | 98 | 0.942 ± 0.030 | 0.820 | 0.948 | 0.878 |
| TWF | 46 | 0.119 ± 0.069 | 0.103 | 0.111 | 0.106 |
| RNF | 19 | 0.010 ± 0.010 | 0.000 | 0.000 | 0.000 |

## Interpretation

HDF, PWF and OSF show enough signal for a useful attribution layer under this benchmark. TWF and RNF should not be presented as reliable failure-mode predictions in v1. AERIS therefore prefers honest partial coverage over a five-class model that looks complete but is statistically weak.

## Multi-label caveat

AI4I allows more than one failure-mode flag to be present for a failed row. The UI should therefore show mode scores side-by-side rather than claim that exactly one physical root cause has been proven.
