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

## Validate and reproduce

    python src/validate_data.py
    python src/eda.py
    python src/train_baseline.py
    python src/model_comparison.py
    python src/risk_model.py
    python src/failure_mode_attribution.py
    python src/explain_model.py
    python src/evaluate_thresholds.py
    python src/uncertainty_audit.py
    python src/split_sensitivity.py
    python src/error_analysis.py
    python src/feature_stability.py
    python src/calibration_audit.py
    python src/feature_ablation.py

The current v1 model uses the shared feature contract in `src/features.py` and the raw-vs-engineered ablation in `src/feature_ablation.py` to justify the added signals. The Streamlit console trains through `src/console_models.py` so the UI reuses the same canonical model architecture rather than duplicating model definitions. It adds temperature delta and mechanical power deterministically from raw operating inputs.

## Test

    pytest -q

The repository CI also runs Python compilation checks for `src/` and `app.py`.

## Launch the console

    streamlit run app.py

## Reporting rule

Never report a model metric without stating the dataset, evaluation design, threshold when relevant, and major limitations. The objective is a reproducible and defensible engineering prototype, not the highest-looking accuracy number.
