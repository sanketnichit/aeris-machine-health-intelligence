import numpy as np
import pytest

from research.twin_sensitivity import paired_summary, evaluate_scenario, audit
from src.digital_twin import Scenario, POLICIES


def test_paired_sampling_error():
    result=paired_summary([1,3,5],[2,2,2])
    assert result["mean"]==1
    assert result["monte_carlo_se"]==pytest.approx(2/np.sqrt(3))
    assert result["normal_95_low"]<1<result["normal_95_high"]
    assert result["fraction_cheaper"]==pytest.approx(1/3)


def test_scenario_accounting():
    config=Scenario(horizon=50,trials=20)
    row=evaluate_scenario(config)
    assert row==evaluate_scenario(config)
    assert set(row["metrics"])==set(POLICIES)
    assert row["metrics"]["reactive"]["paired_cost"]["monte_carlo_se"]==0
    for metrics in row["metrics"].values():
        assert metrics["downtime"]["mean"]+metrics["operated"]["mean"]==pytest.approx(config.horizon)
    assert row["lowest_mean_cost"]


def test_full_grid_and_ties():
    report=audit(trials=20)
    assert report["scenarios"]==len(report["results"])==54
    assert len({(r["scenario"]["load"],r["scenario"]["observation_noise"],
                 r["scenario"]["failure_cost"],r["scenario"]["wear_variability"])
                for r in report["results"]})==54
    assert sum(v["lowest_mean_cost_including_ties"] for v in report["summary"].values())>=54
