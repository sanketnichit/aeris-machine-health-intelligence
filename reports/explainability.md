# AERIS Explainability

## Global feature importance: permutation importance

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

Permutation importance is computed on the held-out test set using average precision. A larger decrease means the model loses more ranking performance when that feature is permuted. Negative values mean the measured permutation change was slightly beneficial to AP in this particular held-out sample; they should not be interpreted as evidence that the feature is harmful or causally irrelevant.

## SHAP global importance

Computed on an unseen 200-row test subset from the fitted underlying HistGradientBoosting model.

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

## Interpretation

Permutation importance and SHAP answer different questions. Permutation importance measures the drop in held-out average-precision performance when a feature is shuffled; SHAP describes how individual transformed features contribute to the underlying tree model's output.

These are model attributions, not physical root-cause measurements. Correlated raw and engineered variables can share or redistribute attribution, and the very small negative permutation changes should be treated as sampling variation rather than substantive direction.
