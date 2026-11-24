"""Synthetic virtual degradation sandbox. Not a calibrated physical digital twin."""
from dataclasses import dataclass, asdict
import math

import numpy as np

POLICIES=("reactive","age_based","condition_based")


@dataclass(frozen=True)
class Scenario:
    horizon: int = 200
    trials: int = 200
    seed: int = 42
    load: float = 1.0
    wear_rate: float = .012
    wear_variability: float = .35
    observation_noise: float = .06
    service_age: int = 60
    condition_threshold: float = .75
    planned_cost: float = 1.
    failure_cost: float = 10.
    planned_downtime: int = 3
    failure_downtime: int = 12

    def validate(self):
        for name,lo,hi in (("horizon",20,1000),("trials",20,2000),("seed",0,2**32-1),
                           ("service_age",1,1000),("planned_downtime",0,100),
                           ("failure_downtime",0,100)):
            v=getattr(self,name)
            if type(v) is not int or not lo<=v<=hi:
                raise ValueError(f"Invalid {name}")
        for name,lo,hi in (("load",.25,3),("wear_rate",.001,.1),("wear_variability",0,1),
                           ("observation_noise",0,.5),("condition_threshold",.1,.99),
                           ("planned_cost",0,1000),("failure_cost",0,10000)):
            v=getattr(self,name)
            if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:
                raise ValueError(f"Invalid {name}")


def innovations(scenario):
    rng=np.random.default_rng(scenario.seed)
    shape=(scenario.trials,scenario.horizon)
    return (rng.lognormal(-scenario.wear_variability**2/2,scenario.wear_variability,shape),
            rng.normal(0,scenario.observation_noise,shape))


def simulate_policy(scenario,wear,noise,policy):
    """Each calendar tick is either downtime, planned intervention or operation.

    Maintenance resets virtual damage to zero; interventions consume their
    configured downtime starting at the current tick. A failure consumes the
    operating tick and subsequent failure downtime. No future information used.
    """
    if policy not in POLICIES:
        raise ValueError("Unknown policy")
    n=scenario.trials
    damage=np.zeros(n)
    age=np.zeros(n,dtype=int)
    down=np.zeros(n,dtype=int)
    planned=np.zeros(n,dtype=int)
    failed=np.zeros(n,dtype=int)
    lost=np.zeros(n,dtype=int)
    operated=np.zeros(n,dtype=int)
    trace=[]
    for t in range(scenario.horizon):
        idle=down>0
        lost+=idle
        down=np.maximum(0,down-1)
        available=~idle
        observed=np.clip(damage+noise[:,t],0,1)
        service=available & ((age>=scenario.service_age) if policy=="age_based"
                             else (observed>=scenario.condition_threshold) if policy=="condition_based"
                             else np.zeros(n,dtype=bool))
        planned+=service
        damage[service]=0
        age[service]=0
        # Zero downtime allows operation in the same tick.
        stop=service & (scenario.planned_downtime>0)
        lost+=stop
        down[stop]=max(0,scenario.planned_downtime-1)
        operating=available & ~stop
        operated+=operating
        damage[operating]+=scenario.wear_rate*scenario.load**2*wear[operating,t]
        age[operating]+=1
        failure=operating & (damage>=1)
        failed+=failure
        trace.append({"tick":t+1,"damage":float(min(1,damage[0])),
                      "observed_before_operation":float(observed[0]),
                      "planned":bool(service[0]),"failure":bool(failure[0]),
                      "operated":bool(operating[0])})
        damage[failure]=0
        age[failure]=0
        down[failure]=scenario.failure_downtime
    cost=planned*scenario.planned_cost+failed*scenario.failure_cost
    return {"planned":planned,"failures":failed,"cost":cost,"downtime":lost,
            "operated":operated,"trace":trace}


def distribution(x):
    return {"mean":float(np.mean(x)), "p05":float(np.quantile(x,.05)),
            "median":float(np.quantile(x,.5)), "p95":float(np.quantile(x,.95))}


def compare(scenario=Scenario()):
    scenario.validate()
    wear,noise=innovations(scenario)
    results={p:simulate_policy(scenario,wear,noise,p) for p in POLICIES}
    reference=results["reactive"]
    summary={}
    for name,r in results.items():
        delta=r["cost"]-reference["cost"]
        summary[name]={**{k:distribution(r[k]) for k in ("cost","failures","planned","downtime","operated")},
                       "trial_failure_fraction":float(np.mean(r["failures"]>0)),
                       "paired_cost_difference":distribution(delta),
                       "fraction_cheaper_than_reactive":float(np.mean(delta<0))}
    return {"model_version":"synthetic-wear-v1","scenario":asdict(scenario),
            "summary":summary,"traces":{p:r["trace"] for p,r in results.items()},
            "scope":"Hypothetical stochastic wear model and simulated cost units. Quantiles are simulated outcome spread, not calibrated real-world prediction intervals. No asset linkage or operational policy selection."}
