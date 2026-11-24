from dataclasses import replace
import numpy as np
import pytest

from src.digital_twin import Scenario, compare, innovations, simulate_policy, POLICIES


def test_reproducible_paired_scenarios():
    config=Scenario(horizon=100,trials=20)
    result=compare(config)
    assert result==compare(config)
    assert result["summary"]["reactive"]["paired_cost_difference"]["mean"]==0
    assert set(result["summary"])==set(POLICIES)
    wear,noise=innovations(config)
    for policy in POLICIES:
        run=simulate_policy(config,wear,noise,policy)
        assert np.all(run["operated"]+run["downtime"]==config.horizon)
        assert np.all(run["cost"]==run["planned"]*config.planned_cost+run["failures"]*config.failure_cost)


def test_deterministic_wear_and_downtime():
    config=Scenario(horizon=20,trials=20,wear_rate=.1,load=2,wear_variability=0,observation_noise=0,
                    failure_downtime=2,planned_downtime=1,service_age=2)
    wear,noise=innovations(config)
    reactive=simulate_policy(config,wear,noise,"reactive")
    assert np.all(reactive["failures"]==4)
    assert np.all(reactive["downtime"]==8)
    planned=simulate_policy(config,wear,noise,"age_based")
    assert np.all(planned["failures"]==0)
    assert np.all(planned["planned"]==6)
    assert np.all(planned["downtime"]==6)


def test_future_innovations_cannot_change_prefix():
    config=Scenario(horizon=40,trials=20)
    wear,noise=innovations(config)
    first=simulate_policy(config,wear,noise,"condition_based")
    wear[:,20:]*=10
    second=simulate_policy(config,wear,noise,"condition_based")
    assert first["trace"][:20]==second["trace"][:20]


@pytest.mark.parametrize("changes",[{"trials":0},{"horizon":1001},{"load":float("nan")},{"seed":-1}])
def test_invalid_scenarios(changes):
    with pytest.raises(ValueError):
        compare(replace(Scenario(),**changes))
