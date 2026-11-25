# MFPT two-channel measurement fusion — findings

[Protocol](MFPT_MEASUREMENT_FUSION_PROTOCOL.md) | [Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45613057615) | [Evidence](evidence/mfpt_measurement_fusion_summary.json)

40 scenarios reuse 17 physical recordings (680 recording-scenario comparisons, including 560 fault and 120 normal assessments). All frozen primary-only aggregates reproduced. Second-channel indications are synthetic, not independent physical measurements.

| Secondary mode | Primary correct | Fused correct | Fused incorrect | Conflict assessments | Compatible but reference excluded | Accepted outside reference |
|---|---:|---:|---:|---:|---:|---:|
| Reference aligned | 30 | 112 | 0 | 34 | 0 | 0 |
| Small offset | 30 | 106 | 0 | 34 | 0 | 0 |
| Shared bias | 30 | 80 | 0 | 0 | 136 | 52 |
| Opposed bias | 30 | 50 | 0 | 102 | 34 | 22 |

Each mode includes 140 repeated fault assessments and 30 normal assessments. Overall, 348 correct fused suggestions versus 120 primary-only correct suggestions; no incorrect fused suggestions or normal false suggestions observed. Gross recovery 256, loss 28. Compatible intersections excluded the reference in 170 repeated assessments; 74 accepted suggestions were outside reference containment. Their observed correctness does not validate the underlying measurement intervals.

When both declared total bounds contained their injected errors, all 20 scenarios (340 repeated assessments) contained the reference in the intersection; 274 of 280 fault assessments were correctly accepted, with no incorrect accepted. This result is conditional on the modeled bounds and fixed dataset, not a field reliability estimate.

A second indication can recover substantial coverage under credible bounds. Shared bias can make both channels agree while excluding the true speed; interval agreement is not calibration. Neither the modeled secondary channel nor the nominal bias bounds constitute actual instrumentation evidence. Next, represent common-mode error explicitly and require externally supported calibration before any deployment claim.
