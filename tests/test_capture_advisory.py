import hashlib
import json

import numpy as np
import pytest

from research.capture_advisory import evaluate_capture, load_pins
from research.mfpt_transfer import RATE, WINDOW, WINDOWS
from src.calibration_console import example_records
from src.capture_archive import archive_capture, load_capture


def pin(context,pins):
    data=json.dumps(context,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    digest=hashlib.sha256(data).hexdigest()
    pins[digest]=data
    return digest


@pytest.fixture(scope="module")
def capture(tmp_path_factory):
    root=tmp_path_factory.mktemp("archive")
    t=np.arange(WINDOW*WINDOWS)/RATE
    x=(1+.7*np.sin(2*np.pi*80*t))*np.sin(2*np.pi*3000*t)
    y=np.sin(2*np.pi*110*t)
    raw=("horizontal,vertical\n"+"".join(f"{a:.8f},{b:.8f}\n" for a,b in zip(x,y))).encode()
    path=root/"capture.sqlite"
    entry=archive_capture(path,raw,asset_id="synthetic-bearing",start="2026-06-01T00:00:00Z",
                          sample_rate_hz=RATE,window_samples=WINDOW,unit="m/s2",clipping_limit=10.)
    ident=entry["capture_id"]
    raw,analysis=load_capture(path,ident)
    return ident,raw,analysis


def context_for(capture):
    ident,raw,analysis=capture
    p,s,c,pins=example_records(.001)
    context={"capture_id":ident,"capture_sha256":analysis["capture_sha256"],
             "asset_id":analysis["asset_id"],"axis":"horizontal",
             "observed_from":analysis["start_utc"],"observed_until":analysis["windows"][-1]["timestamp"],
             "primary_speed_hz":25.,"secondary_speed_hz":25.,
             "effective_orders":{"outer":3.2,"inner":5.,"ball":6.},
             "primary":p,"secondary":s,"common":c}
    return context,pins


def test_archived_capture_research_advisory(capture):
    context,pins=context_for(capture)
    digest=pin(context,pins)
    result=evaluate_capture(*capture,digest,pins)
    assert result["suggestion"]=="outer"
    assert result["capture_id"]==capture[0]
    assert result["measurement_context_sha256"]==digest
    assert not result["operational_authorization"]


@pytest.mark.parametrize("change,reason",[
    ("hash","capture_context_mismatch"),("asset","capture_context_mismatch"),
    ("time","measurement_does_not_cover_capture"),("missing","calibration_metadata_missing"),
    ("bound","calibration_enrollment_mismatch"),("geometry","order_geometry_outside_frozen_band")])
def test_invalid_context_abstains(capture,change,reason):
    context,pins=context_for(capture)
    if change=="hash": context["capture_sha256"]="a"*64
    if change=="asset": context["asset_id"]="wrong"
    if change=="time": context["observed_until"]=context["observed_from"]
    if change=="missing": context["common"]=None
    if change=="bound": context["primary"]["individual_bound"]=.0001
    if change=="geometry": context["effective_orders"]["outer"]=1000.
    result=evaluate_capture(*capture,pin(context,pins),pins)
    assert result["suggestion"] is None and result["reason"]==reason
    assert not result["operational_authorization"]


def test_unpinned_context_abstains(capture):
    result=evaluate_capture(*capture,"a"*64,{})
    assert result["reason"]=="measurement_context_unverified"
    assert result["suggestion"] is None


def test_trusted_pin_directory_rejects_tamper(tmp_path):
    raw=b"trusted fixture"
    digest=hashlib.sha256(raw).hexdigest()
    file=tmp_path/digest
    file.write_bytes(raw)
    assert load_pins(tmp_path)=={digest:raw}
    file.write_bytes(b"altered")
    with pytest.raises(ValueError,match="fingerprint"):
        load_pins(tmp_path)
