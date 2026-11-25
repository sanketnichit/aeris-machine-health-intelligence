"""Read-only Streamlit research evidence; no model fitting or network requests."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from research.verify_evidence import verify

EVIDENCE = Path(__file__).resolve().parents[1] / "research" / "evidence"


def maintenance_table(report, ratio):
    rows = []
    for policy, scenarios in report["summary"].items():
        model, threshold = policy.split(":")
        row = scenarios[str(ratio)]
        rows.append({"Model": model, "Threshold": int(threshold),
                     "Planned": row["planned"], "Late": row["late_alerts"],
                     "Missed": row["no_alerts"], "Cost": row["total_cost"],
                     "Mean unused cycles": row["mean_unused_cycles"]})
    return pd.DataFrame(rows).sort_values(["Cost", "Model", "Threshold"]).reset_index(drop=True)


def bearing_comparison(report, split, detail="by_bearing"):
    if split not in ("bearing", "condition") or detail not in ("by_bearing", "by_stage"):
        raise ValueError("Unknown bearing comparison")
    rows = []
    for model in ("age_reference", "learned"):
        for group, metrics in report["summary"][split][model][detail].items():
            rows.append({"Group": group, "Model": model, "MAE": metrics["mae"],
                         "RMSE": metrics["rmse"], "Endpoints": metrics["endpoints"]})
    return pd.DataFrame(rows)


def read_report(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def render_overview():
    """Executive overview derived from registered evidence, not hardcoded metrics."""
    official = read_report("official_summary.json")
    xjtu = read_report("xjtu_summary.json")
    replication = read_report("pronostia_summary.json")
    gate = read_report("xjtu_gate_summary.json")
    review = read_report("xjtu_reliability_summary.json")
    telemetry = read_report("telemetry.json")
    st.subheader("Machine health research command center")
    st.caption("Explore the evidence, inspect uncertainty, and reproduce each experiment.")
    a, b, c, d = st.columns(4)
    a.metric("Official NASA engines", official["engines"])
    b.metric("Physical bearing histories", len(xjtu["snapshot_counts"])+len(replication["snapshot_counts"]))
    c.metric("Physical vibration recordings", f"{sum(xjtu['snapshot_counts'].values())+sum(replication['snapshot_counts'].values()):,}")
    d.metric("Replay observations", sum(len(t["points"]) for t in telemetry["traces"]))
    st.markdown("### What the evidence says")
    left, right = st.columns(2)
    with left:
        primary = official["primary"]
        baseline = official["metrics"]["age_reference"]["mae"]
        mae = official["metrics"][primary]["mae"]
        st.metric("Frozen NASA primary MAE", f"{mae:.2f} cycles", f"{(1-mae/baseline)*100:.1f}% lower than age reference", delta_color="normal")
        st.caption("Official simulated FD001 endpoints; the secondary adaptive model performed better.")
    with right:
        rows = gate["summary"]["bearing"]["stage"]["all"]
        base, adapted = rows["learned"]["mae"], rows["switch_2x"]["mae"]
        st.metric("XJTU development gate MAE", f"{adapted:.2f} snapshots", f"{(1-adapted/base)*100:.1f}% lower than learned")
        st.caption("Held-out bearing development endpoints; not independent confirmation.")
    st.warning("Independent replication: the frozen vibration gate did not outperform the learned comparator on PRONOSTIA.")
    accepted = sum(v["accepted"] for split in review["summary"].values() for v in split.values())
    total = sum(v["endpoints"] for split in review["summary"].values() for v in split.values())
    st.warning(f"Reliability limitation: {accepted}/{total} advisory forecasts accepted in the XJTU reliability audit.")
    st.markdown("### Research map")
    base = "https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/main/research/"
    for title, path, note in [
        ("AI4I classification","AI4I_FINDINGS.md","Synthetic generator rules outperform learned classification at the fixed threshold."),
        ("NASA official prognostics","FD001_OFFICIAL_FINDINGS.md","100 simulated test engines; frozen primary and comparators."),
        ("Uncertainty and maintenance","CMAPSS_RISK_FINDINGS.md","Development uncertainty, asymmetric risk and hypothetical costs."),
        ("Physical vibration validation","XJTU_FINDINGS.md","15 physical laboratory bearings; mixed baseline comparisons."),
        ("Adaptive reliability","XJTU_ADAPTIVE_FINDINGS.md","Observable switching and negative selective-forecasting result."),
        ("Independent replication","PRONOSTIA_FINDINGS.md","Separate laboratory platform; failed replication of adaptive superiority."),
    ]:
        st.markdown(f"**[{title}]({base+path})** — {note}")
    with st.expander("Evidence provenance"):
        records = verify(EVIDENCE)
        st.dataframe(pd.DataFrame(records), hide_index=True)
        st.caption("Git blob fingerprints verify registered content integrity, not scientific validity.")
    st.caption("Research prototype only. No production deployment, field safety or measured savings established.")


def render_maintenance():
    report = read_report("maintenance_summary.json")
    st.caption(report["scope"])
    ratio = st.select_slider("Hypothetical failure cost", options=[5, 10, 25], value=10)
    table = maintenance_table(report, ratio)
    st.caption(f"Planned cost: {report['planned_cost']} · Inspection cadence: {report['cadence']} cycles · Intervention lead: {report['lead']} cycles")
    st.bar_chart(table.assign(Policy=table.Model + ":" + table.Threshold.astype(str)).set_index("Policy")["Cost"])
    st.dataframe(table, hide_index=True)
    st.caption("Sorted retrospectively by cost; no operational policy has been selected.")
    st.markdown(f"[Execution evidence]({report['run_url']}) · revision `{report['revision']}`")
    st.download_button("Download maintenance evidence", json.dumps(report, indent=2), "maintenance_summary.json", "application/json")


def render_official():
    path = EVIDENCE / "official_summary.json"
    if not path.is_file():
        st.info("Official results are not yet published in this repository.")
    else:
        report = read_report("official_summary.json")
        st.caption(report["scope"])
        st.markdown(f"Primary candidate: **{report['primary']}** · {report['engines']} official endpoints")
        metrics = pd.DataFrame(report["metrics"]).T
        st.dataframe(metrics)
        st.markdown(f"[Execution evidence]({report['run_url']})")


def render_replay():
    st.subheader("Cycle-by-cycle engine replay")
    path = EVIDENCE / "telemetry.json"
    if not path.is_file():
        st.info("Verified development traces have not yet been published.")
        st.markdown("[Replay generation workflow](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/workflows/research-telemetry.yml)")
    else:
        report = read_report("telemetry.json")
        st.caption(report["scope"])
        traces = {t["unit"]: t for t in report["traces"]}
        unit = st.selectbox("Development engine", sorted(traces), key="replay_unit")
        trace = traces[unit]
        points = pd.DataFrame(trace["points"]).set_index("cycle")
        cycle = st.slider("Observed cycle", min_value=int(points.index.min()),
                          max_value=int(points.index.max()), key=f"replay_cycle_{unit}")
        threshold = st.slider("Illustrative alert threshold (cycles)", 5, 60, 20)
        history = points.loc[:cycle]
        current = history.iloc[-1]
        cols = st.columns(3)
        cols[0].metric("Personalized RUL", f"{current['relative_hgb']:.1f}")
        cols[1].metric("Adaptive RUL", f"{current['adaptive_mean']:.1f}")
        cols[2].metric("Age reference RUL", f"{current['age_reference']:.1f}")
        st.line_chart(history[["age_reference","relative_hgb","adaptive_mean"]])
        hits = history.loc[(history.index >= 20) & ((history.index-20)%10 == 0)
                           & (history.adaptive_mean <= threshold)]
        if hits.empty:
            st.info("No threshold crossing at scheduled checks so far.")
        else:
            st.warning(f"First simulated alert at cycle {hits.index[0]}. Engineering review only.")
        sensor = st.selectbox("Observed sensor", [c for c in history if c.startswith("sensor_")])
        st.line_chart(history[[sensor]])
        if st.checkbox("Reveal retrospective ground truth", key=f"replay_truth_{unit}"):
            st.metric("Actual remaining cycles", trace["failure_cycle"]-cycle)
            st.caption("Ground truth is available only retrospectively, not used by the alert policy.")
        st.caption(f"Evaluation fold {trace['fold']} · engine excluded from fitting")
        if "run_url" in report:
            st.markdown(f"[Execution evidence]({report['run_url']})")


def render_bearings():
    st.subheader("Physical vibration validation")
    st.caption("XJTU-SY accelerated laboratory bearing experiments; a distinct task from NASA engine forecasting.")
    st.markdown("[Physical validation protocol](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/main/research/XJTU_PROTOCOL.md)")
    path = EVIDENCE / "xjtu_summary.json"
    if not path.is_file():
        st.info("Physical-bearing results are not yet published. No empirical claim is made.")
        st.markdown("[Physical research workflow](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/workflows/research-xjtu.yml)")
    else:
        report = read_report("xjtu_summary.json")
        st.caption(report["scope"])
        cols = st.columns(2)
        cols[0].metric("Laboratory bearings", len(report["snapshot_counts"]))
        cols[1].metric("Vibration snapshots", sum(report["snapshot_counts"].values()))
        split = st.radio("Held-out population", ["bearing", "condition"],
                         format_func=lambda x: "Unseen bearing" if x == "bearing" else "Unseen operating condition",
                         key="bearing_split")
        metrics = pd.DataFrame({m: r["all"] for m,r in report["summary"][split].items()}).T
        st.dataframe(metrics)
        detail = st.radio("Comparison breakdown", ["by_bearing", "by_stage"], key="bearing_detail")
        table = bearing_comparison(report, split, detail)
        st.bar_chart(table, x="Group", y="MAE", color="Model", stack=False)
        st.dataframe(table, hide_index=True)
        st.caption("Errors are remaining recorded snapshots, not engine cycles. Stage selection is retrospective; endpoint is the last recording, not independently measured failure time.")
        st.markdown(f"[Execution evidence]({report['run_url']})")
        st.download_button("Download physical validation evidence", json.dumps(report, indent=2), "xjtu_summary.json", "application/json")


def render_reliability():
    st.subheader("Adaptive forecasting and reliability")
    gate = read_report("xjtu_gate_summary.json")
    review = read_report("xjtu_reliability_summary.json")
    st.warning("Exploratory development results; the evaluated review policy accepted no forecasts. No deployment policy has been selected.")
    split = st.radio("Evaluation population", ["bearing", "condition"], key="reliability_split")
    st.caption(gate["scope"])
    aggregate = pd.DataFrame(gate["summary"][split]["stage"]["all"]).T
    st.dataframe(aggregate)
    st.bar_chart(aggregate["mae"])
    ages = gate["summary"][split]["landmark"]["by_point"]
    landmark = pd.DataFrame([
        {"Age": int(age), "Bearings": values["bearings"],
         "2x activation": values["gate_2x_fraction"],
         **{model: metric["mae"] for model, metric in values["metrics"].items()}}
        for age, values in ages.items()
    ]).sort_values("Age").set_index("Age")
    st.markdown("**Observable landmarks**")
    st.dataframe(landmark)
    st.line_chart(landmark.drop(columns=["Bearings", "2x activation"]))
    st.caption("MAE in remaining recorded snapshots; survivor populations differ across landmarks.")
    results = pd.DataFrame(review["summary"][split]).T
    results.index = results.index.astype(int)
    results = results.sort_index()
    n = int(results["endpoints"].sum())
    accepted = int(results["accepted"].sum())
    a, b = st.columns(2)
    a.metric("Review assessments", n)
    b.metric("Accepted forecasts", accepted)
    if accepted == 0:
        st.error("No forecasts passed the configured review policy. Retained MAE is undefined.")
    st.caption(review["scope"])
    st.dataframe(results.drop(columns=["reason_counts"]))
    reasons = pd.DataFrame(results["reason_counts"].tolist(), index=results.index)
    st.bar_chart(reasons)
    st.caption("Review reasons can overlap. Coverage is evaluated only where finite intervals exist, and is not guaranteed under operating-condition shift.")
    st.markdown(f"[Signal gate run]({gate['run_url']}) · [Reliability run]({review['run_url']})")
    st.download_button("Download adaptive evidence", json.dumps(gate, indent=2), "xjtu_gate_summary.json", "application/json")
    st.download_button("Download reliability evidence", json.dumps(review, indent=2), "xjtu_reliability_summary.json", "application/json")


def render_replication():
    st.subheader("Independent physical method replication")
    report = read_report("pronostia_summary.json")
    st.caption(report["scope"])
    a,b,c = st.columns(3)
    a.metric("Learning bearings", len(report["fit_bearings"]))
    b.metric("Evaluation bearings", len(report["evaluation_bearings"]))
    c.metric("Validated recordings", sum(report["snapshot_counts"].values()))
    st.warning("The frozen 2x switch did not reproduce its XJTU advantage over the learned comparator. No replacement primary candidate is selected.")
    st.markdown(f"Frozen primary: **{report['primary']}**")
    stage = report["summary"]["stage"]
    aggregate = pd.DataFrame(stage["all"]).T
    st.dataframe(aggregate)
    st.bar_chart(aggregate["mae"])
    kind = st.radio("Replication breakdown", ["stage", "landmark"], key="replication_breakdown")
    points = report["summary"][kind]["by_point"]
    breakdown = pd.DataFrame([
        {"Point": float(point), "Bearings": values["bearings"],
         **{model: metric["mae"] for model,metric in values["metrics"].items()}}
        for point,values in points.items()
    ]).sort_values("Point").set_index("Point")
    st.dataframe(breakdown)
    st.line_chart(breakdown.drop(columns=["Bearings"]))
    st.caption("Remaining recorded snapshots; stages are retrospective, landmarks are observed ages. Do not compare raw errors across datasets with different recording cadence.")
    st.markdown(f"[Execution evidence]({report['run_url']}) · revision `{report['revision']}`")
    st.download_button("Download independent replication evidence", json.dumps(report, indent=2), "pronostia_summary.json", "application/json")


def render_physical_replay():
    st.subheader("Physical bearing vibration replay")
    st.caption("Measured vibration-feature histories; not a live machine connection or a raw waveform display.")
    if not (EVIDENCE / "pronostia_replay.json").is_file():
        st.info("Verified physical replay traces are not yet published.")
        st.markdown("[Replay execution workflow](https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/workflows/research-pronostia-replay.yml)")
        return
    report = read_report("pronostia_replay.json")
    st.caption(report["scope"])
    traces = {t["bearing"]:t for t in report["traces"]}
    bearing = st.selectbox("Physical bearing", sorted(traces), key="physical_replay_bearing")
    trace = traces[bearing]
    points = pd.DataFrame(trace["points"]).set_index("age")
    age = st.select_slider("Observed recording", options=points.index.tolist(), key=f"physical_replay_age_{bearing}")
    history = points.loc[:age]
    current = history.iloc[-1]
    st.caption(f"Condition {trace['condition']} · recording interval {report['recording_interval_seconds']} seconds · display cadence {report['display_cadence_snapshots']} recordings")
    a,b,c = st.columns(3)
    a.metric("Observed vibration ratio", f"{current['ratio']:.2f}x")
    b.metric("Statistical remaining snapshots", f"{current['age_reference']:.1f}")
    c.metric("Learned remaining snapshots", f"{current['learned']:.1f}")
    st.markdown("**Observed vibration features**")
    feature = st.radio("Vibration feature", ["rms","crest"], key="physical_replay_feature")
    st.line_chart(history[[f"horizontal_{feature}",f"vertical_{feature}"]])
    st.markdown("**Forecast comparison**")
    st.line_chart(history[["age_reference","learned","switch_2x","ramp_2x_4x"]])
    st.caption("Forecasts are in remaining recorded snapshots. The gate is computed from all observations available at the selected age, not only displayed samples.")
    st.info("2x gate uses learned forecast." if current["ratio"]>=2 else "2x gate uses statistical reference.")
    if st.checkbox("Reveal retrospective endpoint", key=f"physical_replay_truth_{bearing}"):
        st.metric("Actual remaining recorded snapshots", trace["last_recorded_age"]-age)
        st.caption("Last recorded observation is an endpoint proxy, not independently timed failure. It was not used by the forecast.")
    st.markdown(f"[Execution evidence]({report['run_url']})")
    st.download_button("Download physical replay evidence", json.dumps(report, indent=2), "pronostia_replay.json", "application/json")


def render_cwru():
    st.subheader("Measured bearing spectral audit")
    report = read_report("cwru_spectral_summary.json")
    st.caption("Post-v0.1.0 CWRU seeded-fault recordings; descriptive spectral comparison, not classification accuracy.")
    a, b, c = st.columns(3)
    a.metric("Recordings", report["record_count"])
    b.metric("Envelope improves expected order", f'{report["envelope_improves_expected_count"]}/{report["record_count"]}')
    c.metric("Analyzed samples", f'{sum(r["analyzed_samples"] for r in report["records"]):,}')
    rows = pd.DataFrame([
        {"Recording": str(r["file_id"]), "Defect": r["fault"], "Load (HP)": r["load_hp"],
         "Raw FFT (%)": 100*r["median_fractions"]["raw"][r["fault"]],
         "Envelope (%)": 100*r["median_fractions"]["envelope"][r["fault"]]}
        for r in report["records"]
    ])
    st.dataframe(rows, hide_index=True)
    st.bar_chart(rows.set_index("Recording")[["Raw FFT (%)", "Envelope (%)"]])
    st.caption("Median share of representation-specific non-DC spectral power in the first three expected-order harmonics.")
    counts = report["expected_exceeds_alternative_count"]
    st.markdown(f'Expected order exceeded alternative: raw **{counts["raw"]}/8**, envelope **{counts["envelope"]}/8**.')
    st.warning("No normal controls or competing ball defects; repeated windows and loads are correlated. No RUL, physical calibration, or field diagnosis established.")
    st.markdown(f"[Execution evidence]({report['run_url']}) · revision `{report['revision']}`")
    st.download_button("Download CWRU evidence summary", json.dumps(report, indent=2), "cwru_spectral_summary.json", "application/json")


def render_report():
    from research.technical_report import generate_report
    st.subheader("Technical evidence report")
    content = generate_report(EVIDENCE)
    st.download_button("Download technical report", content, "AERIS_technical_report.md", "text/markdown")
    st.markdown(content)


def render_evidence():
    st.title("AERIS | Research Intelligence")
    st.caption("Verified benchmark evidence · read-only research workspace")
    try:
        registered = verify(EVIDENCE)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Research evidence integrity check failed: {exc}")
        st.stop()
    st.caption(f"Content integrity verified for {len(registered)} registered evidence files. This is not scientific certification.")
    st.warning("Simulated and laboratory benchmark evidence, not industrial safety certification or measured savings.")
    pages = {
        "Evidence map": render_overview,
        "Maintenance replay": render_maintenance,
        "Official NASA test": render_official,
        "Temporal replay": render_replay,
        "Physical bearings": render_bearings,
        "Adaptive reliability": render_reliability,
        "Independent replication": render_replication,
        "Physical vibration replay": render_physical_replay,
        "CWRU spectral audit": render_cwru,
        "Technical report": render_report,
    }
    page = st.sidebar.radio("Research page", list(pages), key="research_page")
    pages[page]()
