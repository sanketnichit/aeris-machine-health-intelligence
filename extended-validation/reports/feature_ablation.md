# AERIS Feature Ablation Study

This experiment isolates the contribution of the two deterministic engineering-derived features used by AERIS v1. The model family, hyperparameters, random seed, train/test partition, cross-validation scheme and 0.50 calibrated decision threshold are held fixed.

## Features

- **Raw operating features:** product type, air temperature, process temperature, rotational speed, torque and tool wear.
- **Engineered set:** the same six raw features plus temperature delta and mechanical power.

Neither engineered feature uses machine-failure or failure-mode labels.

## Results

| Feature set | CV PR-AUC | Test PR-AUC | Test precision | Test recall | Test F1 | Test Brier |
|---|---:|---:|---:|---:|---:|---:|
| Raw operating features | 0.8026 ± 0.0376 | 0.8490 | 0.9259 | 0.7353 | 0.8197 | 0.0108 |
| Raw + engineered features | 0.8713 ± 0.0301 | 0.8986 | 0.9649 | 0.8088 | 0.8800 | 0.0075 |

## Change from adding the engineered features

- CV PR-AUC change: **+0.0687**
- Test PR-AUC change: **+0.0496**
- Test recall change: **+0.0735**
- Test F1 change: **+0.0603**
- Brier-score change: **-0.0033** (negative is better)

## Interpretation

The engineered features improve both ranking and thresholded detection on the AI4I benchmark under the fixed evaluation design. This supports keeping them in v1. It does not establish physical causality, and the effect should be re-tested on independent industrial data because AI4I is synthetic.
