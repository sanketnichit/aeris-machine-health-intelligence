# Virtual degradation laboratory

This is a synthetic digital-twin **prototype**, not a calibrated twin of a physical machine. It does not read or write registered asset telemetry. Parameters are illustrative, not fitted to NASA, XJTU-SY, PRONOSTIA or field assets.

## Model

Each operating tick adds wear rate × relative load² × a positive lognormal innovation to latent damage. The innovation distribution has mean one. Independent Gaussian observation noise is added to current damage and clipped to [0,1]. Crossing latent damage one is a simulated failure. Replacement resets damage and operating age to zero.

Each calendar tick is either an operating tick or a downtime tick. Planned service consumes the configured downtime starting at that tick; zero planned downtime allows operation immediately. Failure occurs during operation, and subsequent ticks consume failure downtime. No costs beyond planned and failure interventions are modeled. Interventions are counted when initiated even near the horizon; downtime outside the horizon is not counted.

## Paired policies

- Reactive: operate until failure.
- Age-based: service after a specified count of operating ticks.
- Condition-based: service when the current noisy observation crosses a configured threshold.

Each policy sees the same seeded random innovations indexed by trial and calendar tick, not the future. This is a common-random-numbers comparison, not a physical causal estimate. Report mean costs, p05/median/p95, downtime, failures and paired cost differences against reactive. Quantiles summarize simulated outcomes, not confidence intervals on real equipment. The simulation failure fraction is not a calibrated failure probability.

## Reproduce

```python
from src.digital_twin import Scenario, compare
result = compare(Scenario(seed=42, trials=200, horizon=200))
print(result["summary"])
```

Or open Virtual degradation laboratory in the Streamlit sidebar. Adjust load, horizon, noise, service age, observed damage threshold and hypothetical failure cost. Download the complete scenario and result as JSON. The first-trial latent trajectory is shown for teaching, not used by the condition-based policy.

## Limits

No asset-specific identification, physics calibration, component interaction, repair uncertainty, prospective validation, real cost model or operational policy selection. No claim of savings or industrial safety is warranted. Selection against this simulated model may exploit its assumptions; use a different model and independent observations before making engineering claims.

## Frozen sensitivity evidence

The [sensitivity protocol](../research/TWIN_SENSITIVITY_PROTOCOL.md) and [findings](../research/TWIN_SENSITIVITY_FINDINGS.md) document 54 scenarios with 500 paired trials per scenario. The condition-based policy has the lowest simulated mean cost in 48 scenarios including ties. The measured vibration-state transition audit is reported separately in [calibration findings](../research/TWIN_CALIBRATION_FINDINGS.md). Neither experiment identifies the virtual wear model's parameters from physical equipment. Monte Carlo error is not model-form or field prediction uncertainty. The virtual laboratory displays both registered summaries separately from user-configured scenarios.
