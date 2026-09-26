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

## 4. Evaluation

The final seed-42 test set is held out once for the primary evaluation.

Model selection uses stratified cross-validation on the training set. Secondary split-sensitivity and bootstrap audits are downstream robustness checks, not tuning loops.

Primary metric is average precision because the failure class is rare. Precision, recall and F1 are reported alongside it. Accuracy is intentionally not the headline metric.

## 5. Model choice

HistGradientBoosting currently gives the strongest balance of cross-validated ranking performance and held-out classification performance among the tested baseline families.

XGBoost is intentionally not a dependency for v1. A strong scikit-learn implementation is enough to establish the method.

## 6. Risk score

The model output is calibrated using sigmoid calibration. This converts the raw model score into a more useful probability-like risk estimate.

The risk score is still a benchmark estimate, not a physical health measurement.

## 7. Explainability

Permutation importance is used for robust global feature ranking on the held-out test set.

SHAP is added only after the core model is trusted and is used for local/global explanation. SHAP values are treated as model attribution, not physical causality.

## 8. Failure modes

AI4I can contain multiple failure flags for a single row. Therefore v1 does not force a single mutually exclusive diagnosis.

HDF, PWF and OSF show enough cross-validated signal to expose as separate mode likelihoods. TWF and RNF are deferred because their benchmark signal is too weak/unstable.

## 9. What would make v2 stronger?

The highest-value next dataset is a real industrial time-series benchmark such as UCI MetroPT-3. The next modelling step would be temporal degradation/RUL work on C-MAPSS.

Both are deliberately outside the application-deadline v1 scope.


## 10. Uncertainty and error analysis

AERIS reports uncertainty around held-out metrics with stratified bootstrap intervals and checks the fixed model across five independent stratified splits. The primary seed-42 evaluation remains the headline result for consistency. Held-out error analysis is descriptive only; it does not trigger hidden threshold tuning. The current error profile shows 18 false negatives and 4 false positives at the 0.50 calibrated threshold, with many false negatives carrying the TWF flag. This is treated as a limitation and future investigation point rather than a reason to overstate the current mode layer.
