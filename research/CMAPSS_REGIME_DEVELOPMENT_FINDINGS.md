# NASA training-only regime development — findings

[Protocol](CMAPSS_REGIME_DEVELOPMENT_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45615446421) | [Evidence](evidence/cmapss_regime_development_summary.json)

21 scenarios, 418 within-subset and 359 transfer landmark assessments. Repeated ages and repeated target populations are not independent endpoints. All training hashes match the registered NASA source; the fit, calibration and evaluation engine IDs are disjoint within each subset. Official test offsets were not accessed. Ten targeted tests passed.

| Source | Target | Age | Endpoints | Settings rejected | Accepted | Regime MAE | Raw interval coverage |
|---|---|---:|---:|---:|---:|---:|---:|
| FD001 | FD001 | 50 | 20 | 1 | 0 | 36.035 | 100.0% |
| FD001 | FD001 | 100 | 20 | 2 | 0 | 31.479 | 85.0% |
| FD001 | FD001 | 150 | 19 | 0 | 0 | 11.877 | 100.0% |
| FD001 | FD002 | 50 | 52 | 52 | 0 | 59.165 | 76.9% |
| FD001 | FD002 | 100 | 52 | 52 | 0 | 44.782 | 59.6% |
| FD001 | FD002 | 150 | 48 | 48 | 0 | 59.205 | 68.8% |
| FD001 | FD003 | 50 | 20 | 0 | 0 | 55.574 | 85.0% |
| FD001 | FD003 | 100 | 20 | 0 | 0 | 56.270 | 55.0% |
| FD001 | FD003 | 150 | 20 | 0 | 0 | 53.957 | 75.0% |
| FD001 | FD004 | 50 | 50 | 50 | 0 | 67.201 | 74.0% |
| FD001 | FD004 | 100 | 50 | 50 | 0 | 64.101 | 46.0% |
| FD001 | FD004 | 150 | 47 | 47 | 0 | 59.621 | 70.2% |
| FD002 | FD002 | 50 | 52 | 1 | 0 | 37.931 | 88.5% |
| FD002 | FD002 | 100 | 52 | 1 | 0 | 27.472 | 94.2% |
| FD002 | FD002 | 150 | 48 | 2 | 46 | 12.649 | 93.8% |
| FD003 | FD003 | 50 | 20 | 2 | 0 | 57.476 | 90.0% |
| FD003 | FD003 | 100 | 20 | 2 | 0 | 47.232 | 90.0% |
| FD003 | FD003 | 150 | 20 | 1 | 0 | 28.609 | 95.0% |
| FD004 | FD004 | 50 | 50 | 7 | 0 | 49.879 | 96.0% |
| FD004 | FD004 | 100 | 50 | 7 | 0 | 41.438 | 98.0% |
| FD004 | FD004 | 150 | 47 | 1 | 6 | 25.599 | 87.2% |

All 152 FD002 and 147 FD004 transfer assessments are outside setting support, but none of the 60 FD003 assessments are. The explicit domain gate withholds every transfer. Setting compatibility is not fault-mode compatibility.

The illustrative 80-cycle width gate accepts only 52/418 within-subset assessments, all at age 150: 46/48 FD002 and 6/47 FD004. Retained interval coverage is 43/46 and 6/6 respectively; two accepted FD002 forecasts overpredict by more than 20 cycles. Zero acceptance elsewhere means retained error is undefined, not zero. Regime normalization improves raw MAE versus the original relative model in 6/12 within-subset scenarios; no universal advantage is established.

This is development on previously available simulated training populations. No official-label tuning, independent validation, conditional conformal guarantee after selection, or operational authorization. Do not adjust the width threshold using these outcomes and call the result validation.
