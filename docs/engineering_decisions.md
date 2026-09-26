# AERIS Engineering Decisions

## 1. Scope before complexity

The first release deliberately limits itself to:

- fault detection
- calibrated failure-risk scoring
- model explanation
- one focused visualization
- defensible secondary failure-mode attribution

RUL, counterfactual simulation, LLM reporting, streaming and deployment are future work.

## 2. Dataset choice

AI4I 2020 is synthetic. That is a limitation, but it is small enough to audit deeply before the application deadline. AERIS explicitly documents this limitation rather than presenting benchmark scores as production evidence.

## 3. Leakage prevention

Excluded from prediction features:

- UDI
- Product ID
- TWF
- HDF
- PWF
- OSF
- RNF

The failure-mode flags are target-side information and would make the binary model unrealistically easy.

## 4. Engineering feature design

Two deterministic transformations are added to the six observed operating inputs:

- temperature delta = process temperature - air temperature
- mechanical power = torque × rotational speed / 9549.2966

These transformations use only observed inputs. They were evaluated through training-only model comparison and then checked across independent held-out splits. The improvement is treated as benchmark evidence, not proof of physical causality.

## 5. Evaluation

The final seed-42 test set is held out once for the primary evaluation.

Model selection uses stratified cross-validation on the training set. Secondary split-sensitivity and bootstrap audits are downstream robustness checks, not tuning loops.

Primary metric is average precision because the failure class is rare. Precision, recall and F1 are reported alongside it. Accuracy is intentionally not the headline metric.

## 6. Model choice

HistGradientBoosting is the model carried forward from the training-partition comparison because Random Forest is nearly tied on cross-validated PR-AUC while HGB has higher cross-validated recall and F1. The held-out test set is reserved for final comparison rather than model selection.

XGBoost is intentionally not a dependency for v1. A strong scikit-learn implementation is enough to establish the method.

## 7. Risk score

The model output is calibrated using sigmoid calibration. This converts the raw model score into a more useful probability-like risk estimate.

The risk score is still a benchmark estimate, not a physical health measurement.

## 8. Explainability

Permutation importance is used for robust global feature ranking.

SHAP is used for local/global explanation after the core model is established. SHAP values are treated as model attribution, not physical causality. Correlated raw and derived features can share or redistribute attribution.

## 9. Failure modes

AI4I can contain multiple failure flags for a single row. Therefore v1 does not force a single mutually exclusive diagnosis.

HDF, PWF and OSF show enough cross-validated signal to expose as separate mode likelihoods. TWF and RNF are deferred because their benchmark signal remains too weak/unstable.

The very strong HDF benchmark result is not presented as evidence of physical root-cause understanding.

## 10. Console architecture

The Streamlit console trains through `src/console_models.py`, which reuses the canonical model builders from `src/models.py`. The risk model, explanation tree and failure-mode models therefore share the same feature contract and documented architecture instead of having separate UI-only implementations. A runtime test exercises the bundle on a temporary benchmark-shaped dataset.

## 11. Uncertainty, calibration and feature stability

AERIS reports uncertainty around held-out metrics with stratified bootstrap intervals and checks the fixed model across five independent stratified splits. The primary seed-42 evaluation remains the headline result for consistency.

AERIS also checks:
1. held-out metric uncertainty,
2. calibration by product type and selected operating regimes,
3. held-out error profiles,
4. feature-importance stability across five splits.

These checks are descriptive robustness audits, not additional tuning loops.

## 12. Reproducibility

The direct dependencies are pinned to the GitHub Actions validation environment, and `docs/reproducibility_audit.md` records the regenerated benchmark metrics, threshold results, calibration checks, robustness intervals and failure-mode feasibility results. The benchmark CSV remains external to the repository by design.

## 13. What would make v2 stronger?

The highest-value next datasets are real industrial time-series sources such as UCI MetroPT-3, followed by C-MAPSS for temporal degradation/RUL work.

These are deliberately outside the application-deadline v1 scope.
