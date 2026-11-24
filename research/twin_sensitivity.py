"""Synthetic sensitivity study, not industrial maintenance optimization."""
import itertools
import json
from dataclasses import asdict
import math

import numpy as np

from src.digital_twin import Scenario, POLICIES, innovations, simulate_policy, distribution

LOADS=(.75,1.,1.5)
NOISE=(0.,.06,.15)
COSTS=(5.,10.,25.)
VARIABILITY=(.15,.35)


def paired_summary(cost,reference):
    delta=np.asarray(cost,dtype=float)-np.asarray(reference,dtype=float)
    mean=float(delta.mean())
    se=float(delta.std(ddof=1)/math.sqrt(len(delta)))
    return {"mean":mean,"monte_carlo_se":se,"normal_95_low":mean-1.96*se,
            "normal_95_high":mean+1.96*se,"fraction_cheaper":float((delta<0).mean())}


def evaluate_scenario(scenario):
    scenario.validate()
    wear,noise=innovations(scenario)
    results={p:simulate_policy(scenario,wear,noise,p) for p in POLICIES}
    reference=results["reactive"]["cost"]
    metrics={}
    for name,r in results.items():
        metrics[name]={k:distribution(r[k]) for k in ("cost","failures","downtime","operated")}
        metrics[name]["paired_cost"]=paired_summary(r["cost"],reference)
    minimum=min(v["cost"]["mean"] for v in metrics.values())
    winners=[p for p,v in metrics.items() if math.isclose(v["cost"]["mean"],minimum,rel_tol=0,abs_tol=1e-12)]
    return {"scenario":asdict(scenario),"metrics":metrics,"lowest_mean_cost":winners}


def audit(trials=500):
    rows=[evaluate_scenario(Scenario(trials=trials,load=load,observation_noise=noise,
                failure_cost=cost,wear_variability=variability))
          for load,noise,cost,variability in itertools.product(LOADS,NOISE,COSTS,VARIABILITY)]
    counts={p:sum(p in r["lowest_mean_cost"] for r in rows) for p in POLICIES}
    summary={}
    for p in POLICIES:
        values=[r["metrics"][p]["paired_cost"] for r in rows]
        summary[p]={"lowest_mean_cost_including_ties":counts[p],
                    "paired_mean_cost_difference_range":[min(v["mean"] for v in values),max(v["mean"] for v in values)],
                    "scenarios_entire_interval_below_zero":sum(v["normal_95_high"]<0 for v in values),
                    "scenarios_entire_interval_above_zero":sum(v["normal_95_low"]>0 for v in values),
                    "mean_downtime_range":[min(r["metrics"][p]["downtime"]["mean"] for r in rows),
                                           max(r["metrics"][p]["downtime"]["mean"] for r in rows)]}
    return {"protocol":"virtual-maintenance-sensitivity-v1","scenarios":len(rows),
            "trials_per_scenario":trials,"ties":sum(len(r["lowest_mean_cost"])>1 for r in rows),
            "summary":summary,"results":rows,
            "scope":"Synthetic sensitivity only; paired Monte Carlo intervals quantify numerical sampling error under the assumed model, not physical model uncertainty or real equipment outcomes."}


if __name__=="__main__":
    print(json.dumps(audit(),indent=2,allow_nan=False))
