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
| FD001 maintenance replay | [Implementation](cmapss_maintenance_replay.py) | Hypothetical costs and lead times; [verified summary](evidence/maintenance_summary.json) |
| FD001 official endpoint v1 | [Frozen protocol](FD001_OFFICIAL_PROTOCOL.md) | Fixed candidates; [official findings](FD001_OFFICIAL_FINDINGS.md); test labels now observed |

The development workflow is [research-cmapss.yml](../.github/workflows/research-cmapss.yml). The official workflow is separate, pinned to its frozen implementation revision. See [research-fd001-official.yml](../.github/workflows/research-fd001-official.yml). Do not use official test outcomes to optimize or select candidates.

## Current milestone
The [adaptive physical findings](XJTU_ADAPTIVE_FINDINGS.md) are published, including the failed selective forecasting policy (zero accepted forecasts). The [PRONOSTIA independent replication](PRONOSTIA_FINDINGS.md) is complete. The frozen 2x gate improves MAE over the age reference by 4.0%, but loses to the learned comparator; the XJTU adaptive advantage did not replicate. The evaluation population is now observed. No field safety claim.

## Evidence integrity
Run `python -m research.verify_evidence` from the repository root to check all registered evidence files offline. The manifest records Git blob hashes and byte counts; this is a content-integrity check, not an independent validation of scientific claims. Each evidence addition must be registered with its exact blob hash and byte count before CI can pass. The original run URLs and revisions remain in the evidence files. Preserve earlier evidence rather than replacing experimental outcomes.

## Measured vibration-state transition audit

[Protocol](TWIN_CALIBRATION_PROTOCOL.md) · [Findings](TWIN_CALIBRATION_FINDINGS.md) · [Evidence](evidence/twin_calibration_summary.json). Six learning bearings, eleven previously observed evaluation bearings, 54 short-horizon endpoints. Condition-specific drift improves pooled MAE by 1.16% versus persistence; broad empirical residual bands and mixed bearing-level results preclude a calibrated physical twin claim. The virtual maintenance model remains synthetic.

## Post-release measurement reliability program

The CWRU/MFPT transfer is a selected laboratory diagnostic result, distinct from prognostic forecasting. Subsequent MFPT experiments reuse the same 17 recordings and are retrospective, not new independent samples.

| Audit | Findings |
|---|---|
| Continuous uncertainty | [Interval guard](MFPT_ORDER_UNCERTAINTY_FINDINGS.md) |
| Closed-cell refinement | [Breakpoint results](MFPT_BREAKPOINT_FINDINGS.md) |
| Counterexamples | [Decision instability](mfpt_counterexample_findings.md) |
| Diagnostic possibility sets | [Outer sets](mfpt_possibility_findings.md) |
| Measurement width | [Precision versus bias](MFPT_MEASUREMENT_WIDTH_FINDINGS.md) |
| Bias budget | [Coverage trade-off](MFPT_BIAS_BUDGET_FINDINGS.md) |
| Two-channel fusion | [False agreement](MFPT_MEASUREMENT_FUSION_FINDINGS.md) |
| Common-mode model | [Findings](MFPT_COMMON_MODE_FINDINGS.md) and [frozen protocol](MFPT_COMMON_MODE_PROTOCOL.md) |

The research dashboard and generated technical report expose the registered studies. The [offline capture advisory](../docs/capture_advisory.md) provides a guarded research integration path, not a production decision API. Real instrumentation and independent prospective validation remain required.

## NASA multi-regime official endpoints

[Protocol](CMAPSS_MULTIREGIME_PROTOCOL.md) | [Findings](CMAPSS_MULTIREGIME_FINDINGS.md) | [Evidence](evidence/cmapss_multiregime_summary.json). The frozen FD001 control reproduced exactly; direct primary transfer was worse than the age reference on all three new subsets. All four official populations are now observed. No post-test tuning or field claims.

## Regime-aware development

[Findings](CMAPSS_REGIME_DEVELOPMENT_FINDINGS.md). Setting support detects multi-condition transfer but misses the FD003 domain difference; the fixed selective policy has low coverage. All official labels remain excluded from this development audit.
