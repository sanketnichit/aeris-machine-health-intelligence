# AI4I generator-rule audit

Source: https://doi.org/10.24432/C5HS5C

Run from repository root:

    python scripts/download_dataset.py
    python -m research.ai4i_rule_audit

This is a retrospective diagnostic on the existing seed-42 stratified 80/20 partition, not a new independent test. HDF, PWF and OSF rules are transcribed from the published generator description, not fitted to labels. Stochastic TWF and RNF are intentionally omitted. Inputs at rounded boundaries may disagree with source flags. Published generator rules are not validated safety thresholds.

Compare binary precision/recall/F1 and paired errors against calibrated HGB at 0.50. Average precision is reported only for the probabilistic model; the rule union is a binary operating point, not a ranking model. Individual mode agreement is separate from aggregate target agreement.

The experiment prints JSON containing data and split identifiers. Do not adjust thresholds using these test results. No empirical result is claimed until execution on the canonical dataset. If rule reconstruction matches or exceeds ML, report that finding rather than suppress it. External temporal validation remains necessary.
