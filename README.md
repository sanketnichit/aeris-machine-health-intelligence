# AERIS - Machine Failure Prediction

AERIS is a BTech project I built around the AI4I 2020 Predictive Maintenance Dataset from UCI.

The idea was to make a small but complete machine-failure project instead of only training a model in a notebook. The repo has data checks, a baseline model, a stronger model with a couple of derived features, evaluation scripts, explainability, tests, and a Streamlit app.

**Live demo:** https://aeris-machine-health-intelligence.streamlit.app/

## What is in the project

- Load and validate the AI4I 2020 dataset.
- Train a Random Forest baseline.
- Train a HistGradientBoosting model with calibrated probabilities.
- Add two derived features:
  - temperature difference
  - estimated mechanical power
- Check precision, recall, F1 and PR-AUC instead of relying on accuracy.
- Use permutation importance and SHAP to inspect model predictions.
- Run some extra checks for split sensitivity, calibration, uncertainty and errors.
- Use the trained pipeline in a small Streamlit interface.

The HDF, PWF and OSF failure-mode models are treated as a separate experiment because the failure flags in AI4I can overlap.

## Dataset

The project uses the [AI4I 2020 Predictive Maintenance Dataset](https://doi.org/10.24432/C5HS5C) from the UCI Machine Learning Repository.

The dataset has 10,000 rows and 3.39% positive machine-failure labels. It is a synthetic benchmark, so the numbers below should not be treated as expected performance on real factory machines.

The CSV is not stored in the repo. A fresh clone can download it with:

```powershell
python scripts/download_dataset.py
```

It will be saved as `data/ai4i2020.csv`.

## Main result

For the current seed-42 stratified 80/20 evaluation, the calibrated model reports:

| Metric | Result |
|---|---:|
| PR-AUC | 0.899 |
| Precision at 0.50 | 0.965 |
| Recall at 0.50 | 0.809 |
| F1 at 0.50 | 0.880 |
| Brier score | 0.0075 |

PR-AUC is used as the main metric because failures are rare.

The more detailed numbers, confusion matrix and reproduction notes are in [reports/risk_model.md](reports/risk_model.md) and [docs/reproducibility_audit.md](docs/reproducibility_audit.md).

## Features

The model uses six observed inputs:

- machine type
- air temperature
- process temperature
- rotational speed
- torque
- tool wear

It also uses two simple deterministic features:

`temp_delta_k` = process temperature - air temperature

`mechanical_power_kw` = rotational speed x torque / 9549.2966

The failure label, failure-mode flags, UDI and Product ID are not used as prediction inputs.

## Running the project

Use Python 3.12 with the pinned requirements.

### Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_dataset.py
```

### Run the main scripts

```bash
python src/validate_data.py
python src/eda.py
python src/train_baseline.py
python src/risk_model.py
python src/explain_model.py
```

### Start the Streamlit app

```bash
streamlit run app.py
```

### Run tests

```bash
pytest -q
```

The extra experiments are in [extended-validation/README.md](extended-validation/README.md).

## Repository layout

```text
aeris-machine-health-intelligence/
├── app.py
├── src/                  # main data, feature and model code
├── scripts/              # dataset setup
├── tests/                # project tests
├── reports/              # generated model reports
├── docs/                 # notes and validation details
├── extended-validation/  # extra experiments
└── data/                 # dataset goes here locally
```

## A few limitations

- AI4I is synthetic, not real industrial telemetry.
- The dataset is not a time series from a real machine fleet.
- Good benchmark performance does not prove physical root-cause understanding.
- The current project is a benchmark/college project, not a production maintenance system.
- A real deployment would need external industrial data, drift checks, calibration on the target population and a maintenance-cost-based alert threshold.

More notes are in [docs/model_card.md](docs/model_card.md).

## Project notes

This project has changed quite a bit while I was building it. Some files are intentionally simple and some of the validation scripts are more detailed because I wanted to check whether the results were just coming from one train/test split.

For the reasoning behind the model and feature choices, see [docs/engineering_decisions.md](docs/engineering_decisions.md).
