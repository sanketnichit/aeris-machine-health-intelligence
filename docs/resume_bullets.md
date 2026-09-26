# AERIS — Resume-Ready Project Content

## Recommended project entry

**AERIS — Machine Health Intelligence | Python, scikit-learn, SHAP, Streamlit**
Built an explainable predictive-maintenance pipeline for imbalanced machine-failure detection, calibrated risk scoring and secondary failure-mode attribution; validated robustness with bootstrap, split-sensitivity, calibration and feature-stability audits.

## Strong 3-bullet version

- Built an end-to-end predictive-maintenance pipeline on the UCI AI4I 2020 benchmark using HistGradientBoosting with sigmoid calibration; achieved 0.899 PR-AUC, 0.965 precision, 0.809 recall and 0.880 F1 on a held-out stratified test set.
- Engineered temperature-delta and mechanical-power features from observed operating signals; controlled ablation improved cross-validated PR-AUC from 0.803 to 0.871 and held-out PR-AUC from 0.849 to 0.899 without using target-side failure flags.
- Added SHAP and permutation explanations, 3,000-replicate bootstrap uncertainty, five-split sensitivity, subgroup calibration and held-out error audits, then exposed the shared model bundle through a Streamlit Machine Health Console.

## Concise 2-bullet version

- Developed an explainable machine-failure risk model with HistGradientBoosting and sigmoid calibration, reaching 0.899 PR-AUC and 0.880 F1 on a held-out AI4I 2020 benchmark test set.
- Validated feature value and model stability with controlled ablation, bootstrap intervals, split sensitivity, calibration/error audits and SHAP/permutation explanations; packaged the pipeline in a Streamlit engineering console.

## One-line portfolio summary

AERIS is an auditable predictive-maintenance prototype that turns observed machine signals into calibrated failure risk, model explanations and secondary failure-mode likelihoods, with explicit uncertainty and synthetic-data caveats.

## Skills represented

Python: pandas, NumPy, scikit-learn, Streamlit, SHAP

Machine learning: classification, gradient boosting, probability calibration, imbalanced-class evaluation

Evaluation: PR-AUC, precision, recall, F1, Brier score, bootstrap uncertainty, split sensitivity, calibration analysis, feature ablation

Explainability: permutation importance, SHAP, local prediction analysis

Engineering practice: feature contracts, reusable model builders, tests, pinned dependencies, GitHub Actions CI, reproducibility documentation

## ATS phrase

Python | pandas | NumPy | scikit-learn | HistGradientBoosting | Probability Calibration | PR-AUC | Precision/Recall | Brier Score | SHAP | Streamlit | GitHub Actions | Predictive Maintenance | Fault Detection

Add SQL separately only where SQL is genuinely demonstrated elsewhere in the resume.

## Positioning

Describe AERIS as an auditable predictive-maintenance benchmark rather than a finished industrial system. The strongest evidence is the controlled feature ablation, calibration work, uncertainty audits, shared offline/console architecture and explicit limitations.

## Claim checklist

- 0.899 held-out PR-AUC
- 0.965 precision at 0.50
- 0.809 recall at 0.50
- 0.880 F1 at 0.50
- 0.0075 Brier score
- engineered-feature ablation
- SHAP and permutation importance
- bootstrap, split-sensitivity, calibration and error audits
- Streamlit console
- GitHub Actions CI
- reproducibility documentation
- synthetic benchmark limitation

## Avoid

Do not claim production-ready predictive maintenance, real-time fault detection, root-cause diagnosis, industrial validation, or use of Red Bull/F1 telemetry.