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

## Post-release NASA multi-regime evidence

The [frozen evaluation](CMAPSS_MULTIREGIME_FINDINGS.md) adds 607 simulated official endpoints. Direct FD001 relative-HGB transfer is worse than the age reference in MAE on FD002, FD003 and FD004, with large asymmetric errors on multi-condition subsets. The fixed within-subset training procedure improves MAE versus age-only in each new subset, but does not establish a universally superior model. No candidate selection on the official test labels; all four populations are now observed. This is evidence against unqualified cross-regime deployment, not independent physical validation.

## Training-only regime development

The [development findings](CMAPSS_REGIME_DEVELOPMENT_FINDINGS.md) show settings support cannot identify all domain shifts. The illustrative 80-cycle width gate accepts only 52 within-subset landmark forecasts, two with overprediction greater than 20 cycles. No selective coverage guarantee or physical validation is established.

## Terminal Paderborn conditional transfer

The [conditional study](PADERBORN_CONDITIONAL_FINDINGS.md) does not establish reliable cross-platform diagnostic performance. Both timing hypotheses accepted six of 44 damaged recordings correctly and produced three false suggestions on 24 healthy recordings. All 68 decisions agreed, but physical geometry and clock calibration are not verified. No retuning was performed. The bounded research scope is closed with this negative outcome.
