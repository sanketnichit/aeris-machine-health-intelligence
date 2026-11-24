# AERIS research prototype roadmap

The target is a reproducible research demonstrator, not certified industrial software. The following estimates are planning judgments (not model accuracy, measured performance, or objective completion). Baseline: 78%; current estimate: 94% (equally weighted category estimates, rounded).

| Workstream | Estimate | Remaining completion gate |
|---|---:|---|
| Core ML research | 100% | Research-scope conclusions frozen; negative results and evaluation limits retained. |
| Validation and reproducibility | 95% | All evidence registered and prior tests passed; same-revision acceptance pending. |
| Application and UX | 90% | Authenticated fleet review passed; desktop screenshots inspected and fleet presentation improved. Updated desktop browser regression passed; final acceptance pending. Mobile testing and external user feedback are follow-on goals. |
| Telemetry and monitoring | 95% | Concurrent authenticated workload, periodic worker, backup recovery and incident review passed. Final release smoke gate remains. |
| Twin and decision intelligence | 90% | Measured-state and sensitivity audits integrated and tested; model-form limits frozen. Final acceptance pending; physical calibration outside release scope. |
| Packaging and documentation | 95% | RC2 fresh extracted-archive verification passed; RC3 combined archive and stack acceptance pending; publish only after verification. |

No arbitrary commit-count target. A failed experiment is a valid research outcome; it must be reported and not tuned into a claimed independent success. New results are published only after their execution is verified and their content registered.

## Separate industrial readiness gate

The prototype does not establish prospective field performance, equipment-specific calibration, safe control, production authorization or security. Industrial deployment requires a separate validation and engineering program: authenticated encrypted transport, operational monitoring, tested recovery, equipment commissioning, external review and prospective outcomes. The research roadmap does not measure progress toward certification.
