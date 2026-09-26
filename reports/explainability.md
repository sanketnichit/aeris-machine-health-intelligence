# AERIS Explainability

## Global feature importance: permutation importance

| Feature | Mean AP decrease | Std |
|---|---:|---:|
| Torque [Nm] | 0.5534 | 0.0238 |
| Air temperature [K] | 0.5480 | 0.0487 |
| Rotational speed [rpm] | 0.4172 | 0.0262 |
| Tool wear [min] | 0.3246 | 0.0336 |
| Process temperature [K] | 0.3000 | 0.0293 |
| Type | 0.0290 | 0.0103 |

Permutation importance is computed on the held-out test set using average precision. A larger decrease means the model loses more ranking performance when that feature is permuted.

## SHAP global importance

Computed on an unseen 200-row test subset from the fitted tree model.

| Encoded feature | Mean absolute SHAP |
|---|---:|
| Torque [Nm] | 0.9194 |
| Tool wear [min] | 0.7749 |
| Air temperature [K] | 0.5840 |
| Rotational speed [rpm] | 0.5284 |
| Process temperature [K] | 0.4610 |
| Type_H | 0.1002 |
| Type_M | 0.0647 |
| Type_L | 0.0598 |

## Interpretation

Both explanation methods identify **torque, temperature variables, rotational speed and tool wear** as the major model signals, while machine type contributes much less.

SHAP values are model explanations, not proof of physical causality. Correlated variables can share or redistribute attribution.
