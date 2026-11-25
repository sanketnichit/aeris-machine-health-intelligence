"""Read-only Paderborn acquisition evidence and diagnostic eligibility status."""
import json
import pandas as pd
import streamlit as st

INTAKE="paderborn_intake_summary.json"
TIME="paderborn_timebase_summary.json"
COHORT="paderborn_cohort_summary.json"


def timebase_rows(report):
    out=[]
    for row in report["records"]:
        channels={c["name"]:c for c in row["channels"]}
        v=channels["vibration_1"]
        s=channels["speed"]
        candidates=v["raster_and_count_candidates"]
        axis=row["time_axes"][candidates[0]]["vector"] if len(candidates)==1 else {}
        consistent=all(len(c["raster_and_count_candidates"])==1 and
                       c["metadata"].get("XIndex")==str(c["raster_and_count_candidates"][0]+1)
                       for c in (v,s))
        out.append({"Specimen":row["specimen"],"Recording":row["filename"],
                    "Vibration samples":v["vector"]["count"],"Stored span":axis.get("span"),
                    "Median stored step":axis.get("median_step"),
                    "Max relative step deviation":axis.get("max_relative_step_deviation"),
                    "Raster/count/index consistent":consistent,
                    "Native speed median":s["vector"].get("median"),
                    "Physical clock verified":False,"Diagnostic eligible":False})
    return pd.DataFrame(out)


def render_paderborn(read_report,registered):
    st.subheader("Paderborn physical acquisition and timing")
    st.warning("Structural and conditional research evidence only. Nominal sampling rate is not a calibrated timebase; unqualified diagnostic scoring remains blocked. No operational performance is claimed.")
    if INTAKE not in registered:
        st.info("Structural acquisition pending.")
        return
    intake=read_report(INTAKE)
    a,b,c=st.columns(3)
    a.metric("Pilot specimens",intake["specimens"])
    b.metric("Inventoried recordings",intake["inventory_measurements"])
    c.metric("Sample-count discrepancies",intake["nominal_sample_count_mismatches"])
    st.markdown(f"[Source intake execution]({intake['run_url']})")
    if TIME in registered:
        report=read_report(TIME)
        rows=timebase_rows(report)
        st.dataframe(rows,hide_index=True)
        st.metric("Internally consistent channel links",int(rows["Raster/count/index consistent"].sum()))
        st.caption("Stored time units are not verified. Relative step deviation is dimensionless. XIndex agreement is internal metadata consistency, not proof of physical timing.")
        st.markdown(f"[Timing execution]({report['run_url']})")
        st.download_button("Download timing evidence",json.dumps(report,indent=2),TIME,"application/json")
    else:
        st.info("Timing audit pending.")
    if COHORT in registered:
        cohort=read_report(COHORT)
        st.metric("Primary cohort specimens inventoried",cohort["specimens"])
        st.metric("Primary recording inventory",cohort["inventory_measurements"])
        st.markdown(f"[Cohort execution]({cohort['run_url']})")
    else:
        st.info("Primary cohort archive inventory pending; 17 specimens predeclared.")

    if "paderborn_conditional_summary.json" in registered:
        terminal=read_report("paderborn_conditional_summary.json")
        st.subheader("Frozen conditional diagnostic transfer")
        st.warning("Negative transfer result: low fault coverage and false suggestions on healthy recordings. Geometry and clock remain unverified; no operational authorization.")
        st.dataframe(conditional_rows(terminal),hide_index=True)
        st.metric("Decision agreement",f"{terminal['agreement']}/{terminal['recordings']}")
        st.caption("Paired timing hypotheses on the same recordings; agreement is not clock calibration.")
        st.markdown(f"[Conditional experiment execution]({terminal['run_url']})")
        st.download_button("Download conditional evidence",json.dumps(terminal,indent=2),"paderborn_conditional_summary.json","application/json")


def conditional_rows(report):
    return pd.DataFrame([{"Timing hypothesis":mode,"Fault recordings":row["fault_records"],
                          "Correct fault":row["correct_accepted"],"Incorrect fault":row["incorrect_accepted"],
                          "Fault abstention":row["fault_abstained"],"Healthy recordings":row["normal_records"],
                          "Healthy false suggestions":row["normal_incorrect_accepted"]}
                         for mode,row in report["overall"].items()])
