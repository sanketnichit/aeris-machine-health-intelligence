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


def read_report(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def render_evidence():
    st.title("AERIS | Research Intelligence")
    st.caption("Verified benchmark evidence · read-only research workspace")
    st.warning("Simulated benchmark results, not industrial safety certification or measured savings.")
    overview, maintenance, official, replay = st.tabs(["Evidence map", "Maintenance replay", "Official NASA test", "Temporal replay"])
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
