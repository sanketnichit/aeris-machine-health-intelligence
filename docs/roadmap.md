# AERIS research prototype roadmap

The target is a reproducible research demonstrator, not certified industrial software. The following estimates are planning judgments (not model accuracy, measured performance, or objective completion). Baseline: 78%; current estimate: 85% (equally weighted category estimates, rounded).

| Workstream | Estimate | Remaining completion gate |
|---|---:|---|
| Core ML research | 90% | Freeze a final model comparison and document negative results; retain independent test boundaries. |
| Validation and reproducibility | 90% | Vibration-state audit completed and registered; reproduce from a clean release and verify integrated report. |
| Application and UX | 90% | Research, virtual lab and populated fleet browser checks passed; visual review and user feedback remain. |
| Telemetry and monitoring | 85% | Test periodic worker and incident actions in the running stack; document backup and access-control limitations. |
| Twin and decision intelligence | 65% | Measured vibration dynamics audit integrated; small improvement does not establish superiority. Complete review of simulator assumptions and uncertainty; no physical calibration claim. |
| Packaging and documentation | 90% | Architecture, quickstart, README and changelog consolidated; rc.2 fresh extracted-archive validation pending. |

No arbitrary commit-count target. A failed experiment is a valid research outcome; it must be reported and not tuned into a claimed independent success. New results are published only after their execution is verified and their content registered.

## Separate industrial readiness gate

The prototype does not establish prospective field performance, equipment-specific calibration, safe control, production authorization or security. Industrial deployment requires a separate validation and engineering program: authenticated encrypted transport, operational monitoring, tested recovery, equipment commissioning, external review and prospective outcomes. The research roadmap does not measure progress toward certification.
