# FEMTO-ST PRONOSTIA method replication v1

Source: NASA PCoE dataset repository https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
Archive listed by NASA: https://phm-datasets.s3.amazonaws.com/NASA/10.+FEMTO+Bearing.zip
Citation: Nectoux et al., PRONOSTIA: An experimental platform for bearings accelerated degradation tests, IEEE PHM 2012.

Frozen before evaluation. Independent physical platform relative to XJTU; replication of method, not direct transfer of fitted weights.

## Population and data contract
Require the six complete learning bearings (Bearing1_1,1_2,2_1,2_2,3_1,3_2) and eleven complete Full_Test_Set bearings (1_3–1_7,2_3–2_7,3_3). Do not use the truncated Test_set as complete histories. Nested zip archives allowed; ignore temperature files. Each acceleration recording contains 2560 samples in two channels (last two of six columns, comma or semicolon separated), at 25.6 kHz, nominally every ten seconds. Require finite values, contiguous numbered recordings, unique identities and published full-life counts where verified. Record downloaded archive fingerprint and observed counts; no raw recordings redistributed.

## Fixed comparison
Fit once on six learning bearings only; apply the existing XJTU feature extraction (RMS, peak, crest, kurtosis, high-frequency fraction, relative RMS) with sample count 2560, equal-bearing HGB training weights, max_iter=150, seed42, early_stopping=False. Use the empirical age-conditioned median of surviving learning lifetimes, learned model, 2x switch, 4x switch, and 2x–4x ramp exactly as in XJTU. Gate uses first-five and trailing-five RMS medians; no target data. Primary comparison is fixed 2x switch versus statistical and learned baselines, mean absolute error across four retrospective lifetime-stage endpoints (25/50/75/90%) per evaluation bearing. Secondary: RMSE, each bearing's MAE, per-stage errors, fixed observable ages 20/50/100/200/500/1000 snapshots with survivor counts. Report every candidate. Test endpoints use remaining recorded snapshots, not independently timed failures. These stages are not official challenge endpoint scoring and not a live decision signal. No threshold tuning or selection using the eleven evaluation histories.

## Limits
Only six fitting and eleven evaluation bearings; no independently calibrated uncertainty or safety guarantee. This does not validate the abstention policy or establish condition-disjoint generalization. Differences in recording intervals mean raw errors are not directly comparable with XJTU. No field or state-of-the-art claims. If the source does not supply full trajectories, fail closed rather than treat truncated recordings as failures.
