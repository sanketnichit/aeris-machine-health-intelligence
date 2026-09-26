# Dataset Decision

## Why AI4I 2020 for v1?

AI4I is intentionally used as a controlled benchmark for the first AERIS release.

### Strengths

- 10,000 observations.
- Clear failure target.
- Multiple process/sensor variables.
- Multiple named failure mechanisms.
- Severe class imbalance that makes precision/recall/PR-AUC meaningful.
- Small enough to build and audit thoroughly.

### Important limitation

AI4I 2020 is **synthetic**, not proprietary or production telemetry. UCI explicitly describes it as synthetic data intended to reflect industrial predictive-maintenance data.

### Why not C-MAPSS yet?

C-MAPSS is a stronger benchmark for temporal degradation and remaining-useful-life research, but it requires sequence-oriented modelling and more careful RUL evaluation. It is kept as a planned extension rather than forcing it into the deadline-driven v1.

### Why not a real industrial dataset yet?

Real predictive-maintenance datasets can be substantially larger and more temporally complex. For example, UCI's MetroPT-3 dataset contains 1,516,948 observations from a metro train compressor APU and was collected specifically for predictive-maintenance/anomaly work. It is a strong future validation target, but not the right first dataset when the goal is to establish a clean, explainable pipeline quickly.

## Engineering principle

AERIS will make its dataset limitations explicit. The project does not present AI4I results as evidence about Red Bull Powertrains or any specific real-world machine fleet.
