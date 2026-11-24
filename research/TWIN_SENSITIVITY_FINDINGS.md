# Virtual maintenance sensitivity findings

[Execution](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/45451056286) · [Protocol](TWIN_SENSITIVITY_PROTOCOL.md) · [Registered summary](evidence/twin_sensitivity_summary.json)

The frozen factorial study ran all 54 scenarios with 500 trials each: 27,000 scenario-trials, each evaluated under three policies using paired innovations. All scenarios use the same seed, and comparisons across scenarios are dependent.

| Policy | Lowest mean cost (including ties) | Paired mean cost difference vs reactive (range) | Scenarios with entire approximate 95% MC interval below zero |
|---|---:|---:|---:|
| Reactive | 0 | 0 to 0 | 0 |
| Age-based | 9 | -47 to 0 | 36 |
| Condition-based | 48 | -94 to -2.954 | 54 |

Three scenarios tied. Condition-based has the lowest simulated mean cost in 45 scenarios outright and three tied; age-based in six outright and three tied. Mean downtime ranges: reactive 12–47.848, age-based 9–47.848, condition-based 3–21.756 virtual ticks.

These comparisons are conditional on the simplified simulator, its damage reset, specified service thresholds and hypothetical cost assumptions. The interval quantifies Monte Carlo sampling variability, not parameter uncertainty, real-world model error or field reliability. Cost ranking is not a deployment recommendation, and the simulated outcomes do not calibrate the physical bearing signal model.

Full scenario-level results and the environment are preserved in the workflow artifact twin-sensitivity-v1. The repository registers the compact execution summary.
