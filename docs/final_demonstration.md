# AERIS research demonstration and evaluation

## Demonstrate the contribution

Start the isolated local Compose stack using the quickstart. Populate the deterministic synthetic fleet with scripts/demo_fleet.py. The default research console requires no raw dataset downloads.

| Segment | Demonstrate | Explain |
|---|---|---|
| Research overview | Evidence map and linked results | Four benchmark datasets, distinct populations and targets; no pooled accuracy score. |
| Prognostics | Official NASA endpoint comparison and temporal replay | Primary MAE improvement, asymmetric penalty trade-off and causal feature construction. |
| Physical bearings | XJTU reliability, PRONOSTIA replication and measured replay | Why method transfer is difficult and why zero accepted forecasts is important evidence. |
| Fleet | Synthetic drift and missing-signal assets, advisory reasons and incident history | Transactional ingestion, explicit rule triggers and withheld unvalidated predictions. |
| Virtual laboratory | Vary workload and observation noise; compare maintenance policies | Shared seeded random innovations, hypothetical costs and model-form limitations. |
| Reproducibility | Download technical report; show fixed-revision acceptance and checksums | Evidence integrity and regression tests do not establish industrial certification. |

## Evaluation questions

- What is new? A reproducible multi-dataset research demonstrator combining comparative prognostics, explicit reliability checks, physical signal experiments, monitoring infrastructure and isolated maintenance simulation. No universal new best predictor is claimed.
- Why not report accuracy alone? Failure prevalence is low and remaining-life targets use different units. Precision, recall, MAE, asymmetric loss and uncertainty matter in different tasks.
- What failed? AI4I generator rules beat the classifier at a fixed threshold; physical adaptive superiority did not replicate; the XJTU selective policy accepted no forecasts. The measured state-transition improvement is small.
- Is the digital twin real? No. Virtual material wear is synthetic; the measured vibration-state audit does not identify physical wear or calibrate the maintenance simulator.
- Can it be deployed to control machinery? No. Field sensing, asset-specific calibration, prospective validation, production access control, independent safety review and operational engineering remain required.

## Completion boundary

A completed research release means that the documented scope is packaged and passes the fixed-revision acceptance checklist, including clean extraction, browser rendering, concurrent workloads and recovery. It does not mean that open scientific questions or industrial deployment are solved. See the scientific conclusions and release acceptance documents.
