# Dataset

Place the **AI4I 2020 Predictive Maintenance Dataset** CSV here as:

`data/ai4i2020.csv`

### Recommended setup

From the repository root:

```bash
python scripts/download_dataset.py
```

The setup script downloads the official UCI archive, extracts only `ai4i2020.csv`, validates its header, and writes it to the expected path. Use `--force` to replace an existing copy.

Canonical source:

- UCI Machine Learning Repository, dataset ID 601
- DOI: https://doi.org/10.24432/C5HS5C
- License: CC BY 4.0

The project scripts intentionally do not fabricate or alter the source data. Run validation before modelling.

The raw CSV is intentionally **not committed** to GitHub. A fresh clone therefore needs the setup step above before running the modelling pipeline.
