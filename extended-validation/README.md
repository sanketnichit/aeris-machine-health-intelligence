# AERIS Extended Validation

This directory contains **additional validation and study code beyond the minimum AERIS v1 pipeline**.

The core project deliberately stays focused on:

1. fault detection
2. calibrated failure-risk scoring with model explanation
3. the Machine Health Console

The studies below support those capabilities without making the core implementation harder to inspect.

## Studies

| Study | Purpose |
|---|---|
| `model_comparison.py` | Compare model families using training-only cross-validation before final held-out evaluation. |
| `feature_ablation.py` | Measure the incremental value of the two deterministic engineered features. |
| `evaluate_thresholds.py` | Evaluate OOF-selected thresholds and produce calibration / PR plots. |
| `uncertainty_audit.py` | Quantify uncertainty around the seed-42 held-out metrics with stratified bootstrap intervals. |
| `split_sensitivity.py` | Measure how the fixed model changes across alternate stratified splits. |
| `error_analysis.py` | Profile held-out false positives and false negatives descriptively. |
| `feature_stability.py` | Check whether permutation-importance rankings persist across splits. |
| `calibration_audit.py` | Inspect subgroup and operating-regime calibration. |
| `failure_mode_attribution.py` | Test HDF/PWF/OSF/TWF/RNF feasibility as a secondary multi-label study. |

## Running the studies

Run from the repository root after placing the AI4I CSV at `data/ai4i2020.csv`:

    python extended-validation/src/model_comparison.py
    python extended-validation/src/feature_ablation.py
    python extended-validation/src/evaluate_thresholds.py
    python extended-validation/src/uncertainty_audit.py
    python extended-validation/src/split_sensitivity.py
    python extended-validation/src/error_analysis.py
    python extended-validation/src/feature_stability.py
    python extended-validation/src/calibration_audit.py
    python extended-validation/src/failure_mode_attribution.py

Generated reports are written to `extended-validation/reports/`.

The scripts add the project `src/` directory to their import path when executed directly. This keeps the core package as the single source of truth for data loading, feature engineering and model construction.
