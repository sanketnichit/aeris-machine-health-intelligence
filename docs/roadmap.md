# AERIS research prototype roadmap

The target is a reproducible research demonstrator, not certified industrial software. The following estimates are planning judgments (not model accuracy, measured performance, or objective completion). Baseline: 78% (equally weighted category estimates, rounded).

| Workstream | Estimate | Remaining completion gate |
|---|---:|---|
| Core ML research | 90% | Freeze a final model comparison and document negative results; retain independent test boundaries. |
| Validation and reproducibility | 85% | Complete vibration-state audit, publish its exact evidence, reproduce from a clean release. |
| Application and UX | 80% | Full browser walkthrough including populated fleet, failure states and virtual lab; visual inspection and usability review. |
| Telemetry and monitoring | 85% | Test periodic worker and incident actions in the running stack; document backup and access-control limitations. |
| Twin and decision intelligence | 55% | Evaluate measured vibration dynamics and uncertainty; explicitly separate virtual wear scenarios from calibrated physical predictions. |
| Packaging and documentation | 75% | Consolidated technical report, architecture and demo instructions; clean release candidate including all current modules. |

No arbitrary commit-count target. A failed experiment is a valid research outcome; it must be reported and not tuned into a claimed independent success. New results are published only after their execution is verified and their content registered.

## Separate industrial readiness gate

The prototype does not establish prospective field performance, equipment-specific calibration, safe control, production authorization or security. Industrial deployment requires a separate validation and engineering program: authenticated encrypted transport, operational monitoring, tested recovery, equipment commissioning, external review and prospective outcomes. The research roadmap does not measure progress toward certification.
