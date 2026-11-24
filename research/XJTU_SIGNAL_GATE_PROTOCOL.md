# XJTU-SY observable vibration gate — exploratory development

Motivation: the completed [bearing audit](XJTU_FINDINGS.md) showed weak early-life learning and improved late-life estimates. Its stages are retrospective and cannot be used to switch a deployed model.

For each bearing, define a reference per channel from its first five RMS observations. Before five observations exist, retain the age-conditioned reference. Subsequently, compare the trailing five-observation median RMS with that reference and take the maximum channel ratio, floored at one. Neither reference nor gate uses future observations. A very small reference RMS is floored at 1e-12; the ratio remains a heuristic, not a probability or calibrated health score.

Fixed exploratory comparisons: statistical age reference, unchanged learned vibration model, hard switches at 2x and 4x reference RMS, linear interpolation from 2x to 4x. Thresholds are chosen heuristically, not fit or selected on held-out outcomes. The learned model retains the prior feature set and equal-bearing sample weights.

Evaluate each candidate in the original bearing-disjoint and condition-disjoint splits at the four retrospective stages, and independently at fixed observable landmarks 20, 50, 100, 200, 500 and 1000 snapshots, excluding the final recorded observation at landmarks. Report surviving asset count and gate activation fraction. Do not pool different landmarks as independent observations. No threshold or deployment policy will be selected on these exploratory results.

Use the same fingerprint-verified mirror as the original experiment. The existing physical development population has been observed; no independent confirmation or safety claim follows. The gate is not a failure detector; changes in RMS can reflect load, measurement conditions or other effects. Additional physical assets are needed for confirmation.
