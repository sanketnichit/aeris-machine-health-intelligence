"""Local telemetry fleet view, separate from benchmark prediction workspaces."""
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError

import pandas as pd
import streamlit as st


def fetch(route, params=None):
    # Deployment-controlled base URL, never a user-entered destination.
    base=os.environ.get("AERIS_API_URL","http://127.0.0.1:8080").rstrip("/")
    suffix="?"+urlencode(params) if params else ""
    token=os.environ.get("AERIS_API_TOKEN")
    request=Request(base+route+suffix,headers={"Authorization":"Bearer "+token} if token else {})
    with urlopen(request,timeout=4) as response:
        return json.load(response)


def render_fleet():
    st.title("AERIS | Telemetry fleet")
    st.caption("Registered machine observations · local research storage")
    st.warning("Data completeness is not machine health. No operational forecast or control is provided.")
    st.button("Refresh fleet")
    try:
        report=fetch("/v1/assets")
    except (URLError,OSError,ValueError):
        st.info("Local telemetry API unavailable. Start it with python -m src.api, or use Docker Compose.")
        return
    rows=report["assets"]
    a,b,c=st.columns(3)
    a.metric("Registered assets",report["total_assets"])
    b.metric("Displayed assets",len(rows))
    c.metric("Complete latest records",sum(r["quality"]=="complete" for r in rows))
    if report["truncated"]:
        st.warning("Only the first 200 registered assets are displayed.")
    if not rows:
        st.info("No assets registered. Use the local API to register an asset and ingest observations.")
        return
    st.dataframe(pd.DataFrame(rows),hide_index=True)
    with st.expander("Recent monitoring events"):
        try:
            event_report=fetch("/v1/events",{"limit":100})
            events=event_report["events"]
            st.caption("Latest 100 observation-level events, ordered by ingestion. Not active incidents or machine diagnoses.")
            if events:
                st.dataframe(pd.DataFrame(events),hide_index=True)
                st.download_button("Download monitoring events",json.dumps(events,indent=2),"monitoring_events.json","application/json")
            else:
                st.info("No monitoring events recorded.")
        except (URLError,OSError,ValueError,KeyError):
            st.info("Monitoring event history unavailable.")
    with st.expander("Review incidents"):
        try:
            incident_report=fetch("/v1/incidents",{"limit":100})
            incidents=incident_report["incidents"]
            st.caption("Recent review incidents. Acknowledgement and resolution are manual API actions, not evidence of repaired equipment.")
            if incidents:
                st.dataframe(pd.DataFrame(incidents),hide_index=True)
                st.download_button("Download incident history",json.dumps(incidents,indent=2),"incidents.json","application/json")
            else:
                st.info("No review incidents recorded.")
        except (URLError,OSError,ValueError,KeyError):
            st.info("Incident history unavailable.")
    asset=st.selectbox("Asset", [r["asset_id"] for r in rows],key="fleet_asset")
    try:
        records=fetch("/v1/telemetry/history",{"asset_id":asset,"limit":1000})["records"]
    except (URLError,OSError,ValueError):
        st.error("Unable to retrieve asset history.")
        return
    if not records:
        st.info("No observations stored for this asset.")
        return
    names=sorted({name for row in records for name in row["measurements"]})
    signal=st.selectbox("Measurement",names,key="fleet_signal")
    points=[{"Timestamp":row["timestamp"],"Value":row["measurements"][signal]["value"]}
            for row in records if signal in row["measurements"]]
    unit=next(row["measurements"][signal]["unit"] for row in records if signal in row["measurements"])
    st.caption(f"{signal} ({unit}) · most recent 1000 records at most; missing values are not imputed.")
    frame=pd.DataFrame(points)
    frame["Timestamp"]=pd.to_datetime(frame["Timestamp"],utc=True)
    st.line_chart(frame.set_index("Timestamp"))
    st.dataframe(frame,hide_index=True)
    st.download_button("Download retrieved history",json.dumps(records,indent=2),f"{asset}_history.json","application/json")
