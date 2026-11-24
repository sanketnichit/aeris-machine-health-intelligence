# Virtual maintenance sensitivity audit v1

This is a sensitivity study of the synthetic wear simulator, not a physical machine experiment or evidence of industrial savings.

Fixed factorial grid: relative load 0.75, 1.0, 1.5; observation noise 0, 0.06, 0.15; hypothetical failure cost 5, 10, 25; wear variability 0.15, 0.35. This gives 54 scenarios. Each uses 500 independent simulated trials, 200 calendar ticks, seed 42, wear rate 0.012, planned service age 60, condition trigger 0.75, planned cost 1, planned downtime 3 and failure downtime 12. Retain all scenarios, including unfavorable outcomes.

Use common random innovations indexed by trial and calendar tick for the three policies within each scenario. The same seed across scenarios induces dependence across scenarios; scenario counts are sensitivity summaries, not independent evidence. No tuning or policy selection based on the grid.

Report mean cost, failures, downtime and operating ticks, outcome p05/p95 for cost, and paired mean cost difference relative to reactive with Monte Carlo standard error (sample standard deviation divided by square root of trial count). Report paired 95% normal-approximation Monte Carlo intervals as numerical sampling uncertainty under the specified simulator, not real-world prediction or model uncertainty. Count each policy's lowest mean-cost scenarios, preserving ties; report cost/downtime trade-offs. Do not interpret an apparent winner as a recommended maintenance policy.

Model assumptions (damage accumulation, reset after intervention, load squared, hypothetical costs) remain uncalibrated. Real equipment may violate every assumption. No extrapolation to actual RUL, field safety or realized savings.
