# Vibration-state calibration audit v1

This is a measured-signal calibration experiment, not a physical damage model or asset digital twin validation. PRONOSTIA's evaluation histories have already been observed in previous experiments. This new endpoint/task is exploratory held-out evaluation, not a new blind dataset.

Fit only six Learning_set bearings. Evaluate the eleven Full_Test_Set bearings, using the same validated archive contract as the replication experiment. Do not fit global parameters or tune thresholds using evaluation bearings.

## State and transition

Use log of the maximum channel RMS ratio relative to each bearing's first five observations, with a causal trailing five-record median and lower bound one (existing vibration_ratio). This is a dimensionless signal proxy, not material damage. For nonoverlapping 20-record transitions anchored at recording 5, fit a mean increment model on learning bearings. Fit a global median drift, a median drift conditional on operating condition, and empirical residual quantiles from learning transitions. Give each learning bearing equal total weight within its respective fit group. No future lifetime or terminal normalization is used. Clip predicted log ratio to zero.

## Evaluation

At observable ages 50, 100, 200, 500, 1000 and 2000, predict the log ratio 20 recordings later if that target exists. Primary comparator: condition-specific drift versus persistence of the current signal. Global drift is secondary. Report MAE/RMSE, empirical 90% residual-band coverage and mean width; residual bands are descriptive, not conformal or calibrated prediction intervals. Report bearing-level and landmark-level results and counts, plus paired per-bearing mean absolute-error differences. No hyperparameter selection, no RUL extrapolation, no interpretation as health probability. The previously observed bearing populations cannot provide new independent validation of a chosen model.

The exact physical archive is the NASA-listed FEMTO Bearing archive with SHA256 e21bb22bd8d54fd18ebe98b4b4e094c0c40469bda19811a2a642d5cc84ebd81f. Use existing archive parser and causal vibration feature pipeline. The virtual maintenance simulator remains uncalibrated; this audit only establishes whether short-horizon signal dynamics are forecastable with a simple learned drift.
