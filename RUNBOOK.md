# AERIS Runbook

## Environment

Recommended: Python 3.12.x for the pinned validation environment.

Windows PowerShell:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

The direct dependencies are pinned to the versions used by the CI validation environment.

## Dataset

Download the AI4I 2020 CSV from the canonical UCI source and place it at:

    data/ai4i2020.csv

The benchmark CSV is intentionally not committed to the repository.

## Validate and reproduce the core system

From the repository root:

    python src/validate_data.py
    python src/eda.py
    python src/train_baseline.py
    python src/risk_model.py
    python src/explain_model.py

The v1 risk model uses the shared feature contract in `src/features.py` and the canonical model builders in `src/models.py`. The Streamlit console trains through `src/console_models.py`, so the UI reuses the same model architecture rather than maintaining a second risk-model implementation.

## Extended validation

Additional studies live under `extended-validation/` so the core implementation remains easy to inspect:

    python extended-validation/src/model_comparison.py
    python extended-validation/src/feature_ablation.py
    python extended-validation/src/evaluate_thresholds.py
    python extended-validation/src/uncertainty_audit.py
    python extended-validation/src/split_sensitivity.py
    python extended-validation/src/error_analysis.py
    python extended-validation/src/feature_stability.py
    python extended-validation/src/calibration_audit.py
    python extended-validation/src/failure_mode_attribution.py

These studies validate robustness, threshold behaviour, feature contribution and secondary attribution. They are not hidden tuning loops and do not replace the primary seed-42 evaluation.

## Test

    pytest -q

CI also compiles both the core `src/` package and the extended-validation Python scripts.

## Launch the console

    streamlit run app.py

## Reporting rule

Never report a model metric without stating the dataset, evaluation design, threshold when relevant, and major limitations. The objective is a reproducible engineering prototype, not the highest-looking metric.
