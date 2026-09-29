# AERIS: Machine Health Intelligence

[![CI](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/workflows/ci.yml)

AERIS is a predictive-maintenance project built with the AI4I 2020 dataset. It trains a model to detect machine failures, estimate risk, and show which inputs influenced a prediction.

**Live demo:** https://aeris-machine-health-intelligence.streamlit.app/

## What it does

- Checks and prepares the AI4I dataset.
- Trains a HistGradientBoosting classifier and calibrates its output with sigmoid calibration.
- Adds two features from the observed inputs: temperature difference and estimated mechanical power.
- Shows feature attribution with permutation importance and SHAP.
- Provides a Streamlit console for trying machine operating values.

Failure-mode scores for HDF, PWF, and OSF are included as a secondary study. They are separate scores because the dataset allows more than one failure flag on a row.

## Data and results

The project uses the [AI4I 2020 Predictive Maintenance Dataset](https://doi.org/10.24432/C5HS5C) from the UCI Machine Learning Repository. It has 10,000 rows; the machine-failure label is positive for 3.39% of them. The data is synthetic, so these results describe performance on this benchmark and should not be read as expected performance on factory equipment.

On the stratified 80/20 split with random seed 42, the calibrated model reported:

| Metric | Result |
|---|---:|
| PR-AUC (average precision) | 0.899 |
| Precision at 0.50 | 0.965 |
| Recall at 0.50 | 0.809 |
| F1 at 0.50 | 0.880 |
| Brier score | 0.0075 |

The 95% stratified-bootstrap interval for PR-AUC was 0.835–0.953. Across five fixed-model stratified splits, mean PR-AUC was 0.881 ± 0.025. More detail is in [reports/risk_model.md](reports/risk_model.md) and [docs/reproducibility_audit.md](docs/reproducibility_audit.md).

## Evaluation notes

Average precision is the main metric because failures are uncommon. Model selection uses cross-validation on the training portion; the test portion is held out for the reported result.

The model uses six observed inputs and two deterministic derived features:

- `temp_delta_k`: process temperature minus air temperature
- `mechanical_power_kw`: rotational speed × torque / 9549.2966

The failure label and failure-mode flags are not used as model inputs. The derived features improved results in the benchmark evaluation, but that does not establish physical causality. See [docs/model_card.md](docs/model_card.md) for intended use and limitations.

## Run it

Use Python 3.12 for the pinned environment. From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_dataset.py
```

The dataset is saved to `data/ai4i2020.csv`. Then run the core scripts:

```bash
python src/validate_data.py
python src/eda.py
python src/train_baseline.py
python src/risk_model.py
python src/explain_model.py
```

To launch the console:

```bash
streamlit run app.py
```

The optional studies under `extended-validation/` cover feature ablation, threshold selection, uncertainty, split sensitivity, error analysis, calibration, and failure-mode attribution. Their commands and descriptions are in [extended-validation/README.md](extended-validation/README.md).

## Repository layout

- `src/`: data loading, features, models, evaluation, and console model setup
- `reports/`: generated benchmark and explainability results
- `docs/`: model card, engineering decisions, demo notes, and reproduction details
- `extended-validation/`: secondary evaluation studies
- `tests/`: project tests

For setup details, see [RUNBOOK.md](RUNBOOK.md). The project and dataset licenses are documented in [LICENSE](LICENSE) and [DATA_LICENSE.md](DATA_LICENSE.md).
