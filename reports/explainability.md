# AERIS Explainability

## Permutation importance

| Feature | Mean AP decrease |
|---|---:|
| Rotational speed [rpm] | 0.5086 |
| Temperature delta [K] | 0.4181 |
| Tool wear [min] | 0.2860 |
| Mechanical power [kW] | 0.1767 |
| Torque [Nm] | 0.0606 |
| Type | 0.0211 |
| Process temperature [K] | -0.0070 |
| Air temperature [K] | -0.0076 |

Permutation importance was measured on the test set using average precision. A larger drop means the model depended more on that feature for ranking the test examples. The small negative values are just what happened on this split; they should not be read as the feature being harmful.

## SHAP

These values are calculated on a 200-row test subset using the HistGradientBoosting model before probability calibration.

| Encoded feature | Mean absolute SHAP |
|---|---:|
| Tool wear [min] | 0.7829 |
| Rotational speed [rpm] | 0.6020 |
| Mechanical power [kW] | 0.4781 |
| Torque [Nm] | 0.4772 |
| Temperature delta [K] | 0.4336 |
| Process temperature [K] | 0.2948 |
| Air temperature [K] | 0.2396 |
| Type_M | 0.0968 |
| Type_H | 0.0603 |
| Type_L | 0.0603 |

## What this means

Permutation importance tells me how much the model's test-set ranking changes when a feature is shuffled. SHAP shows how the inputs moved an individual prediction in the tree model.

Neither one tells me the physical root cause of a machine problem. Also, correlated raw and derived features can share the importance between them.
