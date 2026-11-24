# AERIS research prototype roadmap

The target is a reproducible research demonstrator, not certified industrial software. The following estimates are planning judgments (not model accuracy, measured performance, or objective completion). Baseline: 78%; current estimate: 90% (equally weighted category estimates, rounded).

| Workstream | Estimate | Remaining completion gate |
|---|---:|---|
| Core ML research | 90% | Freeze a final model comparison and document negative results; retain independent test boundaries. |
| Validation and reproducibility | 90% | Vibration-state and sensitivity audits registered; RC2 clean archive passed; repeat validation on final revision. |
| Application and UX | 90% | Authenticated fleet review passed; desktop screenshots inspected and fleet presentation improved. Latest visual regression and mobile/user feedback remain. |
| Telemetry and monitoring | 95% | Concurrent authenticated workload, periodic worker, backup recovery and incident review passed. Final release smoke gate remains. |
| Twin and decision intelligence | 80% | Measured-state audit and 54-scenario simulation sensitivity completed. Verify integrated reporting; document model-form limitations. No physical calibration claim. |
| Packaging and documentation | 95% | RC2 fresh extracted-archive verification passed; repeat packaging for final release revision. |

No arbitrary commit-count target. A failed experiment is a valid research outcome; it must be reported and not tuned into a claimed independent success. New results are published only after their execution is verified and their content registered.

## Separate industrial readiness gate

The prototype does not establish prospective field performance, equipment-specific calibration, safe control, production authorization or security. Industrial deployment requires a separate validation and engineering program: authenticated encrypted transport, operational monitoring, tested recovery, equipment commissioning, external review and prospective outcomes. The research roadmap does not measure progress toward certification.
