# Vibration-state calibration findings v1

[Executed audit](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45444550319) · [Frozen protocol](TWIN_CALIBRATION_PROTOCOL.md) · [Registered results](evidence/twin_calibration_summary.json)

Revision: `9c5a20f69251c79d293f830648bacd603a2b654c`.

The six learning bearings provided 372 nonoverlapping 20-record transitions. The eleven previously observed evaluation bearings provided 54 observable-age endpoints. No evaluation bearing was used to fit global or condition-specific drift. The forecast target is the dimensionless log vibration ratio, not damage or RUL.

| Predictor | MAE | RMSE |
|---|---:|---:|
| Persistence | 0.025678 | 0.045993 |
| Global drift | 0.025678 | 0.045993 |
| Condition-specific drift (primary) | 0.025379 | 0.045175 |

The global median increment is zero. Condition-specific increments are 0, 0.005906 and 0.001342. The primary reduces pooled endpoint MAE by 1.16%; equal-bearing mean paired MAE difference is -0.000233. Four bearings improve, two worsen and five tie. Three of six landmark groups improve, three worsen. No statistical superiority is established.

The empirical residual band covers 54/54 targets, with mean width 0.473209 log-ratio units. This is descriptive, not calibrated 90% coverage; it is broad relative to observed forecast errors and the evaluation endpoints are clustered by bearing.

The result does not justify identifying virtual material wear from vibration or transferring the simulator's maintenance costs to real assets. These evaluation histories were previously examined, so the result is exploratory and not a fresh blind confirmation. Keep the virtual wear model separate from measured signal forecasting.
