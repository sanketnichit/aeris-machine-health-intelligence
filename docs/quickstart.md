# AERIS quickstart

Python 3.12 is the CI-tested runtime. See VERSION for the current candidate. AERIS is a research demonstrator, not certified machinery monitoring.

## Start the complete local stack

With Docker and Docker Compose installed, clone the repository and run:

```bash
git clone https://github.com/sanketnichit/aeris-machine-health-intelligence.git
cd aeris-machine-health-intelligence
docker compose up --build --detach --wait
```

Dashboard: http://127.0.0.1:8501. API: http://127.0.0.1:8080. Both host ports are local-only. For a disposable demonstration database, use a new Compose project name; do not mix demo records with confidential telemetry.

With Python installed on the host, populate the synthetic fleet:

```bash
python scripts/demo_fleet.py
```

The replay is deterministic and idempotent; its historical timestamps are not live measurements. Optional periodic freshness monitoring: `docker compose --profile monitoring up --detach --wait`. Only assets with configured freshness limits are scanned. See [API guide](api.md) for opt-in review actions, shared token and backup instructions.

Stop services with `docker compose down`; the named database volume persists. Adding --volumes destroys that project's stored telemetry.

## Alternative: Python-only setup

```bash
python -m venv .venv
```

Activate in Windows PowerShell using `.\.venv\Scripts\Activate.ps1`, or macOS/Linux using `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
python -m research.verify_evidence
python -m pytest -q
python -m streamlit run app.py
```

In a second activated terminal, run `python -m src.api` to enable the fleet workspace. Run the demo client in another terminal. The research workspace reads committed evidence without raw dataset acquisition or training. AI4I classification may download the UCI benchmark and fit models on first use.

## Demonstration walkthrough

1. Research intelligence: evidence map, official NASA result and the asymmetric-penalty ranking. Explain that simulated engines differ from industrial field assets.
2. Temporal replay and physical vibration replay: change the observed endpoint; reveal ground truth only for retrospective inspection.
3. Adaptive reliability and independent replication: show zero accepted forecasts and failure to replicate adaptive superiority.
4. Telemetry fleet: choose synthetic-drift, inspect the review recommendation, reasons and withheld forecast. Expand monitoring events, incidents and deviation history; contrast synthetic-missing.
5. Virtual degradation laboratory: compare three maintenance policies with shared random innovations, vary workload and hypothetical costs, and inspect the separate measured vibration-state audit. Neither model is a calibrated physical twin.
6. Technical report: download the evidence-linked report. Explain negative results and deployment limits.

## Reproduction

```bash
python -m research.technical_report --output AERIS_technical_report.md
```

For a release bundle, verify SHA256SUMS using a compatible SHA-256 utility, extract the source ZIP and use the Python-only setup above. The bundle records the tested revision and resolved dependency environment.

If evidence integrity fails, restore registered files rather than bypassing verification. If dependencies fail, check Python 3.12 and the virtual environment. Raw benchmark archives are acquired only by dedicated experiment workflows.

See [architecture](architecture.md), [research index](../research/README.md), [virtual laboratory](digital_twin.md) and [roadmap](roadmap.md).
