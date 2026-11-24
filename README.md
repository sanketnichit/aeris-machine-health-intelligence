# AERIS — Machine Health Intelligence

AERIS began as a BTech project on the UCI AI4I 2020 dataset and has expanded into a reproducible machine-health research prototype. The project uses AI-assisted development; its evidence, code, limitations and experimental decisions are documented for review.

**Live demo:** https://aeris-machine-health-intelligence.streamlit.app/ (deployment availability is not guaranteed by CI).

## Research capabilities

| Task | Verified evidence | Limits |
|---|---|---|
| AI4I failure classification | [Rule and stress audits](research/AI4I_FINDINGS.md) | Synthetic snapshot; generator rules outperform ML at the fixed threshold |
| NASA FD001 forecasting | [Frozen official endpoint results](research/FD001_OFFICIAL_FINDINGS.md) | Simulated engines; primary MAE 17.35 cycles, adaptive comparator 15.33 |
| Uncertainty and risk | [Development findings](research/CMAPSS_RISK_FINDINGS.md) | Intervals remain wide; no safety guarantee |
| Maintenance decisions | [Replay summary](research/evidence/maintenance_summary.json) | Hypothetical costs; not measured savings |
| Temporal monitoring | [Verified replay traces](research/evidence/telemetry.json) | Three held-out development engines, 655 pre-failure observations |
| Physical bearings | [XJTU-SY findings](research/XJTU_FINDINGS.md) | Physical laboratory data; 32.7% lower MAE under held-out conditions, 5.1% higher MAE under held-out bearings |

The research console provides offline evidence tables, cost comparisons, official benchmark metrics and cycle-by-cycle telemetry replay. The original AI4I interactive classifier remains a separate workspace. See the [research index](research/README.md) for reproducibility and limitations. The official FD001 test set has been observed; future model changes require new independent evaluation.

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

The original classification task uses the [AI4I 2020 Predictive Maintenance Dataset](https://doi.org/10.24432/C5HS5C) from the UCI Machine Learning Repository.

The dataset has 10,000 rows and 3.39% positive machine-failure labels. It is a synthetic benchmark, so the numbers below should not be treated as expected performance on real factory machines.

The CSV is not stored in the repo. A fresh clone can download it with:

```powershell
python scripts/download_dataset.py
```

It will be saved as `data/ai4i2020.csv`.

## Original AI4I benchmark result

For the current seed-42 stratified 80/20 evaluation, the calibrated model reports:

| Metric | Result |
|---|---:|
| PR-AUC | 0.899 |
| Precision at 0.50 | 0.965 |
| Recall at 0.50 | 0.809 |
| F1 at 0.50 | 0.880 |
| Brier score | 0.0075 |

The test set only has about 68 failures in it, so a single point estimate isn't the whole story. The 95% bootstrap interval on each metric:

| Metric | 95% interval |
|---|---:|
| PR-AUC | [0.835, 0.953] |
| Precision | [0.915, 1.000] |
| Recall | [0.721, 0.897] |
| F1 | [0.817, 0.938] |
| Brier | [0.0050, 0.0102] |

Across five different stratified splits, mean PR-AUC is 0.881 ± 0.025 and mean F1 is 0.836 ± 0.057 - so the headline numbers above hold up and aren't just a lucky split.

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

The default Research intelligence workspace reads committed evidence without downloading a dataset or training a model. Select AI4I failure prediction for the original model demo.

```bash
streamlit run app.py
```

### Run tests

```bash
pytest -q
```

The extra experiments are in [extended-validation/README.md](extended-validation/README.md).

To reproduce the model-comparison report from the repository root (after downloading the dataset):

```bash
python extended-validation/src/model_comparison.py
```

## Repository layout

```text
aeris-machine-health-intelligence/
├── app.py
├── src/                  # main data, feature and model code
├── scripts/              # dataset setup
├── tests/                # project tests
├── reports/              # generated model reports
├── docs/                 # notes and validation details
├── research/             # protocols, new experiments and verified evidence
├── extended-validation/  # original extra experiments
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
