# PRONOSTIA independent method replication — v1

Execution: https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45434619220
Frozen implementation with ingestion-only amendments: dae11c810fd28c0d8cc7b9ff174e368ebb7cc4a0
Archive SHA256: e21bb22bd8d54fd18ebe98b4b4e094c0c40469bda19811a2a642d5cc84ebd81f
Protocol: [PRONOSTIA_PROTOCOL.md](PRONOSTIA_PROTOCOL.md)
Exact evidence: [pronostia_summary.json](evidence/pronostia_summary.json)

Complete histories for six learning and eleven evaluation bearings were validated against the recording-count contract. No truncated challenge test histories were treated as failures. Identical duplicate recordings were counted once. All five fixed candidates were scored on 44 retrospective endpoints (four per held-out bearing). No weights, threshold or primary candidate were selected using evaluation outcomes.

| Candidate | MAE | RMSE |
|---|---:|---:|
| Age reference | 530.159 | 663.970 |
| Learned | 448.141 | 564.995 |
| Switch 2x (primary) | 508.888 | 650.863 |
| Switch 4x | 511.280 | 652.347 |
| Ramp 2x–4x | 509.312 | 651.098 |

Errors are in remaining recorded snapshots. The primary improves MAE by 4.0% versus age reference, but has 13.6% higher MAE than learned. The learned comparator improves MAE by 15.5% versus age reference. Thus the adaptive advantage over learned forecasting on XJTU did not replicate.

| Lifetime stage | Age reference MAE | Learned MAE | Switch 2x MAE |
|---|---:|---:|---:|
| 25% | 940.909 | 650.193 | 940.909 |
| 50% | 271.455 | 479.413 | 271.455 |
| 75% | 427.636 | 304.231 | 436.484 |
| 90% | 480.636 | 358.726 | 386.705 |

At fixed observed ages 20, 50 and 100, learned MAE is lower than age reference, whereas the 2x gate returns the same aggregate error as the reference. The stage-90 improvement of the gate over age reference does not establish a usable operational lifetime-stage switch. The gate uses observable signals only. Full landmark and per-bearing metrics are available in the evidence file.

## Interpretation
This is independent-platform method replication with new fitted weights, not direct transfer of a model. Early learned performance differs from XJTU, so the earlier motivation for a universal vibration gate is not supported. The two datasets have different recording cadence and signal window lengths; do not pool raw snapshot errors. The small held-out population and correlated endpoints limit inference. No uncertainty calibration or abstention validation was performed, and this is not official challenge endpoint scoring. The evaluation population is now observed; do not tune a new gate on it and describe that as independent confirmation. No field safety, state-of-the-art or realized-savings claim.
