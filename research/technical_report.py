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
    if "cwru_spectral_summary.json" in reports:
        cwru = reports["cwru_spectral_summary.json"]
        lines.extend(["", "## CWRU measured spectral audit (post-v0.1.0)", "",
                      f"Envelope improves expected-order power fraction in {cwru['envelope_improves_expected_count']}/{cwru['record_count']} recordings.",
                      "", "| Recording | Defect | Load (HP) | Raw FFT (%) | Envelope (%) |",
                      "|---|---|---:|---:|---:|"])
        for row in cwru["records"]:
            fault = row["fault"]
            raw = 100 * row["median_fractions"]["raw"][fault]
            env = 100 * row["median_fractions"]["envelope"][fault]
            lines.append(f"| {row['file_id']} | {fault} | {row['load_hp']} | {raw:.5f} | {env:.4f} |")
        counts = cwru["expected_exceeds_alternative_count"]
        lines.extend(["", f"Expected-order fraction exceeds alternative: raw {counts['raw']}/{cwru['record_count']}, envelope {counts['envelope']}/{cwru['record_count']}.",
                      "Representation-specific non-DC power fractions; correlated seeded-fault recordings without normal controls. Not classification accuracy, RUL or field validation.", ""])
    if "cwru_extension_summary.json" in reports:
        extension = reports["cwru_extension_summary.json"]
        raw, env = (extension["representations"][m] for m in ("raw", "envelope"))
        lines.extend(["", "## CWRU diagnostic extension (post-v0.1.0)", "",
                      f"Expected order ranks first: raw {raw['expected_first_count']}/{extension['fault_records']}; envelope {env['expected_first_count']}/{extension['fault_records']}.",
                      f"Descriptive normal/fault pairwise AUC: raw {raw['normal_fault_pairwise_auc']:.2f}, envelope {env['normal_fault_pairwise_auc']:.2f}.",
                      "", "| Fault group | Raw expected first | Envelope expected first |", "|---|---:|---:|"])
        for group, metrics in env["by_group"].items():
            lines.append(f"| {group} | {raw['by_group'][group]['expected_first']}/{metrics['records']} | {metrics['expected_first']}/{metrics['records']} |")
        lines.extend(["", "No threshold selected. Small rolling-element defects fail all four envelope rankings. Correlated same-rig recordings and differing acquisition rates constrain interpretation; no diagnostic accuracy or field validation claim.", ""])
    if "cwru_selective_summary.json" in reports:
        selective = reports["cwru_selective_summary.json"]
        e = selective["evaluation"]
        lines.extend(["", "## CWRU selective diagnosis (post-v0.1.0)", "",
                      f"Development-selected margin threshold {selective['policy']['margin_threshold']:.2f}; evaluation coverage {e['coverage']:.0%}.",
                      f"Accepted {e['accepted']}/{e['records']}, incorrect accepted {e['incorrect_accepted']}, withheld {e['abstained']}; forced ranking errors {e['forced_errors']}.",
                      "All four rolling-element cases remain unresolved. Zero observed retained errors does not establish zero risk. Same-rig severity transfer, no held-out normal controls or operational calibration.", ""])
    if "mfpt_transfer_summary.json" in reports:
        mfpt = reports["mfpt_transfer_summary.json"]
        e = mfpt["fault_assessment"]
        lines.extend(["", "## Independent MFPT transfer (post-v0.1.0)", "",
                      f"Frozen CWRU thresholds: floor {mfpt['score_floor']:.6f}, margin {mfpt['margin_threshold']:.2f}.",
                      f"Fault recordings: {e['accepted']}/{e['records']} accepted, {e['incorrect_accepted']} incorrect accepted; forced errors {e['forced_errors']}.",
                      f"Normal controls receiving a fault suggestion: {mfpt['normal_incorrect_accepted']}/{len(mfpt['normal_assessment'])}.",
                      "Positive selected laboratory cross-rig transfer, not a healthy-state diagnosis or field validation. No rolling-element controls; repeated loads may share physical hardware.",
                      mfpt["data_attribution"], ""])
    if "mfpt_robustness_summary.json" in reports:
        robustness = reports["mfpt_robustness_summary.json"]
        lines.extend(["", "## MFPT sensor robustness (post-v0.1.0)", "",
                      f"{robustness['record_scenario_count']} repeated recording-scenario assessments; {robustness['window_scenario_count']} window-scenario evaluations.",
                      "", "| Scenario | Correct accepted | Incorrect accepted | Withheld | Correct after gate |", "|---|---:|---:|---:|---:|"])
        for s in robustness["scenarios"]:
            a, b = s["ungated"], s["gated"]
            lines.append(f"| {s['kind']} {s['value']:g} | {a['correct_accepted']} | {a['incorrect_accepted']} | {a['abstained']} | {b['correct_accepted']} |")
        lines.extend(["", "Speed metadata error produced 5/9 incorrect accepted suggestions at -5% and 1/1 at +5%. No safe tolerance established.",
                      "The explicit quality gate removed 50 correct suggestions and prevented zero observed incorrect suggestions. Artificial repeated perturbations, not independent hardware validation.",
                      robustness["data_attribution"], ""])
    if "mfpt_order_uncertainty_summary.json" in reports:
        order = reports["mfpt_order_uncertainty_summary.json"]
        lines.extend(["", "## MFPT continuous order uncertainty (post-v0.1.0)", "",
                      f"{order['record_scenario_count']} repeated recording-scenario comparisons.",
                      "", "| Speed error | Declared uncertainty | Reference in interval | Point correct | Point incorrect | Guard correct | Guard incorrect |", "|---|---|---|---:|---:|---:|---:|"])
        for s in order["scenarios"]:
            a, b = s["point"], s["interval"]
            lines.append(f"| {s['declared_speed_error']:+.0%} | {s['declared_uncertainty']:.0%} | {s['reference_in_interval']} | {a['correct_accepted']} | {a['incorrect_accepted']} | {b['correct_accepted']} | {b['incorrect_accepted']} |")
        lines.extend(["", "Both uncertainty guards withheld all six incorrect point suggestions in each repeated grid. The narrow guard retains 27 correct suggestions; the wide guard retains none, so its retained error is undefined.",
                      "The narrow interval excludes the reference at ±5% actual error; no stability guarantee outside declared bounds. Retrospective sensitivity only, not independent validation.",
                      order["data_attribution"], ""])
    if "mfpt_breakpoint_summary.json" in reports:
        audit = reports["mfpt_breakpoint_summary.json"]
        rows = audit["scenarios"]
        lines.extend(["", "## MFPT closed-cell stability refinement", "",
                      f"Recovered {sum(s['recovered_correct'] for s in rows)} correct suggestions across {audit['record_scenario_count']} repeated assessments.",
                      f"New incorrect suggestions: {sum(s['new_incorrect'] for s in rows)}. A sufficient floating-point stability check, not exact interval arithmetic.", ""])
    if "mfpt_counterexample_summary.json" in reports:
        audit = reports["mfpt_counterexample_summary.json"]
        lines.extend(["", "## MFPT decision counterexamples", "",
                      f"{sum(s['point_evaluations'] for s in audit['scenarios'])} point evaluations.",
                      "| Nominal outcome | Abstention witness | Competing suggestion witness |", "|---|---:|---:|"])
        for group in ("nominal_correct", "nominal_incorrect"):
            counts = [s["counterexample_counts"][group] for s in audit["scenarios"]]
            lines.append(f"| {group} | {sum(c.get('abstention',0) for c in counts)} | {sum(c.get('competing_suggestion',0) for c in counts)} |")
        lines.extend(["", "First witnesses only; absence of a witness is not proof of invariance.", ""])
    if "mfpt_possibility_summary.json" in reports:
        audit = reports["mfpt_possibility_summary.json"]
        rows = audit["scenarios"]
        contained = [s for s in rows if s["reference_in_interval"]]
        lines.extend(["", "## MFPT diagnostic possibility sets", "",
                      f"Fault truth membership with reference containment: {sum(s['fault_truth_in_outer_set'] for s in contained)}/{sum(s['fault_records'] for s in contained)} repeated fault assessments.",
                      f"Outer-set narrowing in {sum(s['global_to_cell_shrunk'] for s in rows)}/{audit['record_scenario_count']} assessments.",
                      "A singleton is not a stable diagnosis; an empty set does not establish health. These are not probabilities or exact attainable sets.", ""])
    if "mfpt_measurement_width_summary.json" in reports:
        audit = reports["mfpt_measurement_width_summary.json"]
        lines.extend(["", "## MFPT measurement width and bias", "",
                      f"{audit['record_scenario_count']} repeated recording-scenario assessments.",
                      "| Reference contained | Fault assessments | Correct accepted | Incorrect accepted |", "|---|---:|---:|---:|"])
        for contained in (True, False):
            rows = [s["refined"] for s in audit["scenarios"] if s["reference_in_interval"] == contained]
            lines.append(f"| {contained} | {sum(s['fault_records'] for s in rows)} | {sum(s['correct_accepted'] for s in rows)} | {sum(s['incorrect_accepted'] for s in rows)} |")
        lines.extend(["", "Reducing declared uncertainty does not correct actual bias. No hardware accuracy requirement is established.", ""])
    if "mfpt_bias_budget_summary.json" in reports:
        audit = reports["mfpt_bias_budget_summary.json"]
        lines.extend(["", "## MFPT systematic-bias budget", "",
                      f"{audit['record_scenario_count']} repeated recording-scenario assessments.",
                      "| Assumed bias bound | Correct accepted | Incorrect accepted | Withheld |", "|---|---:|---:|---:|"])
        for bound in sorted({s["assumed_bias_bound"] for s in audit["scenarios"]}):
            rows = [s["composed"] for s in audit["scenarios"] if s["assumed_bias_bound"] == bound]
            lines.append(f"| {bound:.0%} | {sum(s['correct_accepted'] for s in rows)} | {sum(s['incorrect_accepted'] for s in rows)} | {sum(s['abstained'] for s in rows)} |")
        lines.extend(["", "Externally declared bounds are not sensor calibration. The same 17 physical recordings recur across synthetic metadata perturbations; these studies are not independent population validation.", ""])
    if "mfpt_measurement_fusion_summary.json" in reports:
        audit = reports["mfpt_measurement_fusion_summary.json"]
        lines.extend(["", "## MFPT two-channel measurement fusion", "",
                      f"{audit['record_scenario_count']} repeated recording-scenario comparisons.",
                      "| Secondary mode | Primary correct | Fused correct | Fused incorrect | Accepted outside reference |", "|---|---:|---:|---:|---:|"])
        for mode in sorted({s["secondary_mode"] for s in audit["scenarios"]}):
            rows = [s for s in audit["scenarios"] if s["secondary_mode"] == mode]
            lines.append(f"| {mode} | {sum(s['primary']['correct_accepted'] for s in rows)} | {sum(s['fused']['correct_accepted'] for s in rows)} | {sum(s['fused']['incorrect_accepted'] for s in rows)} | {sum(s['accepted_without_reference'] for s in rows)} |")
        lines.extend(["", "Compatible intervals can exclude the reference speed under shared bias. The second channel is simulated, not physically measured; agreement is not calibration.", ""])
    if "mfpt_common_mode_summary.json" in reports:
        audit = reports["mfpt_common_mode_summary.json"]
        lines.extend(["", "## MFPT common-mode measurement error", "",
                      f"{audit['record_scenario_count']} repeated recording-scenario assessments.",
                      "| Common bound | Correct accepted | Incorrect accepted | Compatible outside reference | Accepted outside reference |", "|---|---:|---:|---:|---:|"])
        for bound in audit["common_bounds"]:
            rows = [s for s in audit["scenarios"] if s["assumed_common_bound"] == bound]
            lines.append(f"| {bound:.0%} | {sum(s['common_guard']['correct_accepted'] for s in rows)} | {sum(s['common_guard']['incorrect_accepted'] for s in rows)} | {sum(s['nonempty_without_reference'] for s in rows)} | {sum(s['accepted_without_reference'] for s in rows)} |")
        lines.extend(["", "A shared-error bound requires independently established calibration. Repeated metadata perturbations are not independent field observations.", ""])
    if "cmapss_multiregime_summary.json" in reports:
        audit=reports["cmapss_multiregime_summary.json"]
        lines.extend(["","## NASA C-MAPSS multi-regime evaluation","",
                      f"{audit['unique_test_engines']} distinct official simulated endpoints, including {audit['new_subset_test_engines']} new subset endpoints; {audit['endpoint_evaluations']} scenario endpoint comparisons.",
                      "| Subset | Training mode | Test engines | Age MAE | Frozen primary MAE | Adaptive MAE | Primary NASA score |",
                      "|---|---|---:|---:|---:|---:|---:|"])
        for s in audit["scenarios"]:
            m=s["metrics"]
            lines.append(f"| {s['subset']} | {s['mode']} | {s['test_engines']} | {m['age_reference']['mae']:.3f} | {m[audit['primary']]['mae']:.3f} | {m['adaptive_mean']['mae']:.3f} | {m[audit['primary']]['nasa_score']:.3f} |")
        lines.extend(["","The primary candidate was frozen before the new official evaluation. No model was selected on the new test labels. These are simulated cycles; no hardware or field claims.",""])
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
