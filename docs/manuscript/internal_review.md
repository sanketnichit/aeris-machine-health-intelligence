# Internal critical review — revised draft v0.2

**Decision: major revision before submission.** This is an AI-assisted internal review, not external peer review or an acceptance decision.

| Reviewer concern | Response | Status |
|---|---|---|
| Shared error and selective diagnosis are established | Ragot (2022) already treats correlated bounded uncertainty; Siddique et al. and Zhao et al. (2026) address speed uncertainty and selective diagnosis. The paper explicitly limits its contribution to a retrospective case study. | Narrowed; novelty not established |
| Pseudoreplication | 17 MFPT recordings reused 120 times, 17 Paderborn specimens under four conditions. No iid intervals or significance tests. Added Wheat et al. (2024) and Vieira et al. (2026). | Addressed in text |
| Confusing containment failure and fault misclassification | Define coverage, retained fault error and healthy false-suggestion fraction separately. Reference exclusion is not a wrong label. | Addressed |
| Unpaired comparisons | Recomputed matched acceptance transitions: 205 both, 143 lost, 0 gained, 332 neither from 0 to 1%. All 74 zero-bound reference-excluding acceptances withheld at 1%. | Local artifact reaggregation passed |
| Model versus hardware | Paderborn timing hypotheses are not independent sensor indications; no verified clock, geometry or actual common error. No causal claim. | Addressed as limitation; physical validation absent |
| No matched external baseline | Zero-common guard is an internal comparator, not a comparison against recent methods. | Open scientific limitation |
| Figures and artifacts | Independently checked archive digests and per-record counts locally; added automated figure data assertions and artifact workflow. | Local check passed; workflow run pending |
| Citation metadata | Publisher pages confirm Ragot, Siddique et al., Zhao et al., original Paderborn DOI; added two evaluation studies. Existing foundational references checked at publisher/abstract level. | Full-text citation-chain review incomplete |
| Author and rights | Author must review and understand equations, verify references, confirm affiliation/declarations/permissions, and seek independent expert feedback. | Open |

Sources: https://www.oaepublish.com/articles/ces.2022.13 ; https://www.mdpi.com/2075-1702/14/10/1140 ; https://www.mdpi.com/2227-9717/14/20/3325 ; https://jmlr.csail.mit.edu/papers/v11/el-yaniv10a.html ; https://doi.org/10.36001/phme.2016.v3i1.1577 ; https://doi.org/10.1109/ACCESS.2024.3497716 ; https://doi.org/10.1016/j.ymssp.2026.114640 . Tacholess envelope order analysis (2013), https://pmc.ncbi.nlm.nih.gov/articles/PMC3812632/, is an additional relevant method requiring further comparison; fixed-spectrum metadata perturbations are not variable-speed order tracking. No systematic novelty clearance is claimed.

No new waveform experiments, thresholds, or release changes. Local independent audit reaggregated the three downloaded ZIPs and matched all tested summaries, specimen/condition totals and per-record counts; it was not execution of the exact GitHub checker. A dedicated workflow will run the revised committed checker and independent projection script on the exact artifacts.

Recommendation: seek a supervisor or bearing-diagnostics/metrology researcher for a substantive review before preprint or journal submission. Acceptance at a high-impact journal is not supported by the present evidence alone.
