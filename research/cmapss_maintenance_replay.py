"""Simulated maintenance policy evaluation on FD001 training histories.

One terminal outcome per engine and policy. Costs are hypothetical units,
not measured savings. Failure endpoints are never available for decisions.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

from research.cmapss_stage_audit import age_conditioned, relative_features
from research.cmapss_risk_audit import age_blend
from src.prognostics import load_trajectories, training_targets

THRESHOLDS = (10, 20, 40)
COST_RATIOS = (5, 10, 25)
CADENCE = 10
FIRST_CHECK = 20
LEAD = 5


def terminal_outcome(cycles, forecasts, failure_cycle, threshold, lead=LEAD):
    """First alert is terminal; maintenance can complete before failure only."""
    t = np.asarray(cycles, dtype=float)
    p = np.asarray(forecasts, dtype=float)
    if (t.ndim != 1 or t.shape != p.shape or not np.isfinite(t).all()
            or not np.isfinite(p).all() or (p < 0).any()
            or not np.isfinite(failure_cycle) or failure_cycle < 1
            or (t < 1).any() or (t >= failure_cycle).any()
            or (np.diff(t) <= 0).any()
            or not np.isfinite(threshold) or threshold < 0
            or not np.isfinite(lead) or lead < 0):
        raise ValueError("Invalid replay inputs")
    hits = np.flatnonzero(p <= threshold)
    if not len(hits):
        return dict(status="unplanned_failure", alert_cycle=None,
                    lead_cycles=None, unused_cycles=0.)
    alert = float(t[hits[0]])
    remaining = float(failure_cycle-alert)
    completed = remaining > lead
    return dict(status="planned_maintenance" if completed else "late_alert",
                alert_cycle=alert, lead_cycles=remaining,
                unused_cycles=remaining-lead if completed else 0.)


def summarize(outcomes, failure_cost, planned_cost=1., unused_cycle_cost=.01):
    if not outcomes or not all(np.isfinite(v) and v >= 0 for v in
                               (failure_cost, planned_cost, unused_cycle_cost)):
        raise ValueError("Invalid cost scenario")
    planned = [o for o in outcomes if o["status"] == "planned_maintenance"]
    failed = len(outcomes)-len(planned)
    unused = sum(o["unused_cycles"] for o in planned)
    return dict(engines=len(outcomes), planned=len(planned),
                late_alerts=sum(o["status"] == "late_alert" for o in outcomes),
                no_alerts=sum(o["status"] == "unplanned_failure" for o in outcomes),
                mean_unused_cycles=float(unused/len(planned)) if planned else None,
                mean_alert_lead=float(np.mean([o["lead_cycles"] for o in planned])) if planned else None,
                total_cost=float(len(planned)*planned_cost+failed*failure_cost+unused*unused_cycle_cost))


def run(data_dir):
    path = Path(data_dir)/"train_FD001.txt"
    frame = load_trajectories(path)
    x, y = relative_features(frame), training_targets(frame)
    records = []
    for fold,(fit,ev) in enumerate(GroupKFold(5).split(x,y,frame.unit)):
        life = frame.iloc[fit].groupby("unit").cycle.max().to_numpy()
        models = {
            "mean":HistGradientBoostingRegressor(max_iter=150,random_state=42,early_stopping=False),
            "q25":HistGradientBoostingRegressor(loss="quantile",quantile=.25,max_iter=150,
                                                random_state=42,early_stopping=False)}
        for model in models.values():
            model.fit(x.iloc[fit],y.iloc[fit])
        for unit,group in frame.iloc[ev].groupby("unit",sort=True):
            failure = int(group.cycle.max())
            check = group.loc[(group.cycle >= FIRST_CHECK) &
                              ((group.cycle-FIRST_CHECK)%CADENCE == 0) &
                              (group.cycle < failure)]
            ages = check.cycle.to_numpy()
            if len(check):
                mean = np.maximum(0,models["mean"].predict(x.loc[check.index]))
                q25 = np.maximum(0,models["q25"].predict(x.loc[check.index]))
                ref = age_conditioned(life,ages)
            else:
                mean = q25 = ref = np.array([])
            forecasts = {"age_reference":ref,"learned_mean":mean,
                         "adaptive_mean":age_blend(ages,ref,mean),"learned_q25":q25}
            for name,pred in forecasts.items():
                for threshold in THRESHOLDS:
                    records.append(dict(unit=int(unit),fold=fold,model=name,threshold=threshold,
                                        **terminal_outcome(ages,pred,failure,threshold)))
            records.append(dict(unit=int(unit),fold=fold,model="run_to_failure",threshold=0,
                                **terminal_outcome([],[],failure,0)))
    table = pd.DataFrame(records)
    summary = {}
    for (name,threshold),group in table.groupby(["model","threshold"]):
        outcomes = group.to_dict("records")
        summary[f"{name}:{threshold}"] = {
            str(ratio):summarize(outcomes,ratio) for ratio in COST_RATIOS}
    return dict(train_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                cadence=CADENCE,first_check=FIRST_CHECK,lead=LEAD,
                planned_cost=1.,unused_cycle_cost=.01,failure_costs=list(COST_RATIOS),
                summary=summary,outcomes=records,
                scope="Retrospective simulated decisions; hypothetical costs and perfect maintenance assumption. No official test labels, operational safety claim or selected policy.")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-dir",type=Path,required=True)
    print(json.dumps(run(parser.parse_args().data_dir),indent=2,allow_nan=False))
