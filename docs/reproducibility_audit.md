# Reproducing the Main Result

This note records how I reproduced the main AERIS numbers from the AI4I 2020 CSV.

The dataset is not committed to the repo. Put the source CSV at:

    data/ai4i2020.csv

## Software used

The GitHub Actions validation environment on 2026-09-26 used:

- Python 3.12.14
- pandas 3.0.6
- numpy 2.5.3
- matplotlib 3.11.2
- scikit-learn 1.9.1
- streamlit 1.64.0
- shap 0.52.0
- pytest 9.1.1

The repo pins these direct dependencies in requirements.txt.

## Dataset checks

The AI4I CSV has:

- 10,000 rows
- 14 source columns
- 339 positive machine-failure rows (3.39%)
- no missing values
- no duplicate rows
- no duplicate UDI values
- no duplicate Product ID values
- 27 rows where the binary failure label does not match whether any failure-mode flag is set

The failure-mode flags can overlap, so the secondary failure-mode experiments keep them as separate labels.

## Main model result

Using the current seed-42 stratified 80/20 split, six observed inputs, the two derived features and the calibrated HGB model gives:

| Metric | Result |
|---|---:|
| PR-AUC | 0.8986 |
| Precision @ 0.50 | 0.9649 |
| Recall @ 0.50 | 0.8088 |
| F1 @ 0.50 | 0.8800 |
| Brier score | 0.00752 |

The rounded values used in the README are:

0.899 / 0.965 / 0.809 / 0.880 / 0.0075

The confusion matrix is:

| | Predicted 0 | Predicted 1 |
|---|---:|---:|
| Actual 0 | 1930 | 2 |
| Actual 1 | 13 | 55 |

## How the split is used

The main evaluation is a stratified 80/20 split with random seed 42.

Model selection uses 5-fold stratified cross-validation on the training part only. The held-out test rows are kept aside for the reported result.

## Other checks

The extended-validation folder has additional scripts for:

- model comparison
- feature ablation
- threshold checks
- bootstrap uncertainty
- split sensitivity
- error analysis
- feature-importance stability
- calibration
- failure-mode experiments

These are supporting checks. They are not extra tuning on the final test set.

## What this does and does not show

This note is enough to reproduce the documented AI4I benchmark result.

It does not show that the model will work on real industrial machines. For that, the project would need an external industrial dataset and validation on the actual target population.
