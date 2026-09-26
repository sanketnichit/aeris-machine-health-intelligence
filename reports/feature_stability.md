# AERIS Feature-Stability Audit

This audit measures permutation importance across five independent stratified 80/20 splits using the fixed HistGradientBoosting architecture. Importance is measured as the decrease in average precision on each held-out split. The audit is descriptive and does not tune model hyperparameters or thresholds.

## Stability summary

| Feature | Mean AP drop | Across-split SD | Mean rank | Best rank | Worst rank | Top-1 splits | Top-2 splits |
|---|---:|---:|---:|---:|---:|---:|---:|
| rot_speed_rpm | 0.4935 | 0.0461 | 1.00 | 1 | 1 | 5/5 | 5/5 |
| temp_delta_k | 0.4051 | 0.0471 | 2.00 | 2 | 2 | 0/5 | 5/5 |
| tool_wear_min | 0.2869 | 0.0220 | 3.00 | 3 | 3 | 0/5 | 0/5 |
| mechanical_power_kw | 0.2143 | 0.0327 | 4.00 | 4 | 4 | 0/5 | 0/5 |
| torque_nm | 0.0722 | 0.0062 | 5.00 | 5 | 5 | 0/5 | 0/5 |
| type | 0.0363 | 0.0088 | 6.00 | 6 | 6 | 0/5 | 0/5 |
| process_temp_k | -0.0037 | 0.0028 | 7.20 | 7 | 8 | 0/5 | 0/5 |
| air_temp_k | -0.0070 | 0.0023 | 7.80 | 7 | 8 | 0/5 | 0/5 |

## Interpretation

Permutation importance is not a causal ranking, and correlated variables can share attribution. In this benchmark the engineered temperature-delta and mechanical-power features absorb information that overlaps with their component inputs, so the raw component features can show little additional permutation value once the derived signals are present.

The stable part of the result is the broad ordering: rotational speed is ranked first in all five splits and temperature delta is ranked second in all five. This is evidence of model-behaviour stability on AI4I, not proof of physical causality.
