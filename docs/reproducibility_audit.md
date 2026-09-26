# AERIS Reproducibility Audit

## Purpose

This audit records how the AERIS v1 headline metrics are reproduced from the AI4I 2020 CSV using the documented feature contract, train/test split, model architecture and evaluation procedures.

The benchmark CSV remains intentionally outside the repository. Reproduction requires placing the source file at `data/ai4i2020.csv`.

## Current software baseline

The repository pins the direct Python dependencies used by the GitHub Actions validation environment on 2026-09-26:

- Python: 3.12.14
- pandas: 3.0.6
- numpy: 2.5.3
- matplotlib: 3.11.2
- scikit-learn: 1.9.1
- streamlit: 1.64.0
- shap: 0.52.0
- pytest: 9.1.1

GitHub Actions compiles the core and extended Python sources and runs the full repository test suite on every push.

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

## Core evaluation boundary

The core result uses a single fixed stratified 80/20 seed-42 holdout. Model selection uses only 5-fold stratified cross-validation on the training partition. The held-out test partition is not used to tune the model.

The primary project claims stop at fault detection, calibrated risk scoring, and engineering visualization. Additional studies are kept in [extended-validation](../extended-validation/README.md) and do not change the primary evaluation.

## Extended validation

The extended-validation area preserves the project's secondary evidence in a clearly separated place. It includes model-family comparison, feature ablation, threshold analysis, bootstrap uncertainty, split sensitivity, error analysis, feature-stability, subgroup calibration and failure-mode feasibility.

These studies are useful for understanding robustness and design trade-offs, but they are not part of the minimum v1 inference path.

## Reproduction boundary

This audit establishes numerical reproduction of the documented AI4I benchmark experiments. It does **not** establish real-world industrial performance.

A production-quality validation would still need an independent industrial dataset, prospective validation, population-specific calibration, drift monitoring and maintenance-cost-based threshold selection.
