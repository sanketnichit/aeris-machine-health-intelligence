# AERIS quickstart

Research release candidate 0.1.0-rc.1. Python 3.12 is the CI-tested runtime. AERIS is not a certified monitoring or maintenance decision system.

## Install

Clone the public repository:

```bash
git clone https://github.com/sanketnichit/aeris-machine-health-intelligence.git
cd aeris-machine-health-intelligence
python -m venv .venv
```

Activate the environment in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m pip install -r requirements.txt
python -m research.verify_evidence
python -m pytest -q
python -m streamlit run app.py
```

Open http://localhost:8501. The default research workspace works with committed evidence; it does not download raw datasets or train models. Selecting AI4I classification can download the UCI benchmark and fit models on first use.

## Five-minute demonstration

1. Evidence map: inspect the research populations and limitations.
2. Official NASA test: compare the frozen primary and secondary candidates, noting the different ranking under asymmetric penalty.
3. Temporal replay: change observed cycle and alert threshold; reveal ground truth only for retrospective inspection.
4. Physical vibration replay: choose Bearing1_3, advance observed recording, inspect RMS and crest, compare learned and statistical forecasts. The displayed points are subsampled; this is not a live connection.
5. Independent replication: explain why the fixed vibration gate did not beat the learned model on PRONOSTIA.
6. Adaptive reliability: inspect zero accepted forecasts and sparse calibration; do not present this as validated reliability.
7. Technical report: download the evidence-linked Markdown report.

## Reproducibility and troubleshooting

If evidence integrity fails, restore the registered files from the repository rather than bypassing verification. If dependencies fail to install, check Python 3.12 and the active virtual environment. Raw physical benchmark archives are not required for the read-only console. Separate experiment workflows acquire those archives and preserve execution artifacts.

Run `python -m research.technical_report --output AERIS_technical_report.md` for a deterministic local report.

See [architecture](architecture.md) and the [research index](../research/README.md). No prospective field validation, certified safety, or realized savings are claimed.
