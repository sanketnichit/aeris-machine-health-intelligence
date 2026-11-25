import hashlib
import itertools
import json

import numpy as np
import pytest

from src.common_mode import common_mode_intersection, common_mode_guard
from src.calibration_provenance import provenance_status, advisory


@pytest.mark.parametrize("common", [0., .01, .05])
def test_valid_decomposition_contains_reference(common):
    for c, a, b in itertools.product((-common,0.,common),(-.01,0.,.01),(-.005,0.,.005)):
        p, s = 1+c+a, 1+c+b
        out = common_mode_intersection(s/p,.01,.005,common)
        assert out["intersection"] is not None
        lo, hi = out["intersection"]
        assert lo-1e-12 <= 1/p <= hi+1e-12


def test_common_mode_cannot_explain_differential_disagreement():
    out = common_mode_intersection(1.04,.005,.005,.05)
    assert out["expanded_intersection"] is not None
    assert out["status"] == "common_mode_conflict"
    assert out["intersection"] is None


def test_shared_bias_widens_false_agreement():
    false = common_mode_intersection(1.,.005,.005,0.)
    fixed = common_mode_intersection(1.,.005,.005,.05)
    assert not false["intersection"][0] <= 1/1.05 <= false["intersection"][1]
    assert fixed["intersection"][0] <= 1/1.05 <= fixed["intersection"][1]


def test_unknown_common_bound_abstains():
    out = common_mode_guard(None,None,None,1.,.01,.01,None,1.,.5,.8)
    assert out["suggestion"] is None
    assert out["reason"] == "common_mode_bound_missing"


def fixture():
    payload = b"synthetic certificate fixture, not calibration"
    digest = hashlib.sha256(payload).hexdigest()
    base = {"asset_id":"asset","reference_id":"reference","common_group":"group",
            "valid_from":"2026-01-01T00:00:00Z","valid_until":"2027-01-01T00:00:00Z",
            "certificate_sha256":digest}
    primary = {**base,"channel_id":"primary","individual_bound":.005}
    secondary = {**base,"channel_id":"secondary","individual_bound":.005}
    common = {**base,"common_bound":.01}
    artifacts = {digest:payload}
    def enroll(record):
        raw = json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
        pin = hashlib.sha256(raw).hexdigest()
        artifacts[pin] = raw
        return {**record,"enrollment_sha256":pin}
    return enroll(primary), enroll(secondary), enroll(common), "2026-06-01T00:00:00Z", artifacts


@pytest.mark.parametrize("change,expected", [
    ("expired","calibration_outside_validity"),
    ("missing","calibration_metadata_missing"),
    ("tampered","calibration_artifact_unverified"),
    ("duplicate","calibration_enrollment_mismatch"),
    ("scope","calibration_enrollment_mismatch"),
    ("badtime","observation_timestamp_invalid"),
    ("badbound","calibration_metadata_invalid"),
    ("alteredbound","calibration_enrollment_mismatch"),
    ("missingpin","calibration_enrollment_unverified")])
def test_provenance_rejections(change,expected):
    p,s,c,t,artifacts = fixture()
    if change=="expired": t="2027-01-01T00:00:00Z"
    if change=="missing": c=None
    if change=="tampered": artifacts={p["certificate_sha256"]:b"tampered"}
    if change=="duplicate": s["channel_id"]=p["channel_id"]
    if change=="scope": c["asset_id"]="different"
    if change=="badtime": t="2026-06-01"
    if change=="badbound": p["individual_bound"]=float("nan")
    if change=="alteredbound": p["individual_bound"]=.0001
    if change=="missingpin": artifacts.pop(p["enrollment_sha256"])
    assert provenance_status(p,s,c,t,artifacts)==expected
    out=advisory(None,None,None,1.,p,s,c,t,artifacts,1.,.5,.8)
    assert out["suggestion"] is None and not out["operational_authorization"]


def test_valid_provenance_only_authorizes_review():
    p,s,c,t,artifacts=fixture()
    f=np.arange(151,dtype=float)
    power=np.zeros_like(f)
    power[9:12]=1
    centers={"outer":10.,"inner":40.,"ball":45.}
    out=advisory(f,[power],centers,1.,p,s,c,t,artifacts,1.1,.5,.8)
    assert out["provenance"]=="declared_provenance_consistent"
    assert out["suggestion"]=="outer"
    assert out["next_action"]=="engineering_review_of_conditional_suggestion"
    assert not out["operational_authorization"]


def reenroll(record, artifacts):
    record = {k:v for k,v in record.items() if k!="enrollment_sha256"}
    raw = json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    digest = hashlib.sha256(raw).hexdigest()
    artifacts[digest] = raw
    return {**record,"enrollment_sha256":digest}


def test_distinct_pinned_metadata_still_requires_matching_scope_and_channels():
    p,s,c,t,artifacts=fixture()
    duplicate=reenroll({**s,"channel_id":p["channel_id"]},artifacts)
    assert provenance_status(p,duplicate,c,t,artifacts)=="duplicate_measurement_channel"
    other=reenroll({**c,"asset_id":"other"},artifacts)
    assert provenance_status(p,s,other,t,artifacts)=="calibration_scope_mismatch"
