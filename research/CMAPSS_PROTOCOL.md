# C-MAPSS temporal prognostics protocol

Source: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data

Obtain the original NASA archive, inspect its terms and extract the original train_FD001.txt, test_FD001.txt and RUL_FD001.txt into a local directory. Do not commit raw datasets. Keep source provenance and file hashes.

Development:
    python -m research.cmapss_baseline --data-dir /path/to/C-MAPSS --subset FD001

Initial candidates: constant training-target median, ridge snapshot, histogram gradient boosting snapshot and causal rolling-feature gradient boosting. No capped targets. Window 20, fixed seed 42, group-disjoint 80/20 split by engine. Evaluate one deterministic truncated prefix per validation unit. Select smallest validation RMSE, break ties lexicographically. This initial split is a development diagnostic, not an uncertainty estimate.

After protocol freeze only:
    python -m research.cmapss_baseline --data-dir /path/to/C-MAPSS --subset FD001 --official

Refit selected candidate on all official training engines and evaluate one endpoint per official test engine. MAE/RMSE in cycles; asymmetric NASA score is summed over endpoints. Do not choose model or thresholds using official targets. Preserve results and record code revision and environment externally. Subsequent changes require a new documented evaluation protocol, not repeated optimization on the official test.

Causal features must be prefix invariant and never combine histories across units. Unit identity is excluded from predictive features. Training RUL uses complete trajectories only; official test RUL comes from supplied offsets. No claim of real-world engine safety or calendar-time forecasting. Results remain pending until actual execution.
