# Feature Ablation

I compared the model with and without the two derived features. The model settings, seed, split and threshold were kept the same.

## Features

- **Raw operating features:** product type, air temperature, process temperature, rotational speed, torque and tool wear.
- **Engineered set:** the same six raw features plus temperature delta and mechanical power.

Neither engineered feature uses machine-failure or failure-mode labels.

## Results

| Feature set | CV PR-AUC | Test PR-AUC | Test precision | Test recall | Test F1 | Test Brier |
|---|---:|---:|---:|---:|---:|---:|
| Raw operating features | 0.8026 ± 0.0376 | 0.8490 | 0.9259 | 0.7353 | 0.8197 | 0.0108 |
| Raw + engineered features | 0.8713 ± 0.0301 | 0.8986 | 0.9649 | 0.8088 | 0.8800 | 0.0075 |

## Change after adding the derived features

- CV PR-AUC change: **+0.0687**
- Test PR-AUC change: **+0.0496**
- Test recall change: **+0.0735**
- Test F1 change: **+0.0603**
- Brier-score change: **-0.0033** (negative is better)

## Interpretation

The derived features improve both ranking and thresholded detection on this AI4I split, so I kept them in the current version. It does not establish physical causality, and the effect should be re-tested on independent industrial data because AI4I is synthetic.
