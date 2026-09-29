# Dataset

Put the AI4I 2020 CSV here:

    data/ai4i2020.csv

From the repo root, you can download it with:

    python scripts/download_dataset.py

The script downloads the UCI file, checks the header and saves it to the path above. Use --force if you want to replace an existing copy.

Source:

- UCI Machine Learning Repository, dataset 601
- DOI: https://doi.org/10.24432/C5HS5C
- License: CC BY 4.0

The raw CSV is not committed to GitHub, so this setup step is needed after a fresh clone.
