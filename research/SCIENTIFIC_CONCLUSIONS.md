# Scientific conclusions — research release scope

AERIS investigates machine-health prediction, evidence reliability and local monitoring through four benchmark datasets and isolated synthetic simulations. This is a research demonstrator, not a validated industrial prognostic product.

## Evidence synthesis

| Experiment | Supported observation | Claim not supported |
|---|---|---|
| [AI4I](AI4I_FINDINGS.md) | Known generator rules beat the calibrated classifier at the fixed threshold; corruption and operating-regime audits expose sensitivity. | Real-world failure classification or root-cause discovery. |
| [Official NASA FD001](FD001_OFFICIAL_FINDINGS.md) | Frozen relative-feature primary MAE 17.346 cycles versus age reference 29.160; the adaptive secondary achieved 15.328. The primary asymmetric score is worse than age reference. | State-of-the-art ranking or retrospective promotion of the secondary to a new independently tested primary. |
| [XJTU-SY](XJTU_FINDINGS.md) | Learned model outperformed the age reference under held-out conditions, but not under held-out bearings. | Consistent physical-bearing generalization. |
| [Adaptive reliability](XJTU_ADAPTIVE_FINDINGS.md) | Signal gating improved some development metrics; the evaluated reliability policy accepted 0/112 forecasts, with no finite nominal 90% intervals. | A deployable selective prediction policy. |
| [PRONOSTIA replication](PRONOSTIA_FINDINGS.md) | Frozen adaptive method did not beat the learned comparator on the independent physical platform. | Universal superiority of adaptive gating or direct weight transfer. |
| [Measured state transition](TWIN_CALIBRATION_FINDINGS.md) | Condition-specific drift reduced pooled MAE by 1.16% versus persistence on 54 previously observed held-out endpoints; residual bands were broad. | Meaningful superiority, calibrated prediction bands or a physical damage model. |
| [Virtual maintenance sensitivity](TWIN_SENSITIVITY_FINDINGS.md) | Condition-based policy had lowest simulated mean cost in 48/54 scenarios including ties. | Industrial maintenance savings, physical model validity or a recommended deployment policy. |

## Final research position

No universal winning predictor is established. Benchmark populations and target units differ; do not pool their raw MAE or claim a single accuracy percentage. The official and independent evaluation outcomes are already observed. Future model selection requires a new evaluation population. Negative results are part of the release, not implementation defects to hide.

The monitoring service's advisory intentionally withholds all operational remaining-life and failure-probability estimates. It exposes descriptive telemetry, explicit policy breaches, missing evidence and review history. The stochastic virtual wear laboratory and measured vibration-state forecasting are separate experiments.

## Reproducibility

The registered JSON reports, integrity manifest, execution links and frozen protocols preserve the numerical findings. The generated technical report is an evidence-linked synthesis. Hash checking detects changes relative to the registered manifest; it is not an authenticity signature or peer review. Raw benchmark data are acquired in dedicated experiment workflows and are not redistributed in the source bundle.

## Beyond the research release

A separate program must establish asset-specific sensing and calibration, prospective outcomes, operational safety, encrypted and role-based access, scale and resilience, and independent engineering review. None is a condition for honestly presenting the current research prototype, but each is necessary before claiming production readiness.
