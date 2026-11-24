# Research release acceptance

This checklist applies to a fixed candidate revision, not a moving branch. It defines completion of the research demonstrator, not industrial certification.

| Gate | Acceptance evidence |
|---|---|
| Evidence | All registered reports pass manifest verification; original numerical results and provenance retained. |
| Scientific scope | Scientific conclusions document contains favorable and unfavorable results, units, populations and explicit unsupported claims. |
| Regression | Entire pytest suite passes on the candidate revision. |
| Research UI | All nine research pages and virtual laboratory render in Chromium without application exceptions. |
| Fleet UI | Populated synthetic fleet renders; advisory, events, history and deviation views work; authenticated incident acknowledgement persists. |
| Reliability | Concurrent duplicate submissions, conflicting records, access checks, periodic worker, incident transitions and live backup/recovery pass in the disposable stack. |
| Packaging | SHA-256 checksums pass, clean extracted source runs tests with recorded environment, regenerated technical report matches exactly. |
| Documentation | README, quickstart, architecture, API, research synthesis, virtual laboratory and limitations agree with the candidate. |
| Publication | Successful acceptance workflow is reviewed, then the exact tested revision is tagged and the source/report artifact made available. |

A failed required check blocks publication; rerun against a new fixed revision after correcting the cause. Screenshots support visual inspection, not a guarantee of accessibility or usability. External user feedback, mobile-device testing and production security remain outside this local research release's certification scope.

The candidate's VERSION is metadata until acceptance and publication are confirmed. Never claim a stable tag merely because VERSION changed.
