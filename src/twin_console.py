"""Interactive hypothetical simulation, isolated from live telemetry."""
import json
import pandas as pd
import streamlit as st

from src.digital_twin import Scenario, compare


def render_measured_context():
    from research.verify_evidence import ROOT, verify
    with st.expander("Measured vibration-state evidence",expanded=True):
        try:
            verified={r["file"] for r in verify(ROOT)}
            name="twin_calibration_summary.json"
            if name not in verified:
                raise ValueError("Calibration evidence not registered")
            report=json.loads((ROOT/name).read_text(encoding="utf-8"))
        except (OSError,ValueError,KeyError,TypeError):
            st.error("Verified calibration evidence unavailable.")
            return
        summary=report["summary"]["all"]
        st.caption(report["scope"])
        a,b,c=st.columns(3)
        a.metric("Learning transitions",report["fit"]["transitions"])
        b.metric("Held-out endpoints",summary["condition_drift"]["endpoints"])
        c.metric("Residual band mean width",f"{summary['condition_band']['mean_width']:.3f}")
        st.dataframe(pd.DataFrame([
            {"Predictor":key,**summary[key]} for key in ("persistence","global_drift","condition_drift")
        ]),hide_index=True)
        st.warning("The small improvement does not establish superiority. Residual coverage is descriptive; the virtual wear and cost model remains uncalibrated.")
        st.markdown(f"[Execution evidence]({report['run_url']}) · revision `{report['revision']}`")
        st.download_button("Download measured vibration audit",(ROOT/name).read_bytes(),name,"application/json")


def render_twin():
    st.title("AERIS | Virtual degradation laboratory")
    st.warning("Synthetic digital-twin prototype. No connection to physical assets, calibrated failure predictions or real savings.")
    render_measured_context()
    st.caption("Compare maintenance policies under identical seeded wear and observation-noise sequences.")
    with st.form("twin_scenario"):
        a,b,c=st.columns(3)
        horizon=a.slider("Horizon (virtual ticks)",50,500,200,step=50)
        load=b.slider("Relative operating load",.5,2.,1.,step=.1)
        noise=c.slider("Observation noise",0.,.2,.06,step=.01)
        age=a.slider("Planned service age",10,150,60,step=5)
        threshold=b.slider("Observed damage trigger",.2,.95,.75,step=.05)
        failure_cost=c.slider("Hypothetical failure cost",1,50,10)
        trials=a.selectbox("Monte Carlo trials",[100,200,500],index=1)
        seed=b.number_input("Random seed",min_value=0,max_value=2**32-1,value=42,step=1)
        st.form_submit_button("Run paired simulation")
    scenario=Scenario(horizon=horizon,load=load,observation_noise=noise,
                      service_age=age,condition_threshold=threshold,
                      failure_cost=failure_cost,trials=trials,seed=int(seed))
    report=compare(scenario)
    st.caption(report["scope"])
    table=pd.DataFrame([
        {"Policy":p,"Mean cost":v["cost"]["mean"],"Cost p05":v["cost"]["p05"],
         "Cost p95":v["cost"]["p95"],"Mean failures":v["failures"]["mean"],
         "Mean downtime ticks":v["downtime"]["mean"],"Mean operating ticks":v["operated"]["mean"],
         "Trials with failure":v["trial_failure_fraction"],
         "Mean paired cost difference":v["paired_cost_difference"]["mean"]}
        for p,v in report["summary"].items()
    ]).set_index("Policy")
    st.subheader("Paired maintenance comparison")
    st.dataframe(table)
    st.bar_chart(table[["Mean cost"]])
    st.caption("Costs are hypothetical units; failure fraction is a simulation statistic, not an asset failure probability.")
    st.subheader("Illustrative first-trial trajectory")
    traces=pd.DataFrame({p:[r["damage"] for r in rows] for p,rows in report["traces"].items()},
                        index=range(1,horizon+1))
    traces.index.name="Virtual tick"
    st.line_chart(traces)
    st.caption("Latent damage is displayed for explanation only. The condition policy uses noisy observed damage, not latent future damage.")
    chosen=st.selectbox("Inspect first-trial intervention history",list(report["traces"]),key="twin_trace")
    events=[row for row in report["traces"][chosen] if row["planned"] or row["failure"]]
    if events:
        st.dataframe(pd.DataFrame(events),hide_index=True)
    else:
        st.info("No interventions or failures in this illustrative trial.")
    st.download_button("Download scenario and paired results",json.dumps(report,indent=2),"aeris_virtual_scenario.json","application/json")
