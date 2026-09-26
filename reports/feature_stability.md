# AERIS Feature-Stability Audit

This audit measures permutation importance across five independent stratified 80/20 splits using the fixed HistGradientBoosting architecture. Importance is measured as the decrease in average precision on each held-out split. The audit is descriptive and does not tune model hyperparameters or thresholds.

## Stability summary

| Feature | Mean AP drop | Across-split SD | Mean rank | Best rank | Worst rank | Top-1 splits | Top-2 splits |
|---|---:|---:|---:|---:|---:|---:|---:|
| torque_nm | 0.5512 | 0.0674 | 1.60 | 1 | 3 | 3/5 | 4/5 |
| air_temp_k | 0.5115 | 0.0535 | 1.60 | 1 | 2 | 2/5 | 5/5 |
| rot_speed_rpm | 0.3979 | 0.0642 | 3.00 | 2 | 4 | 0/5 | 1/5 |
| tool_wear_min | 0.3117 | 0.0179 | 4.20 | 3 | 5 | 0/5 | 0/5 |
| process_temp_k | 0.2957 | 0.0281 | 4.60 | 4 | 5 | 0/5 | 0/5 |
| type | 0.0402 | 0.0084 | 6.00 | 6 | 6 | 0/5 | 0/5 |

## Per-split importance

| Seed | Feature | AP drop | Rank |
|---:|---|---:|---:|
| 7 | air_temp_k | 0.4917 | 1 |
| 7 | torque_nm | 0.4901 | 2 |
| 7 | rot_speed_rpm | 0.3601 | 3 |
| 7 | process_temp_k | 0.3180 | 4 |
| 7 | tool_wear_min | 0.2971 | 5 |
| 7 | type | 0.0404 | 6 |
| 21 | air_temp_k | 0.5647 | 1 |
| 21 | rot_speed_rpm | 0.4926 | 2 |
| 21 | torque_nm | 0.4810 | 3 |
| 21 | tool_wear_min | 0.3147 | 4 |
| 21 | process_temp_k | 0.2892 | 5 |
| 21 | type | 0.0425 | 6 |
| 42 | torque_nm | 0.5713 | 1 |
| 42 | air_temp_k | 0.5342 | 2 |
| 42 | rot_speed_rpm | 0.4078 | 3 |
| 42 | tool_wear_min | 0.3267 | 4 |
| 42 | process_temp_k | 0.3053 | 5 |
| 42 | type | 0.0304 | 6 |
| 84 | torque_nm | 0.6450 | 1 |
| 84 | air_temp_k | 0.5389 | 2 |
| 84 | rot_speed_rpm | 0.4079 | 3 |
| 84 | process_temp_k | 0.3162 | 4 |
| 84 | tool_wear_min | 0.2895 | 5 |
| 84 | type | 0.0349 | 6 |
| 123 | torque_nm | 0.5688 | 1 |
| 123 | air_temp_k | 0.4279 | 2 |
| 123 | tool_wear_min | 0.3304 | 3 |
| 123 | rot_speed_rpm | 0.3213 | 4 |
| 123 | process_temp_k | 0.2499 | 5 |
| 123 | type | 0.0526 | 6 |

## Interpretation

Feature importance is not a causal ranking, and correlated variables can share attribution. The useful question here is whether the broad ordering is stable across plausible held-out partitions. Large movement in rank is evidence that a feature's importance should be treated cautiously rather than presented as universally dominant.
