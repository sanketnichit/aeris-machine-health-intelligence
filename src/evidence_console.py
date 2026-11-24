"""Read-only Streamlit research evidence; no model fitting or network requests."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

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


def render_evidence():
    st.title("AERIS | Research Intelligence")
    st.caption("Verified benchmark evidence · read-only research workspace")
    st.warning("Simulated and laboratory benchmark evidence, not industrial safety certification or measured savings.")
    overview, maintenance, official, replay, bearings = st.tabs(["Evidence map", "Maintenance replay", "Official NASA test", "Temporal replay", "Physical bearings"])
    with overview:
        st.subheader("Research evidence")
        st.markdown(
            "- [AI4I physics rules and stress tests](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/main/research/AI4I_FINDINGS.md)\n"
            "- [NASA stage and landmark evaluation](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/main/research/CMAPSS_STAGE_FINDINGS.md)\n"
            "- [Paired statistics and risk evaluation](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/main/research/CMAPSS_RISK_FINDINGS.md)\n"
            "- [Frozen official test protocol](https://github.com/sanketnichit/aeris-machine-health-intelligence/blob/main/research/FD001_OFFICIAL_PROTOCOL.md)"
        )
        st.info("AI4I generator rules beat ML on the synthetic snapshot benchmark. Personalized temporal forecasts improve later-life development errors on simulated FD001 engines. Early-life uncertainty remains substantial.")
    with maintenance:
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
    with official:
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


    with replay:
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


    with bearings:
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
