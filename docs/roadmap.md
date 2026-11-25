# AERIS research prototype roadmap

**Research release v0.2.0: completed (10/10 defined gates).** [GitHub](https://github.com/sanketnichit/aeris-machine-health-intelligence/releases/tag/v0.2.0) · [Zenodo DOI](https://doi.org/10.5281/zenodo.24533914) · [Closure checklist](next_research_release_closure.md). The v0.1.0 milestone and intermediate candidate history below are retained as historical context. No additional research is required for v0.2.0.

**Research release v0.1.0: completed (100% of the defined release acceptance scope).**

[Published release](https://github.com/sanketnichit/aeris-machine-health-intelligence/releases/tag/v0.1.0) · [Successful acceptance and publication](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45453539267)

The release tag points to commit `99e9da8f8f73b80cfabbc857a4b612bffff9341d`. All 180 tests passed in both the checkout and the clean extracted archive. Both acceptance jobs and publication passed. All five published asset SHA-256 digests match the downloaded accepted bundle. This roadmap update is a post-release documentation commit; the tagged source remains unchanged.

| Workstream | Release gate |
|---|---|
| Core ML research | Scientific conclusions frozen with favorable and negative results. |
| Validation and reproducibility | Ten registered evidence reports, clean extraction, deterministic report and regression checks passed. |
| Application and UX | Defined desktop Chromium research, virtual laboratory and populated fleet checks passed; authenticated review persisted. |
| Telemetry and monitoring | Bounded concurrent workload, periodic worker, incident review and live backup/recovery passed. |
| Twin and decision intelligence | Measured-state and synthetic sensitivity audits integrated; explicit forecast abstention and simulation limitations retained. |
| Packaging and documentation | Versioned source, report, checksums, revision and environment published and verified. |

The previous progress percentages (78%, 82%, 85%, 86%, 90%, 94%, 97%) were subjective planning estimates. Completion now refers to the explicit research release acceptance checklist, not scientific accuracy or total potential development.

## Follow-on work (separate scope)

- External user feedback, accessibility and mobile-device testing.
- A genuinely new independent evaluation population and prospective physical measurements.
- Asset-specific calibration and validation of degradation models.
- Production authorization, encrypted transport, performance and resilience engineering, and independent safety review.

The release does not establish prospective field performance, a calibrated physical twin, safe control, industrial security, or realized savings. Completion of this research demonstrator does not imply industrial deployment readiness.

## Post-release measurement reliability milestone

Completed research on fixed MFPT recordings identifies uncertainty-induced abstention, instability, false precision and false sensor agreement. The new common-mode model, pinned calibration enrollment, synthetic advisory lab and offline archived-capture advisory join this evidence to a testable decision-support path. See [protocol and physical validation acceptance plan](../research/MFPT_COMMON_MODE_PROTOCOL.md) and [offline workflow](capture_advisory.md). Completion of implementation is distinct from passing CI, finishing the new experiment, or meeting field validation requirements. At that historical milestone no new release was claimed.

## Next candidate acceptance

The frozen [NASA multi-regime protocol](../research/CMAPSS_MULTIREGIME_PROTOCOL.md) extends evaluation beyond FD001. A separate [non-publishing candidate gate](next_candidate_acceptance.md) covers the expanded application and integrated reliability stack. No release tag or DOI is changed.

The first post-release candidate [acceptance record](candidate_851f08901e5a.md) confirms the exact 851f08901e5a revision passed both jobs. New regime-development changes are a separate candidate.

The second [accepted candidate](candidate_45fd9e8413fc.md) covers the registered NASA regime-development results and passed 390 tests in both package environments. Paderborn timing and the offline verifier are later changes. The [frozen cohort](../research/PADERBORN_COHORT_PROTOCOL.md) will trigger a fresh acceptance campaign on evidence registration.

## Bounded next research release

See [closure checklist](next_research_release_closure.md) for the finite ten-gate scope, now complete. This is a gate-count planning indicator, not an effort estimate or industrial readiness score. Do not extend the completed release without a new explicit scope.
