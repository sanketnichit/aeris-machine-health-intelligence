# AERIS Model Card

## Intended use

AERIS is an educational and portfolio prototype for demonstrating an end-to-end predictive-maintenance workflow:

- binary machine-failure detection
- calibrated risk scoring
- model explanation
- secondary failure-mode attribution

## Not intended for

- real maintenance decisions
- safety-critical control
- deployment on unknown production fleets
- claims about Red Bull Powertrains or Formula 1 telemetry

## Training data

AI4I 2020 Predictive Maintenance Dataset from the UCI Machine Learning Repository.

The dataset is synthetic. It should therefore be treated as a controlled benchmark, not a substitute for real industrial telemetry.

## Inputs

Raw observed inputs:
- machine product type
- air temperature
- process temperature
- rotational speed
- torque
- tool wear

Derived inputs:
- temperature delta = process temperature - air temperature
- mechanical power = torque × rotational speed / 9549.2966

The derived inputs are deterministic transformations of observed signals. They do not use the failure labels.

The following are deliberately excluded from binary failure prediction because they are target-side information or identifiers:

- UDI
- Product ID
- TWF
- HDF
- PWF
- OSF
- RNF

## Metrics

Primary: average precision / PR-AUC.

Secondary: precision, recall, F1, ROC-AUC and Brier score.

Primary seed-42 held-out risk-model result:
- PR-AUC: 0.899
- Precision @ 0.50: 0.965
- Recall @ 0.50: 0.809
- F1 @ 0.50: 0.880
- Brier score: 0.0075

## Known limitations

1. The benchmark is synthetic.
2. Failure events are rare, so some subgroup and failure-mode estimates have high uncertainty.
3. The model captures benchmark correlations, not guaranteed physical causality.
4. The data is not a longitudinal machine fleet with realistic drift.
5. Failure-mode labels can overlap.
6. The calibrated score is useful as a benchmark risk estimate, not a production probability without external validation.
7. The engineering-derived features materially improve benchmark performance, but that improvement may partly reflect structure built into the synthetic data-generation process.
8. Feature attribution is model attribution, not proof of physical root cause.

## Robustness checks

AERIS includes:
- stratified bootstrap intervals around the primary held-out metrics
- fixed-model split sensitivity across five stratified 80/20 splits
- product-type and operating-regime calibration checks
- held-out error analysis
- feature-importance stability across five splits

These are evidence about benchmark robustness, not substitutes for prospective validation on real industrial data.

## Governance principle

AERIS reports where the data or model is weak instead of hiding uncertainty behind a single headline accuracy number.
