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
    render_development(read_report,registered)


DEVELOPMENT="cmapss_regime_development_summary.json"


def development_rows(report,source,target):
    rows=[]
    for s in report["scenarios"]:
        if (s["source"],s["target"])!=(source,target):
            continue
        metrics=s.get("metrics",{})
        rows.append({"Age (cycles)":s["landmark"],"Calibration engines":s["calibration_survivors"],
                     "Evaluation endpoints":s["endpoints"],"Setting support rejected":s["support_rejected"],
                     "Accepted forecasts":s["accepted"],"Acceptance fraction":s["coverage"],
                     "Age MAE":metrics.get("age",{}).get("mae"),
                     "Relative MAE":metrics.get("relative",{}).get("mae"),
                     "Regime MAE":metrics.get("regime",{}).get("mae"),
                     "Raw interval coverage":s.get("raw_interval_coverage"),
                     "Accepted interval coverage":s["accepted_interval_coverage"],
                     "Accepted MAE":s["accepted_mae"],"Reasons":json.dumps(s["reasons"],sort_keys=True)})
    return pd.DataFrame(rows)


def render_development(read_report,registered):
    st.subheader("Training-only regime and forecast applicability")
    st.caption("Engine-disjoint fitting, calibration and evaluation at observable ages. The official test offsets are not accessed by this development audit.")
    if DEVELOPMENT not in registered:
        st.info("Regime-development protocol committed; numerical evidence is not yet registered.")
        return
    report=read_report(DEVELOPMENT)
    modes=sorted({(s["source"],s["target"]) for s in report["scenarios"]})
    source,target=st.selectbox("Development source and target",modes,
                              format_func=lambda pair:f"{pair[0]} to {pair[1]}",
                              key="cmapss_regime_pair")
    rows=development_rows(report,source,target)
    st.dataframe(rows,hide_index=True)
    st.bar_chart(rows.set_index("Age (cycles)")[["Age MAE","Relative MAE","Regime MAE"]])
    st.warning("Setting support is not domain equivalence. Coverage among retained forecasts is descriptive and may differ from raw interval coverage. No conditional coverage or operational authorization is established.")
    st.caption(f"Fixed illustrative interval-width limit: {report['width_limit_cycles']:g} simulated cycles.")
    st.markdown(f"[Development execution]({report['run_url']})")
    st.download_button("Download registered regime-development evidence",json.dumps(report,indent=2),DEVELOPMENT,"application/json")
