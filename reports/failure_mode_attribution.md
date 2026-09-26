# Failure-mode Attribution

AERIS v1 treats failure modes as a **multi-label attribution** problem rather than forcing every failed row into exactly one class.

## Cross-validation feasibility check

| Mode | Positives | Mean PR-AUC | Mean Precision | Mean Recall | Mean F1 |
|---|---:|---:|---:|---:|---:|
| HDF | 115 | 1.000 ± 0.000 | 1.000 | 1.000 | 1.000 |
| PWF | 95 | 0.917 ± 0.039 | 0.811 | 0.895 | 0.849 |
| OSF | 98 | 0.944 ± 0.035 | 0.820 | 0.928 | 0.868 |
| TWF | 46 | 0.129 ± 0.081 | 0.186 | 0.156 | 0.159 |
| RNF | 19 | 0.010 ± 0.010 | 0.000 | 0.000 | 0.000 |

## Production-facing v1 decision

Promote **HDF, PWF and OSF** into the v1 attribution panel.

TWF and RNF remain deferred because their cross-validated signal is too weak/unstable for an engineering-facing prediction layer.

## Synthetic-benchmark caveat

The very strong HDF signal should not be interpreted as evidence of physical root-cause understanding. The AI4I benchmark is synthetic and can contain structured relationships between its generated labels and operating variables. AERIS therefore reports these mode scores as benchmark attribution signals, not physical diagnoses.

## Multi-label caveat

A single failed observation can have more than one mode flag. Therefore AERIS reports mode scores side-by-side and does not claim that one model output proves a unique physical root cause.
