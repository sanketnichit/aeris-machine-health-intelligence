# AERIS — Technical Interview Walkthrough

This is the factual talk track for recruiter screens and technical interviews.

## 60-second version

> AERIS is an explainable predictive-maintenance prototype built on the UCI AI4I 2020 benchmark. I deliberately scoped it to three things: machine-failure detection, calibrated failure-risk scoring, and explanation of the model output.
>
> The benchmark is imbalanced, with 3.39% positive failure labels, so I used PR-AUC as the primary metric instead of accuracy. I compared model families, engineered temperature delta and mechanical power from observed signals, and excluded target-side failure flags from binary prediction.
>
> The final model is HistGradientBoosting with sigmoid calibration. On the held-out seed-42 test set it reaches 0.899 PR-AUC, 0.965 precision, 0.809 recall and 0.880 F1 at a 0.50 threshold, with a Brier score of 0.0075.
>
> I also added bootstrap uncertainty, split sensitivity, calibration checks, error analysis, feature-stability analysis and SHAP/permutation explanations. The main caveat is that AI4I is synthetic, so these are benchmark results rather than evidence of production maintenance performance.

## 2-minute version

AERIS starts with six observed operating variables: product type, air temperature, process temperature, rotational speed, torque and tool wear.

Two deterministic features are then derived: temperature delta = process temperature minus air temperature, and mechanical power = torque times rotational speed divided by 9549.2966.

UDI, Product ID and the TWF/HDF/PWF/OSF/RNF failure flags are excluded from binary prediction because the failure flags are target-side information and would create unrealistic leakage.

The primary evaluation uses one stratified 80/20 seed-42 holdout. Model selection uses 5-fold stratified cross-validation on the training partition; the held-out test partition is kept for the headline result.

The controlled feature ablation increased mean CV PR-AUC from 0.8026 to 0.8713 and held-out PR-AUC from 0.8490 to 0.8986. Recall increased from 0.7353 to 0.8088, while Brier score improved from 0.0108 to 0.0075.

The final risk layer uses HistGradientBoosting followed by sigmoid calibration. The console uses the same canonical model builders as the offline pipeline, so it does not maintain a separate UI-only model definition.

## Core questions and answers

### Why PR-AUC instead of accuracy?

The positive class is rare: only 3.39% of rows are failures. Accuracy can therefore hide poor minority-class detection. PR-AUC directly reflects the precision/recall trade-off for the positive class.

### Why not use the failure-mode flags as inputs?

They are target-side information. Feeding TWF/HDF/PWF/OSF/RNF into the binary detector would make the task unrealistically easy and introduce target leakage.

### Why HistGradientBoosting?

It was carried forward from the training-partition comparison because Random Forest was nearly tied on cross-validated PR-AUC while HGB had higher cross-validated recall and F1. The held-out test set was kept for final comparison rather than model selection.

### Why calibrate the model?

A raw classifier score is not automatically a useful probability-like risk estimate. Calibration maps the model output onto a more useful risk scale. AERIS uses sigmoid calibration and reports Brier score alongside classification metrics.

### Why sigmoid rather than isotonic calibration?

Isotonic was slightly lower on Brier score in the calibration audit, but sigmoid was retained because it is a simpler, less flexible mapping for this small-positive-class benchmark.

### Why not optimize the threshold for maximum recall?

The threshold is an operational decision. Lower thresholds catch more positives but create more false alarms; higher thresholds reduce false alarms but can miss more failures. AERIS reports threshold trade-offs separately instead of silently tuning the headline test result.

### Does the feature gain prove causality?

No. It shows that those feature representations provide more predictive signal on this benchmark. The dataset is synthetic, and correlated features can share information. AERIS treats importance as model behavior, not physical causal proof.

### Why AI4I instead of C-MAPSS?

AERIS v1 is about establishing an auditable detection-to-risk-to-explanation workflow. C-MAPSS is better suited to temporal degradation and RUL, but it would substantially expand the sequence-modeling problem. C-MAPSS/RUL is therefore future work.

### Why is the synthetic-data caveat important?

Benchmark performance does not automatically transfer to a real machine fleet. Real deployment would require representative telemetry, temporal validation, drift checks, sensor-quality handling, prospective evaluation and operational threshold setting.

### What does the error analysis show?

At the 0.50 threshold there are 13 false negatives and 2 false positives on the seed-42 test set. The false negatives are heavily represented by TWF labels. That is a descriptive benchmark observation, not hidden threshold-tuning evidence.

### Why are some failure modes deferred?

HDF, PWF and OSF show enough benchmark signal to expose separately. TWF and RNF remain deferred because their benchmark classification signal is weak or unstable. AERIS does not force a mutually exclusive diagnosis because source labels can overlap.

### Why use both permutation importance and SHAP?

Permutation importance measures the model-performance impact of disrupting a feature across evaluation data. SHAP provides local model attribution for individual predictions. Neither proves physical root cause.

### How did you check robustness?

Three thousand bootstrap replicates quantify uncertainty around the main test metrics. Five fixed-model stratified splits measure sensitivity to the test partition. Additional audits examine calibration, held-out errors and feature-importance stability. These are downstream robustness checks, not hidden tuning loops.

### How do you avoid train/test leakage?

The primary test split is held out before model selection. Cross-validation is performed inside the training data, calibration is fitted from training data, and the test partition is used once for the primary held-out result. Engineered features use observed inputs only.

### What would you build next?

The highest-value next step is validation on real industrial time-series data. After that, a temporal degradation/RUL extension such as C-MAPSS could test transfer beyond static benchmark classification. Streaming, deployment monitoring and counterfactual analysis remain later-stage work.

## Numbers to memorise

| Item | Value |
|---|---:|
| Positive failure rate | 3.39% |
| Primary held-out PR-AUC | 0.8986 |
| Precision at 0.50 | 0.9649 |
| Recall at 0.50 | 0.8088 |
| F1 at 0.50 | 0.8800 |
| Brier score | 0.0075 |
| CV PR-AUC, raw features | 0.8026 ± 0.0376 |
| CV PR-AUC, raw + engineered | 0.8713 ± 0.0301 |
| Bootstrap replicates | 3,000 |
| Alternate fixed splits | 5 |
| Test errors at 0.50 | 13 FN, 2 FP |

## Claims to avoid

Do not describe AERIS as production-ready, real-time, a root-cause diagnosis system, validated on industrial machines, or trained on Red Bull/F1 telemetry. The defensible description is an auditable predictive-maintenance benchmark prototype with explicit synthetic-data limitations.