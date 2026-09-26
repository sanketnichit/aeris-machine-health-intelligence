# AERIS Reproducibility Audit

## Purpose

This audit checks that the headline AERIS v1 metrics can be regenerated from the AI4I 2020 CSV using the documented feature contract, train/test split, model architecture and evaluation procedures.

The benchmark CSV remains intentionally outside the repository. Reproduction therefore requires placing the source file at `data/ai4i2020.csv`.

## Current software baseline

The repository now pins direct Python dependencies to the versions used by the GitHub Actions validation environment on 2026-09-26:

- Python: 3.12.14
- pandas: 3.0.6
- numpy: 2.5.3
- matplotlib: 3.11.2
- scikit-learn: 1.9.1
- streamlit: 1.64.0
- shap: 0.52.0
- pytest: 9.1.1

GitHub Actions also performs source compilation and the full repository test suite on every push.

## Dataset validation

The AI4I CSV contains:

- 10,000 rows
- 14 source columns
- 339 machine-failure positives (3.39%)
- no missing values
- no duplicate rows
- no duplicate UDI values
- no duplicate Product ID values
- 27 rows where the binary failure label disagrees with whether any failure-mode flag is set

The source failure-mode flags can overlap, so AERIS treats them as multi-label targets for the secondary attribution study.

## Primary model reproduction

Using the documented seed-42 80/20 stratified split, the six observed inputs plus the two deterministic engineered features, HGB architecture and sigmoid calibration reproduce:

| Metric | Reproduced value |
|---|---:|
| PR-AUC | 0.8986 |
| Precision @ 0.50 | 0.9649 |
| Recall @ 0.50 | 0.8088 |
| F1 @ 0.50 | 0.8800 |
| Brier score | 0.00752 |

At the displayed precision used in project documentation, these are **0.899 / 0.965 / 0.809 / 0.880 / 0.0075**.

The resulting confusion matrix is:

| | Predicted 0 | Predicted 1 |
|---|---:|---:|
| Actual 0 | 1930 | 2 |
| Actual 1 | 13 | 55 |

## Feature ablation reproduction

Keeping the model family, hyperparameters, split and threshold fixed:

| Feature set | CV PR-AUC | Test PR-AUC | Test Recall | Test F1 | Test Brier |
|---|---:|---:|---:|---:|---:|
| Raw operating features | 0.8026 ± 0.0376 | 0.8490 | 0.7353 | 0.8197 | 0.0108 |
| Raw + engineered features | 0.8713 ± 0.0301 | 0.8986 | 0.8088 | 0.8800 | 0.0075 |

The engineered features are `temp_delta_k` and `mechanical_power_kw`. They use only observed operating inputs and no target-side information.

## Threshold reproduction

OOF-selected raw-model thresholds evaluated once on the untouched test set reproduce:

| Objective | OOF threshold | Test precision | Test recall | Test F1 |
|---|---:|---:|---:|---:|
| F0.5 | 0.6255 | 0.9474 | 0.7941 | 0.8640 |
| F1 | 0.2648 | 0.8730 | 0.8088 | 0.8397 |
| F2 | 0.1055 | 0.8028 | 0.8382 | 0.8201 |

The console keeps 0.50 on the calibrated risk score as the simple demonstration threshold. That is a UI policy, not a universally optimal operational threshold.

## Calibration reproduction

For the same seed-42 held-out evaluation:

- Sigmoid Brier: 0.007521
- Isotonic Brier: 0.007416

Sigmoid remains the v1 mapping because it is simpler and less flexible for this small positive class while preserving essentially the same ranking behaviour.

## Secondary robustness reproduction

Across fixed calibrated-model splits using seeds 42, 7, 21, 84 and 123:

- mean PR-AUC: 0.8813 ± 0.0254
- mean precision: 0.9607 ± 0.0222
- mean recall: 0.7412 ± 0.0768
- mean F1: 0.8355 ± 0.0575
- mean Brier: 0.0087 ± 0.0015

The seed-42 result remains the primary held-out evaluation.

The 3,000-resample stratified bootstrap around the seed-42 test set reproduces:

- PR-AUC: [0.8350, 0.9533]
- Precision: [0.9153, 1.0000]
- Recall: [0.7206, 0.8971]
- F1: [0.8167, 0.9375]
- Brier: [0.0050, 0.0102]

## Failure-mode reproduction

With engineered features and the class-weighted HGB attribution model, 5-fold CV gives:

| Mode | Mean PR-AUC |
|---|---:|
| HDF | 1.000 |
| PWF | 0.917 |
| OSF | 0.944 |
| TWF | 0.129 |
| RNF | 0.010 |

AERIS exposes HDF/PWF/OSF as the v1 secondary attribution layer and keeps TWF/RNF deferred. These are benchmark attribution signals, not physical diagnoses.

## Explainability reproduction

Permutation importance on the held-out test set reproduces the current broad ranking:

1. Rotational speed
2. Temperature delta
3. Tool wear
4. Mechanical power
5. Torque
6. Type
7. Process temperature
8. Air temperature

SHAP on the underlying HGB model reproduces tool wear, rotational speed, mechanical power, torque and temperature delta as the strongest individual model attributions.

These values describe model behaviour and do not establish physical causality.

## CI verification

The current repository source has been validated by GitHub Actions on Python 3.12.14 with the pinned dependency set. The latest validation run completed successfully with all repository tests passing.

## Reproduction boundary

This audit establishes numerical reproduction of the documented benchmark experiments. It does **not** establish real-world industrial performance.

A production-quality validation would still need an independent industrial dataset, prospective validation, population-specific calibration, drift monitoring and maintenance-cost-based threshold selection.
