# Extra Validation

I kept the extra experiments in this folder so the main AERIS code stays fairly small.

The core project is:

1. machine-failure prediction
2. calibrated risk scoring
3. model explanation
4. a Streamlit demo

The scripts here are mainly for checking whether the result changes under different choices.

## Experiments

| File | What I used it for |
|---|---|
| model_comparison.py | Compare a few model choices using training data only. |
| feature_ablation.py | Check how much the two derived features change the result. |
| evaluate_thresholds.py | Look at different alert thresholds. |
| uncertainty_audit.py | Get bootstrap intervals for the held-out metrics. |
| split_sensitivity.py | See how the fixed model changes across different splits. |
| error_analysis.py | Look at false positives and false negatives. |
| feature_stability.py | Check whether feature rankings stay similar across splits. |
| calibration_audit.py | Check calibration for different groups/operating ranges. |
| failure_mode_attribution.py | Try the AI4I failure-mode labels as separate secondary targets. |

## Running them

From the repository root, after the CSV is in data/ai4i2020.csv:

    python extended-validation/src/model_comparison.py
    python extended-validation/src/feature_ablation.py
    python extended-validation/src/evaluate_thresholds.py
    python extended-validation/src/uncertainty_audit.py
    python extended-validation/src/split_sensitivity.py
    python extended-validation/src/error_analysis.py
    python extended-validation/src/feature_stability.py
    python extended-validation/src/calibration_audit.py
    python extended-validation/src/failure_mode_attribution.py

Reports are written to extended-validation/reports/.

I kept these scripts separate from the main model because they are useful for checking the project, but they are not required just to run the app.
