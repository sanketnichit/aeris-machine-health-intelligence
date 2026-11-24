# FD001 official endpoint evaluation — frozen v1

Frozen 2026-11-24 before official test target evaluation in this research program.

## Dataset and identity
Source: https://data.nasa.gov/docs/legacy/CMAPSSData.zip
Expected SHA256:
- train_FD001.txt: 963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8
- test_FD001.txt: 3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851
- RUL_FD001.txt: a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca

100 complete training engines, 100 truncated test engines. Uncapped cycle RUL. One prediction at each official test endpoint.

## Fixed candidates
Primary: relative HGB (causal rolling features and first-observation deviations), selected from the previous stage development audit on aggregate MAE/RMSE. This does not claim superiority on asymmetric cost.
Comparators: empirical age-conditioned median, constant training-row median, snapshot HGB, fixed age-adaptive blend. The blend was informed by development findings. HGB uses max_iter=150, random_state=42, early_stopping=False, remaining estimator defaults; all fitted on all training rows. Window 20. Clip predictions below zero. No feature fitting or tuning on test data.

## Outcomes
Primary metric MAE. Secondary RMSE, summed NASA asymmetric score, signed error, severe over/underprediction fractions (>20 cycles), paired engine bootstrap of primary minus age baseline MAE (5000 draws, seed 42). All candidates reported regardless of ranking. No official-label-based model selection, calibration, threshold tuning or rerunning modified candidates under this protocol. Compute all endpoint predictions before reading target values. Record dataset hashes, code revision and environment; preserve individual predictions and outcomes.

This fixed evaluation concerns simulated FD001 engines only. Development and official endpoint distributions differ. No novelty, field reliability, safety or maintenance savings claim. Uncertainty intervals and maintenance policies are separate exploratory development experiments and are not part of this frozen point-forecast comparison.
