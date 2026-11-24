"""Generate a standalone Markdown technical report from registered evidence."""
import argparse
import json
from pathlib import Path

from research.verify_evidence import ROOT, verify


def generate_report(root=ROOT):
    root=Path(root)
    records=verify(root)
    reports={r["file"]:json.loads((root/r["file"]).read_text(encoding="utf-8")) for r in records}
    official=reports["official_summary.json"]
    physical=reports["xjtu_summary.json"]
    gate=reports["xjtu_gate_summary.json"]
    review=reports["xjtu_reliability_summary.json"]
    independent=reports["pronostia_summary.json"]
    replay=reports["telemetry.json"]
    maintenance=reports["maintenance_summary.json"]
    physical_replay=reports["pronostia_replay.json"]
    lines=["# AERIS — Technical evidence report", "",
           "Research prototype | Simulated and accelerated laboratory benchmarks",
           "", "## Executive summary", "",
           f"- Official NASA test: {official['engines']} simulated engines.",
           f"- Physical bearing histories: {len(physical['snapshot_counts'])+len(independent['snapshot_counts'])}.",
           f"- Physical vibration recordings: {sum(physical['snapshot_counts'].values())+sum(independent['snapshot_counts'].values()):,}.",
           f"- Development telemetry: {sum(len(t['points']) for t in replay['traces'])} pre-failure observations.",
           f"- Physical feature replay: {sum(len(t['points']) for t in physical_replay['traces'])} displayed observations from {len(physical_replay['traces'])} previously evaluated bearings; subsampled for presentation.",
           "- AI4I generator rules outperform the learned classifier at its fixed threshold; see AI4I_FINDINGS.md.",
           "", "## Official NASA FD001", "",
           f"Frozen primary: {official['primary']}. Errors are simulated operating cycles.",
           "", "| Candidate | MAE | RMSE | NASA penalty |", "|---|---:|---:|---:|"]
    for name,m in official["metrics"].items():
        lines.append(f"| {name} | {m['mae']:.3f} | {m['rmse']:.3f} | {m['nasa_score']:.2f} |")
    lines.extend(["","## Physical XJTU-SY development","",
                  "Four retrospective endpoints per bearing. Errors are remaining recorded snapshots.",
                  "", "| Candidate | Bearing-disjoint MAE | Condition-disjoint MAE |","|---|---:|---:|"])
    for name,m in gate["summary"]["bearing"]["stage"]["all"].items():
        lines.append(f"| {name} | {m['mae']:.3f} | {gate['summary']['condition']['stage']['all'][name]['mae']:.3f} |")
    lines.extend(["","## Independent PRONOSTIA replication","",
                  f"Fit on {len(independent['fit_bearings'])} bearings; evaluate on {len(independent['evaluation_bearings'])}. Frozen primary: {independent['primary']}.",
                  "", "| Candidate | MAE | RMSE |","|---|---:|---:|"])
    for name,m in independent["summary"]["stage"]["all"].items():
        lines.append(f"| {name} | {m['mae']:.3f} | {m['rmse']:.3f} |")
    lines.extend(["","The adaptive advantage over learned forecasting did not replicate. Do not select a new primary using these observed evaluation outcomes.",
                  ""])
    calibration=reports["twin_calibration_summary.json"]
    summary=calibration["summary"]["all"]
    lines.extend(["","## Measured vibration-state transition audit","",
                  f"Six learning bearings supplied {calibration['fit']['transitions']} transitions. Eleven previously observed evaluation bearings supplied {summary['condition_drift']['endpoints']} endpoints.",
                  "", "| Predictor | MAE | RMSE |","|---|---:|---:|"])
    for name in ("persistence","global_drift","condition_drift"):
        m=summary[name]
        lines.append(f"| {name} | {m['mae']:.6f} | {m['rmse']:.6f} |")
    band=summary["condition_band"]
    lines.extend(["",f"Descriptive residual-band coverage {band['coverage']:.1%}; mean width {band['mean_width']:.6f} log-ratio units.",
                  "The small MAE difference does not establish superiority. This is not physical damage or virtual maintenance cost calibration.",
                  ""])
    sensitivity=reports["twin_sensitivity_summary.json"]
    lines.extend(["","## Virtual maintenance sensitivity","",
                  f"Frozen grid: {sensitivity['scenarios']} scenarios with {sensitivity['trials_per_scenario']} simulated trials each; {sensitivity['ties']} tied scenarios.",
                  "", "| Policy | Lowest mean cost (including ties) | Paired cost difference range |","|---|---:|---:|"])
    for name,m in sensitivity["summary"].items():
        lo,hi=m["paired_mean_cost_difference_range"]
        lines.append(f"| {name} | {m['lowest_mean_cost_including_ties']} | {lo:.3f} to {hi:.3f} |")
    lines.extend(["","Monte Carlo intervals quantify sampling error under this hypothetical model, not physical parameter uncertainty or field performance. No operational policy is selected.",
                  "", "## Reliability and uncertainty","",
                  "| Split | Assessments | Accepted |","|---|---:|---:|"])
    for split,ages in review["summary"].items():
        lines.append(f"| {split} | {sum(v['endpoints'] for v in ages.values())} | {sum(v['accepted'] for v in ages.values())} |")
    lines.extend(["","No forecasts were accepted by the evaluated policy; retained MAE is undefined. No finite 90% intervals were available. Coverage under condition shift is not guaranteed.",
                  "", "## Maintenance replay","",
                  "Hypothetical cost units only. Retrospective comparison, not a selected deployment policy.",
                  "", "| Failure cost | Lowest simulated cost | Candidate | Run-to-failure cost |","|---:|---:|---|---:|"])
    for ratio in ("5","10","25"):
        policy,cost=min(((p,v[ratio]["total_cost"]) for p,v in maintenance["summary"].items()),key=lambda x:x[1])
        baseline=maintenance["summary"]["run_to_failure:0"][ratio]["total_cost"]
        lines.append(f"| {ratio} | {cost:.2f} | {policy} | {baseline:.2f} |")
    lines.extend(["","## Limits and reproducibility","",
                  "The official NASA and independent PRONOSTIA evaluation populations are now observed. No field safety, state-of-the-art status, operational policy or realized savings is established. Raw errors across physical datasets are not directly comparable because recording cadence differs. Retrospective lifetime stages are not observable deployment signals.",
                  "", "## Registered evidence","",
                  "Content hashes establish consistency with the manifest, not scientific validity.",
                  "", "| Evidence | Revision | Execution | Blob fingerprint |","|---|---|---|---|"])
    for r in records:
        lines.append(f"| {r['file']} | `{r['revision']}` | [Run]({r['run_url']}) | `{r['blob_sha']}` |")
    return "\n".join(lines)+"\n"


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    content=generate_report()
    if args.output:
        args.output.write_text(content,encoding="utf-8")
    else:
        print(content,end="")
