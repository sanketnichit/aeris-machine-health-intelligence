# AERIS — Machine Health Intelligence

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24533914.svg)](https://doi.org/10.5281/zenodo.24533914) [![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

AERIS began as a BTech project on the UCI AI4I 2020 dataset and has expanded into a reproducible machine-health research prototype. The project uses AI-assisted development; its evidence, code, limitations and experimental decisions are documented for review.

**Live demo:** https://aeris-machine-health-intelligence.streamlit.app/ (deployment availability is not guaranteed by CI).

**Latest archived research release:** [v0.2.0](https://github.com/sanketnichit/aeris-machine-health-intelligence/releases/tag/v0.2.0) · [Zenodo DOI](https://doi.org/10.5281/zenodo.24533914) · [Quickstart](docs/quickstart.md) · [Architecture](docs/architecture.md) · [Changelog](CHANGELOG.md)

**Release closure:** v0.2.0 is published on GitHub and Zenodo. The defined ten-gate research-release scope is complete. See [publication details](docs/publication.md) and [closure checklist](docs/next_research_release_closure.md). The original [v0.1.0 archive](https://doi.org/10.5281/zenodo.24522637) is preserved.

## Cite AERIS

Nichit, S. (2026). *AERIS: Machine Health Intelligence* (Version 0.2.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24533914

[ORCID](https://orcid.org/0009-0000-6993-7561) · [Citation metadata](CITATION.cff) · [All versions DOI](https://doi.org/10.5281/zenodo.24522636)

The DOI identifies the archived software release, not a peer-reviewed article. The main branch includes post-publication metadata that is not part of the archived revision. See [publication documentation](docs/publication.md).

## Local platform deployment

**Development add-on:** [Durable edge telemetry buffer](docs/edge_buffer.md) stages observations locally and replays them after an API outage. This is post-v0.1.0 development, not a validated physical hardware connector. See [vibration acquisition](docs/vibration_acquisition.md) and [capture archive](docs/capture_archive.md). The vibration laboratory uses a synthetic demonstration by default. Only trusted local deployments should set AERIS_CAPTURE_ARCHIVE_PATH to an existing nonconfidential archive; all dashboard viewers can read its contents.

Run the dashboard and persistent local research API together with `docker compose up --build --detach --wait`. See the [API and deployment guide](docs/api.md). Both host ports bind to localhost; this is not a public production service.

## Application workspaces

| Workspace | What it demonstrates |
|---|---|
| Research intelligence | Evidence-linked research pages, benchmark comparisons, replay and technical report |
| AI4I failure prediction | Synthetic classification and model explanations |
| Telemetry fleet | Persistent ingestion, monitoring events, review incidents, freshness and explainable advisory |
| Virtual degradation laboratory | Seeded maintenance counterfactuals and separate measured-signal evidence |
| Vibration laboratory (development) | Synthetic waveform and FFT exploration; opt-in read-only local capture archive |

After starting Compose, run `python scripts/demo_fleet.py` to populate explicitly synthetic assets. The advisory always withholds operational failure forecasts. The optional monitoring profile enables periodic freshness scans. See [virtual laboratory](docs/digital_twin.md), [roadmap](docs/roadmap.md) and [quickstart](docs/quickstart.md).

See the [scientific conclusions](research/SCIENTIFIC_CONCLUSIONS.md) for the final cross-experiment evidence synthesis and the [release acceptance checklist](docs/release_acceptance.md) for the fixed-revision publication gate.

## Research capabilities

| Task | Verified evidence | Limits |
|---|---|---|
| AI4I failure classification | [Rule and stress audits](research/AI4I_FINDINGS.md) | Synthetic snapshot; generator rules outperform ML at the fixed threshold |
| NASA FD001 forecasting | [Frozen official endpoint results](research/FD001_OFFICIAL_FINDINGS.md) | Simulated engines; primary MAE 17.35 cycles, adaptive comparator 15.33 |
| Uncertainty and risk | [Development findings](research/CMAPSS_RISK_FINDINGS.md) | Intervals remain wide; no safety guarantee |
| Maintenance decisions | [Replay summary](research/evidence/maintenance_summary.json) | Hypothetical costs; not measured savings |
| Temporal monitoring | [Verified replay traces](research/evidence/telemetry.json) | Three held-out development engines, 655 pre-failure observations |
| Physical bearings | [XJTU-SY findings](research/XJTU_FINDINGS.md) | Physical laboratory data; 32.7% lower MAE under held-out conditions, 5.1% higher MAE under held-out bearings |
| Sensor-driven adaptation | [XJTU adaptive findings](research/XJTU_ADAPTIVE_FINDINGS.md) | Exploratory gate improvements; reliability policy accepted zero forecasts |
| Independent physical replication | [PRONOSTIA findings](research/PRONOSTIA_FINDINGS.md) | 11 held-out bearings; learned model outperformed fixed vibration gate, so adaptive advantage did not replicate |
| Measured vibration-state transition | [Calibration audit](research/TWIN_CALIBRATION_FINDINGS.md) | 54 endpoints; 1.16% lower MAE than persistence, no established superiority or physical twin calibration |
| Virtual maintenance sensitivity | [Frozen sensitivity study](research/TWIN_SENSITIVITY_FINDINGS.md) | 54 scenarios, 500 trials each; conditional simulated costs only |

The research console provides on-demand workspaces, including offline evidence tables, cost comparisons, official benchmark metrics, simulated engine replay, measured physical vibration-feature replay and a downloadable technical report. The physical replay exposes 254 published points from three previously evaluated PRONOSTIA bearings. The original AI4I interactive classifier remains a separate workspace. See the [research index](research/README.md) for reproducibility and limitations. All four official legacy C-MAPSS test populations have been observed; future model changes require new independent evaluation. See the [NASA multi-regime findings](research/CMAPSS_MULTIREGIME_FINDINGS.md), [regime-development findings](research/CMAPSS_REGIME_DEVELOPMENT_FINDINGS.md), [measurement reliability](research/MFPT_COMMON_MODE_FINDINGS.md), [capture advisory](docs/capture_advisory.md), [Paderborn physical cohort](research/PADERBORN_COHORT_FINDINGS.md), and [bounded release closure](docs/next_research_release_closure.md).

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
