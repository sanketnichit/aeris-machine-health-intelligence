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

## Evidence index (2026-11-24)

| Experiment | Evidence | Scope |
|---|---|---|
| AI4I generator-rule and stress audits | [Findings](AI4I_FINDINGS.md) | Synthetic snapshot; rules beat ML at fixed threshold |
| FD001 initial baselines | [Findings](CMAPSS_FINDINGS.md) | Development; constant beats learned models on middle-life prefixes |
| FD001 stages and landmarks | [Findings](CMAPSS_STAGE_FINDINGS.md) | Development; personalized model improves late-life forecasting |
| FD001 paired and risk audits | [Findings](CMAPSS_RISK_FINDINGS.md) | Exploratory engine-cluster bootstrap and quantile calibration |
| FD001 maintenance replay | [Implementation](cmapss_maintenance_replay.py) | Hypothetical costs and lead times; execution pending verification |
| FD001 official endpoint v1 | [Frozen protocol](FD001_OFFICIAL_PROTOCOL.md) | Fixed candidates and untouched official endpoints at protocol freeze; execution pending verification |

The development workflow is [research-cmapss.yml](../.github/workflows/research-cmapss.yml). The official workflow is separate, pinned to its frozen implementation revision. See [research-fd001-official.yml](../.github/workflows/research-fd001-official.yml). Do not use official test outcomes to optimize or select candidates.

## Current milestone
Verify and publish the maintenance replay and frozen official endpoint results. Integrate a user-facing evidence console only after distinguishing evaluated capabilities from proposed features. Experimental bearing replication remains pending; no claim of field safety or independent replication.
