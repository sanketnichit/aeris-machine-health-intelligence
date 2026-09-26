# Data Validation Report

- Rows: 10000, Columns: 14

## Missing values
- No missing values in any column.

## Duplicates
- Fully duplicated rows: 0
- Duplicate UDI values: 0
- Duplicate Product ID values: 0

## Range sanity checks
- air_temp_k negative or zero: 0
- process_temp_k negative or zero: 0
- rot_speed_rpm negative: 0
- torque_nm negative: 0
- tool_wear_min negative: 0
- process_temp < air_temp (physically odd): 0

## Categorical check
- Unique `type` values: ['H', 'L', 'M']

## Target consistency (machine_failure vs TWF/HDF/PWF/OSF/RNF)
- Rows where machine_failure disagrees with (any failure-mode flag == 1): 27
- Example mismatched UDIs: [1222, 1303, 1438, 1749, 2073, 2560, 2750, 3066, 3453, 4045]

## Class balance
- No failure (0): 9661 (96.61%)
- Failure (1): 339 (3.39%)

## Failure-mode counts (among machine_failure == 1)
- TWF: 46
- HDF: 115
- PWF: 95
- OSF: 98
- RNF: 1
- Rows with more than one failure-mode flag set: 24
