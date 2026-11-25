# CWRU extension findings — frozen v1

[Protocol](CWRU_EXTENSION_PROTOCOL.md) · [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45560970156) · [Evidence](evidence/cwru_extension_summary.json)

Twenty new recordings, 120 nonoverlapping windows, 983040 effective samples. All 16 fault recordings show increased expected-order fraction with envelope analysis. The expected defect order strictly exceeds both alternatives in only 8 of 16 envelope recordings (4 of 16 raw).

| Seeded fault group | Raw expected first | Envelope expected first |
|---|---:|---:|
| Ball 0.007 inch | 0/4 | 0/4 |
| Inner 0.014 inch | 4/4 | 4/4 |
| Ball 0.014 inch | 0/4 | 3/4 |
| Outer 0.014 inch | 0/4 | 1/4 |

For the maximum of the three order fractions, all 64 fault–normal pairs rank the fault higher with envelope analysis (descriptive pairwise AUC 1.0); none do with raw FFT (AUC 0.0 in the prespecified direction). No threshold was selected. This is not a classification accuracy estimate. The raw result is retained without reversing the score after observation.

The envelope normal maxima range from 0.004724 to 0.009744, while fault maxima range from 0.029542 to 0.147798. The observed separation is confined to these recordings; it cannot establish a deployment threshold. All four small ball faults favor the outer order under envelope analysis. Only one of four larger outer defects favors its expected order. These failures constrain the earlier favorable eight-record study.

Normal acquisition rates differ from fault recordings; polyphase resampling does not remove all acquisition confounds. The same experimental rig, repeated loads, seeded defects and correlated windows prevent interpreting 120 windows or 64 ranking pairs as independent physical assets. No independent-platform generalization, calibrated probability, industrial fault diagnosis or RUL claim. Future methods must be evaluated on an untouched population. No retrospective threshold selection or promotion of a competing feature is performed.

The registered summary was extracted from the successful run's printed record-level output; the full per-window artifact and environment remain linked in its metadata. The original archived v0.1.0 and first spectral audit remain unchanged.
