# AERIS — Machine Health Intelligence

**Explainable fault detection and failure-risk scoring for industrial equipment.**

AERIS is a focused predictive-maintenance project built around the **AI4I 2020 Predictive Maintenance Dataset**. The project intentionally prioritizes a small, rigorous end-to-end ML pipeline over a large collection of loosely validated features.

## Project scope

### Core
1. **Fault detection** — classify whether a machine observation indicates failure.
2. **Risk scoring + explanation** — produce a calibrated failure-risk score and explain the prediction using model-derived feature importance.
3. **One engineering visualization** — a compact Machine Health Console for inspecting risk, predicted state and contributing factors.
4. **Failure-mode attribution (secondary)** — show multi-label likelihoods for HDF, PWF and OSF only; sparse/unstable TWF and RNF are explicitly deferred.

### Explicitly out of scope for v1
- Remaining-useful-life (RUL) modelling
- What-if / counterfactual simulation
- LLM-generated engineering reports
- Streaming/Kafka deployment
- C-MAPSS temporal modelling
- Motorsport/FastF1 domain transfer

These are documented as future extensions only. The project does not claim to use proprietary Red Bull/F1 telemetry.

## Dataset

**AI4I 2020 Predictive Maintenance Dataset**  
UCI Machine Learning Repository, dataset ID 601.

Source: https://doi.org/10.24432/C5HS5C  
License: CC BY 4.0

The dataset contains 10,000 machine observations with process variables, product type, a machine-failure target, and failure-mode indicators. The raw CSV is kept outside the repository's first commit; place it under data/ai4i2020.csv before running the scripts.

## Why AI4I instead of C-MAPSS?

C-MAPSS is a stronger benchmark for temporal degradation and RUL prediction, but it introduces substantially more sequence-processing and evaluation complexity. AERIS uses AI4I for v1 so the project can establish a trustworthy detection → classification → explanation pipeline first.

C-MAPSS/RUL is deliberately reserved for future work. AI4I is synthetic, so its results are a controlled benchmark, not evidence about a real machine fleet.

## Data validation

Before modelling, the dataset is checked for:

- missing values
- duplicates
- schema/type consistency
- physically invalid ranges
- target/flag consistency
- class imbalance

Current validation found **3.39% positive machine-failure labels**, making this an imbalanced classification problem. Precision, recall and PR-AUC are therefore prioritized over raw accuracy.

A documented target/flag inconsistency exists in 27 rows; AERIS reports this instead of silently rewriting the source labels.

## Repository structure

```
aeris-machine-health-intelligence/
├── app.py
├── requirements.txt
├── LICENSE
├── DATA_LICENSE.md
├── RUNBOOK.md
├── .github/workflows/ci.yml
├── data/
│   └── README.md
├── src/
│   ├── load_data.py
│   ├── validate_data.py
│   ├── eda.py
│   ├── train_baseline.py
│   ├── model_comparison.py
│   ├── risk_model.py
│   ├── failure_mode_attribution.py
│   ├── explain_model.py
│   └── evaluate_thresholds.py
├── reports/
│   ├── data_validation.md
│   ├── model_comparison.md
│   ├── risk_model.md
│   ├── threshold_analysis.md
│   ├── failure_mode_attribution.md
│   ├── explainability.md
│   └── subgroup_audit.md
├── docs/
│   ├── engineering_decisions.md
│   ├── model_card.md
│   └── demo_script.md
├── figures/
└── tests/
    └── test_data_contract.py
```

## Current status

- [x] Dataset loaded and schema-normalized
- [x] Data validation
- [x] Class-balance analysis
- [x] Exploratory data analysis
- [x] Binary Random Forest baseline
- [x] 3-model comparison with held-out test set
- [x] HistGradientBoosting selected for v1
- [x] Sigmoid-calibrated risk model
- [x] Failure-mode feasibility analysis
- [x] Permutation importance + SHAP explanations
- [x] Machine Health Console
- [x] Threshold/calibration analysis
- [x] Subgroup audit
- [x] Stratified bootstrap uncertainty/error audit
- [x] Fixed-model split-sensitivity audit
- [x] Held-out error analysis
- [x] Data-contract tests + CI

## Planned modelling sequence

The project will be built in the following order:

1. Get one complete baseline model working end-to-end.
2. Compare model families using stratified cross-validation on the training set.
3. Select HistGradientBoosting based on cross-validated PR-AUC and held-out behaviour.
4. Calibrate the selected model's probabilities for the risk score.
5. Add feature-level explanations; start with permutation importance, then SHAP.
6. Add the secondary multi-label failure-mode attribution layer only where the data supports it.
7. Build one focused visualization.

## Running the current pipeline

From the repository root:

```bash
pip install -r requirements.txt
python src/validate_data.py
python src/eda.py
python src/model_comparison.py
python src/risk_model.py
python src/failure_mode_attribution.py
python src/explain_model.py
python src/evaluate_thresholds.py
python src/uncertainty_audit.py
python src/split_sensitivity.py
python src/error_analysis.py
pytest -q
```

The EDA command writes six PNG figures to figures/. The threshold evaluation writes the calibration and precision-recall plots there as well.

### Run the engineering console

```bash
streamlit run app.py
```

The console lets you enter a machine operating state and inspect the calibrated failure risk, model explanation, and HDF/PWF/OSF mode scores.

## Current verified results

The current held-out evaluation uses an 80/20 stratified split with model selection on the training portion only. HistGradientBoosting produced PR-AUC **0.843** on the final test set. After sigmoid probability calibration, the risk model produced **0.849 PR-AUC, 0.926 precision, 0.735 recall, 0.820 F1, and 0.0108 Brier score** at the 0.50 decision threshold. A threshold study, product-type subgroup audit, stratified bootstrap intervals, and split-sensitivity audit are included so the project does not hide the precision/recall trade-off or small-sample uncertainty. The five-split robustness audit reports mean PR-AUC **0.825 ± 0.036** and mean F1 **0.762 ± 0.041** for the fixed v1 model at the 0.50 threshold; the seed-42 split remains the primary held-out evaluation for consistency.

See `reports/model_comparison.md`, `reports/risk_model.md`, `reports/threshold_analysis.md`, `reports/explainability.md`, `reports/subgroup_audit.md`, `reports/uncertainty_audit.md`, `reports/split_sensitivity.md`, and `reports/error_analysis.md` for the full experiment record. See `docs/model_card.md` for intended use and limitations, and `docs/demo_script.md` for the recruiter/interview demo.

## Future work

- NASA C-MAPSS run-to-failure / RUL extension
- temporal degradation modelling
- counterfactual what-if analysis
- streaming telemetry
- deployment and monitoring
- FastF1/motorsport-domain adaptation

## Disclaimer

AERIS is an educational/portfolio project using public benchmark data. It is not a production maintenance system and does not represent Red Bull Powertrains systems, models, telemetry or engineering decisions.
