# XJTU-SY physical bearing development protocol v1

Source: https://biaowang.tech/xjtu-sy-bearing-datasets/
Citation: B. Wang, Y. Lei, N. Li, N. Li, “A Hybrid Prognostics Approach for Estimating Remaining Useful Life of Rolling Element Bearings,” IEEE Transactions on Reliability 69(1), 401–412, 2020.

15 physical accelerated run-to-failure bearings, five under each of three load/speed conditions. Two vibration channels; 32768 samples per snapshot at 25.6 kHz; one snapshot per minute. This is a distinct task, not transfer of the NASA engine model. No redistribution of raw recordings.

## Frozen first development experiment
- Read numeric CSV members directly from the supplied zip without extracting paths. Require all 15 bearing IDs, unique contiguous snapshot indices, finite two-channel observations and expected sample count. Record archive SHA256 and observed per-bearing counts.
- Extract per-channel RMS, peak, crest factor, kurtosis and high-frequency power fraction from each observed snapshot. Relative RMS uses only the first snapshot of that bearing. No per-bearing full-life normalization or future data in features.
- Evaluate one bearing at a time using leave-one-bearing-out, and separately hold out each operating condition. Fit on other bearings only; report all folds. Fixed observable ages and relative stages are different tasks; for this first experiment use retrospective 25%, 50%, 75%, 90% endpoints for scoring only. Targets are snapshots remaining until the last recorded observation, not independently measured failure timestamps.
- Compare age-conditioned empirical median to fixed HGB age + vibration features; report per-bearing and aggregate MAE/RMSE, and stage results. No tune-on-held-out-fold or claims of final confirmation.
- Data are physical laboratory experiments, not production machinery. Small correlated sample, accelerated degradation, condition shift and endpoint definition limit inference. No claims of safety, fleet generalization or novelty.

Obtain the archive from the authors' download page or their linked Google Drive file. Archive acquisition is a separate step; confirm its identity before interpreting results. The official FD001 test set is already observed and must not be used for future model selection.
