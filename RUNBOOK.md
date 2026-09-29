# AERIS Runbook

This file is just the quick setup/reference I use for the project.

## 1. Python environment

The validation environment uses Python 3.12.

On Windows PowerShell:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## 2. Dataset

The AI4I 2020 CSV should be here:

    data/ai4i2020.csv

The dataset is not committed to the repo. The easiest setup is:

    python scripts/download_dataset.py

The script checks the CSV header before saving it.

## 3. Main pipeline

Run these from the repository root:

    python src/validate_data.py
    python src/eda.py
    python src/train_baseline.py
    python src/risk_model.py
    python src/explain_model.py

The main model code lives in src/. The Streamlit app uses the same feature and model definitions rather than a separate version of the pipeline.

## 4. Extra experiments

The extended-validation/ folder contains the experiments I used to check the main result:

    python extended-validation/src/model_comparison.py
    python extended-validation/src/feature_ablation.py
    python extended-validation/src/evaluate_thresholds.py
    python extended-validation/src/uncertainty_audit.py
    python extended-validation/src/split_sensitivity.py
    python extended-validation/src/error_analysis.py
    python extended-validation/src/feature_stability.py
    python extended-validation/src/calibration_audit.py
    python extended-validation/src/failure_mode_attribution.py

These are separate from the main inference path so that the core project stays easier to follow.

## 5. Tests

    pytest -q

GitHub Actions also checks that the Python files compile and that the tests pass.

## 6. Streamlit app

    streamlit run app.py

The app trains the console model bundle and lets you try individual machine observations.

## Reporting

When I record a model number, I try to include the dataset, split, threshold and the main limitation with it. The AI4I dataset is synthetic, so benchmark results should not be presented as real factory performance.
