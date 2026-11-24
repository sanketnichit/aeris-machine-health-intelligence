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
    overview, maintenance, official = st.tabs(["Evidence map", "Maintenance replay", "Official NASA test"])
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
