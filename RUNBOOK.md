# AERIS Runbook

## Environment

Recommended: Python 3.12+.

Windows PowerShell:

    py -m venv .venv
    .\\.venv\\Scripts\\Activate.ps1
    pip install -r requirements.txt

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

## Test

    pytest -q

## Launch the console

    streamlit run app.py

## Reporting rule

Never report a model metric without stating the dataset, evaluation design, threshold when relevant, and major limitations. The objective is a reproducible and defensible engineering prototype, not the highest-looking accuracy number.
