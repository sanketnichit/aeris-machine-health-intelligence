"""Synthetic, non-operational decision-support demonstration."""
import hashlib
import json
import os
import sqlite3

import pandas as pd

import numpy as np
import streamlit as st

from src.calibration_provenance import advisory
from src.advisory_review import list_advisories


def example_records(common_bound, missing=False, expired=False):
    payload = b"AERIS synthetic training fixture; no real calibration certificate"
    cert = hashlib.sha256(payload).hexdigest()
    artifacts = {cert:payload}
    base = {"asset_id":"synthetic-bearing","reference_id":"synthetic-reference",
            "common_group":"synthetic-shared-clock","valid_from":"2026-01-01T00:00:00Z",
            "valid_until":"2026-06-01T00:00:00Z" if expired else "2027-01-01T00:00:00Z",
            "certificate_sha256":cert}
    def pin(record):
        data=json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        digest=hashlib.sha256(data).hexdigest()
        artifacts[digest]=data
        return {**record,"enrollment_sha256":digest}
    p=pin({**base,"channel_id":"primary","individual_bound":.005})
    s=pin({**base,"channel_id":"secondary","individual_bound":.005})
    c=None if missing else pin({**base,"common_bound":common_bound})
    return p,s,c,artifacts


def demo_advisory(primary_error, secondary_error, common_bound, scenario):
    p,s,c,artifacts=example_records(common_bound, scenario=="Missing", scenario=="Expired")
    if scenario=="Altered enrollment":
        p["individual_bound"]=.0001
    f=np.arange(151,dtype=float)
    power=np.zeros_like(f)
    power[9:12]=1
    centers={"outer":10*(1+primary_error),"inner":40*(1+primary_error),"ball":45*(1+primary_error)}
    return advisory(f,[power],centers,(1+secondary_error)/(1+primary_error),
                    p,s,c,"2026-06-01T00:00:00Z",artifacts,1.1,.5,.8)


def render_calibration_lab():
    st.subheader("Calibration and common-mode decision lab")
    st.warning("Synthetic demonstration only. Fixture fingerprints are not real calibration or operational authorization.")
    a,b=st.columns(2)
    with a:
        primary=st.slider("Primary indicated speed error (%)",-5.,5.,0.,.5,key="cal_primary")
        secondary=st.slider("Secondary indicated speed error (%)",-5.,5.,0.,.5,key="cal_secondary")
    with b:
        common=st.select_slider("Assumed common error bound (%)",options=[0.,1.,5.],value=1.,key="cal_common")
        scenario=st.radio("Synthetic calibration record",["Consistent","Missing","Expired","Altered enrollment"],key="cal_record")
    result=demo_advisory(primary/100,secondary/100,common/100,scenario)
    st.metric("Research suggestion",result["suggestion"] or "Withheld")
    st.write("Provenance:",result["provenance"])
    st.write("Reason:",result["reason"])
    st.write("Next action:",result["next_action"])
    if result.get("intersection") is not None:
        lo,hi=result["intersection"]
        st.write(f"Possible reference/primary scale: {lo:.5f} to {hi:.5f}")
        st.caption("The modeled reference scale is displayed only for this synthetic demonstration.")
        st.write(f"Reference contained in this fixture: {lo-1e-12 <= 1/(1+primary/100) <= hi+1e-12}")
    st.caption("Operational authorization: false. No machine or real sensor is connected.")


    with st.expander("Local capture-advisory review journal"):
        path=os.environ.get("AERIS_ADVISORY_JOURNAL_PATH")
        if not path:
            st.info("Local review journal is disabled. Configure a trusted local database explicitly.")
        else:
            st.warning("Read-only local research review journal. Anyone with dashboard access can inspect configured records. Review does not authorize operation.")
            try:
                rows=list_advisories(path)
            except (OSError,sqlite3.Error,ValueError,TypeError,KeyError):
                st.error("Advisory journal integrity or availability check failed.")
                return
            if not rows:
                st.info("No capture advisories recorded.")
                return
            table=pd.DataFrame([{"Asset":r["asset_id"],"Advisory":r["advisory_id"],
                                 "Suggestion":r["report"]["suggestion"] or "Withheld",
                                 "Reason":r["report"]["reason"],
                                 "Review":r["review_status"],"Recorded":r["created_at"]} for r in rows])
            st.dataframe(table,hide_index=True)
            ident=st.selectbox("Inspect recorded advisory",list(table["Advisory"]),key="capture_review_id")
            record=next(r for r in rows if r["advisory_id"]==ident)
            st.json(record,expanded=False)
            st.download_button("Download advisory record",json.dumps(record,indent=2),
                               f"advisory-{ident}.json","application/json")
