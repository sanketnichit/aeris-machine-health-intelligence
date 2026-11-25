# Frozen NASA C-MAPSS multi-regime endpoint protocol

This post-v0.1.0 evaluation extends the frozen FD001 point-forecast procedure to official FD002, FD003 and FD004 endpoints. It is new simulated evaluation population, not a new simulator or independent physical validation.

The source is NASA's CMAPSSData.zip, pinned to SHA-256 74bef434a34db25c7bf72e668ea4cd52afe5f2cf8e44367c55a82bfd91a5a34f as recorded in the original FD001 execution (run 45427268184). Verify exact archive bytes, expected 12 explicitly named members and previously registered FD001 member hashes. Record all member fingerprints.

| Subset | Training engines | Official test engines | Operating conditions | Fault modes |
|---|---:|---:|---:|---:|
| FD001 | 100 | 100 | 1 | 1 |
| FD002 | 260 | 259 | 6 | 1 |
| FD003 | 100 | 100 | 1 | 2 |
| FD004 | 249 | 248 | 6 | 2 |

Use frozen relative HGB primary, snapshot HGB, constant, empirical age reference and fixed age blend, with unchanged features, seed 42, 150 iterations and no early stopping. Fit FD001 once and evaluate it without refitting on all four subsets. Also fit the same frozen candidate procedures separately on each new subset's complete training engines; no hyperparameter search or candidate selection. Generate every endpoint forecast before parsing official RUL labels. Unit IDs are local to subsets/splits; never join overlapping IDs across subsets.

Seven scenarios, 707 distinct official endpoint identities, including 607 new official endpoints and 1,314 model-scenario endpoint comparisons (the same new endpoints evaluated twice). Report each scenario separately: MAE, RMSE, NASA asymmetric score, signed error, over/underprediction beyond 20 cycles, paired primary-versus-age bootstrap and individual predictions. No aggregate across repeated modes as independent samples. FD001 historical MAEs must reproduce within 1e-6 cycles; a failed reproduction blocks this run rather than changing the original evidence. Results cannot be used to retune these official populations. No calibration, hardware or field claims. Freeze this protocol with the first workflow execution.
