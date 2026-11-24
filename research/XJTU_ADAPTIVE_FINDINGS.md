# XJTU-SY adaptive and reliability development findings

Signal-gate execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45431336050 (20118c394b7e105e706169be4f0e5861df727b87).
Reliability execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45431765221 (0bcfcbe003d9e82fbc90dceeb7ed8a10b00ab8a5).
See exact [gate summary](evidence/xjtu_gate_summary.json) and [reliability summary](evidence/xjtu_reliability_summary.json).

## Signal-gate comparisons
Four retrospective endpoints per bearing (60 per split), MAE/RMSE in remaining recorded snapshots.

| Candidate | Bearing MAE | Bearing RMSE | Condition MAE | Condition RMSE |
|---|---:|---:|---:|---:|
| Age reference | 381.233 | 524.177 | 593.600 | 849.027 |
| Learned | 400.831 | 649.756 | 399.396 | 728.963 |
| Switch 2x | 257.975 | 413.914 | 413.114 | 685.266 |
| Switch 4x | 264.229 | 415.915 | 422.922 | 688.688 |
| Ramp 2x–4x | 259.477 | 414.491 | 420.506 | 687.363 |

The 2x switch improves aggregate held-out-bearing MAE by 32.3% versus age reference and 35.6% versus learned. The learned model still has the lowest condition-held-out MAE. The gate uses observed vibration ratios only; retrospective stages select scoring rows, not switching decisions. Fixed observable ages 20, 50, 100, 200, 500, 1000 have 15,14,13,7,4,3 surviving bearings respectively. The 2x switch activates for 1,2,4,1,1,0 of those bearings. The small populations limit inference. No gate is selected for deployment.

## Selective forecasting failed to retain forecasts
The reliability audit uses a different fitting/calibration partition, so its errors are not directly comparable with the above models. All 56 landmark assessments per split (112 total repeated assessments of 15 assets) were rejected by the fixed review policy. Retained MAE is undefined. This is a negative utility result, not evidence of safe or improved selective forecasting.

| Age | Eval bearings | Bearing interval n / coverage | Condition interval n / coverage |
|---:|---:|---|---|
| 20 | 15 | 15 / .933 | 15 / .800 |
| 50 | 14 | 14 / .929 | 14 / .571 |
| 100 | 13 | 11 / 1.000 | 13 / .615 |
| 200 | 7 | 1 / 1.000 | 3 / 1.000 |
| 500 | 4 | 0 / undefined | 0 / undefined |
| 1000 | 3 | 0 / undefined | 0 / undefined |

Intervals are nominal 80% marginal split-conformal intervals under exchangeability, which is not assured here. No finite 90% intervals. Wide intervals and model disagreement dominate early; sparse calibration dominates later. Do not relax review criteria and claim validation on the same observed population. Independent confirmation needs more physical assets and explicit calibration/support. All findings are exploratory on already-observed development data; no industrial safety or field performance claim.
