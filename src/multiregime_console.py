"""Read-only multi-regime NASA evidence view; no fitting or label access."""
import json

import pandas as pd
import streamlit as st

NAME="cmapss_multiregime_summary.json"


def endpoint_rows(report,subset):
    rows=[]
    for s in report["scenarios"]:
        if s["subset"]!=subset:
            continue
        for model,metrics in s["metrics"].items():
            rows.append({"Training mode":s["mode"],"Model":model,
                         "Test engines":s["test_engines"],"MAE":metrics["mae"],
                         "RMSE":metrics["rmse"],"NASA score":metrics["nasa_score"],
                         "Mean signed error":metrics["mean_signed_error"],
                         "Overprediction >20":metrics["overprediction_gt20_fraction"]})
    return pd.DataFrame(rows)


def render_multiregime(read_report,registered):
    st.subheader("NASA C-MAPSS multi-regime evaluation")
    st.warning("Official simulated engine endpoints, not physical validation. Within-subset refitting and FD001 transfer reuse the same new test endpoints; they are not independent populations.")
    if NAME not in registered:
        st.info("Frozen multi-regime protocol committed; numerical evidence is not yet registered.")
        return
    report=read_report(NAME)
    transfer=[s for s in report["scenarios"] if s["subset"]!="FD001" and s["mode"]=="fd001_transfer"]
    worse=sum(s["metrics"][report["primary"]]["mae"]>s["metrics"]["age_reference"]["mae"] for s in transfer)
    st.warning(f"Direct FD001 transfer is worse than the age reference on {worse}/{len(transfer)} new subsets by MAE. Do not assume regime applicability.")
    a,b,c=st.columns(3)
    a.metric("Distinct official endpoints",report["unique_test_engines"])
    b.metric("New subset endpoints",report["new_subset_test_engines"])
    c.metric("Scenario endpoint comparisons",report["endpoint_evaluations"])
    subset=st.selectbox("Official subset",["FD001","FD002","FD003","FD004"],index=1,key="cmapss_multiregime_subset")
    rows=endpoint_rows(report,subset)
    st.dataframe(rows,hide_index=True)
    st.bar_chart(rows,x="Model",y="MAE",color="Training mode",stack=False)
    st.caption("MAE in simulated cycles; NASA score is a summed asymmetric penalty, not directly comparable across different endpoint counts.")
    st.markdown(f"[Execution evidence]({report['run_url']}) | revision {report['revision']}")
    st.download_button("Download registered multi-regime evidence",json.dumps(report,indent=2),NAME,"application/json")
