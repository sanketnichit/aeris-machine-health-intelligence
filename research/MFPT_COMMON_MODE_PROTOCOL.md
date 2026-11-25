# Common-mode measurement reliability and calibration provenance

Research milestone, not a deployment safety case.

## Model and experiment

For two indications P and S, use P = R(1+c+e1), S = R(1+c+e2), where R is a common reference speed and all terms are relative to R. Bounds are |c| <= C, |e1| <= A, |e2| <= B. With t=R/P and q=S/P, the individual total bounds give t in [1/(1+A+C),1/(1-A-C)] intersected with [q/(1+B+C),q/(1-B-C)]. Eliminating the latent c further requires |q-1| <= (A+B)t. These conditions follow from pairwise intersection of three closed intervals for c. Numerical slack and outward rounding are precautions, not formal interval arithmetic. Missing C or conflicting measurements produce no suggestion.

Freeze the preceding 40 scenarios and repeat at common-mode bounds 0%, 1%, 5%. Use the same 17 fingerprint-verified MFPT recordings, frozen preprocessing and thresholds (120 scenarios, 2,040 repeated assessments). Decompose injected shared bias as common error in the shared-bias mode and zero otherwise. Reproduce the registered zero-common fusion outcomes. For every valid modeled decomposition assert reference containment; separately report invalid assumptions, conflicts, differential conflicts, nonempty false agreement, acceptance outside reference, correct and incorrect acceptance. No threshold selection, no independent observations or physical sensor measurements.

## Advisory contract

The provenance layer requires separate channel identifiers, same asset, reference and common-error group, UTC observation time within each declared validity interval, bounded individual and common errors and caller-pinned certificate bytes matching a SHA-256 digest. It refuses missing, expired, mismatched, duplicated or fingerprint-invalid inputs. A pinned digest only establishes byte identity: metadata values are not extracted from or authenticated by the certificate. Independent trusted enrollment must bind the metadata to actual calibration, check applicability to the operating regime, instrument configuration and time synchronization. This implementation is not an authorization service. Every result explicitly denies operational authorization. Advisory next actions are obtain applicable calibration evidence, reconcile conflict, obtain better reference measurement or review spectrum, or engineering review of a conditional suggestion.

## Physical validation acceptance plan

Before claiming field performance: collect synchronized tachometer and independent reference readings over the intended speed/load/temperature envelope; document shared timebase, mounting and geometry errors; establish traceable deterministic bounds and validity dates independently of fault labels; freeze the model and diagnostic thresholds; evaluate on previously unseen machines including healthy and ambiguous cases; report record-level and asset-level denominators, incorrect suggestions, abstentions, missing calibration and conflict behavior. Evaluate invalid/expired certificates and common-mode drift. Do not infer sensor accuracy from retrospective benchmark outcomes. No production API or machine-control path is changed.
