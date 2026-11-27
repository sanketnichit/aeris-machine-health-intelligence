# Record-level evidence audit

Both original workflow ZIPs were downloaded and independently SHA-256 checked against their registered archive digests. The release package digest was also checked. JSON summaries agree after removal of full record-level fields. 120 unique MFPT scenarios × 17 recordings = 2,040 comparisons; 1,224/1,224 valid decompositions contain the reference. Counts agree. Paderborn: 68 unique recording identities and fingerprints, paired agreement 68/68, 9 shared accepted, 59 shared abstentions; specimen and condition breakdowns are reproduced. These checks do not reprocess raw waveform bytes.

Source assets:
- [Versioned release package](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45621480466/artifacts/15025206458) SHA-256 9ff2b1f242abf44130c74a805124be647a07061e7bf4a83e785537dbffaab9bd
- [MFPT full audit](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45613822665/artifacts/15020404150) SHA-256 300978a2e93ce9129920874afc8ccebdaae16f3953111d1207dfaa19063e422c
- [Paderborn full audit](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45619064703/artifacts/15022373895) SHA-256 5cad201a54c398e488dd5f2e054f35a67ec3d5daa920729582a15be70646e4c2

Re-run the standard-library checker with these three ZIPs in that order. Artifacts may expire; preserve authorized derived evidence before submission. The per-record breakdown is post hoc, not a new independent experiment. Figures are vector drafts with explicit denominators; journal-specific sizing and accessibility review remain.

The manuscript is a first full working draft, not submission-ready. Next: execute the committed checker in CI or local checkout, review full related work and reference metadata, expert review, author comprehension, verify figure/table provenance, and author-approved submission. 
