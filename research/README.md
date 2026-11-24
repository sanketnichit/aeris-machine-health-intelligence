# AERIS research program

## Baseline freeze
The existing AI4I benchmark at commit 47a677344f6bba8e429fe1bb79a7a73675d7b39e is the reference. Its reported AP 0.8986 is a synthetic snapshot-classification result, not prospective failure forecasting. Do not overwrite its reports with new-task results.

## Primary research question
Can physics-informed temporal representations and uncertainty-aware abstention improve prognostic decisions on unseen machine units and operating regimes relative to simple baselines? This is a hypothesis, not a novelty or performance claim.

## Evidence gates
1. Harden cache identity and report provenance; add regression tests.
2. Compare known AI4I generation-rule baselines against ML; label rule reconstruction explicitly. Stress test sensor noise, missingness and operating-regime shifts. Freeze protocols before final evaluation.
3. Build a separate run-to-failure benchmark: start with NASA C-MAPSS, use unit-disjoint development/validation partitions, preserve official test labels, fit preprocessing on training units only, and compare constant/linear/tree baselines before sequence models. Report MAE, RMSE and asymmetric penalty; distinguish simulated cycles from real time.
4. Add uncertainty intervals calibrated on disjoint units; report coverage, width, selective risk and abstention under shifts. Do not claim coverage under arbitrary shift.
5. Replicate on experimental bearing data using a separate task contract and bearing-disjoint splits. No claim of direct transfer between unrelated assets.
6. Replay telemetry and evaluate alert lead time, false alarms, missed failures and cost sensitivity; no production safety claims without prospective validation.

## Experiment contract
Record dataset source/version/hash, license, unit IDs and split hashes, configuration, seed, code commit, dependency versions, metrics and uncertainty. Keep negative findings. Never tune on final test labels. Report baselines and limitations alongside improvements. Any publication claim requires literature review and independent reproduction.

## Current milestone
Cache correctness and regression tests; no new empirical performance claim.
