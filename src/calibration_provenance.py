"""Calibration provenance gate for research advisory decisions.

A pinned digest proves byte identity only. The caller must independently
establish certificate authenticity, applicability and trustworthy pinning.
No machine actuation or operational authorization is provided.
"""
import datetime as dt
import hashlib
import math
import re

from src.measurement_budget import _bound
from src.common_mode import common_mode_guard

HEX = re.compile(r"[0-9a-f]{64}")
FIELDS = {"channel_id", "asset_id", "reference_id", "common_group",
          "valid_from", "valid_until", "individual_bound", "certificate_sha256"}
COMMON_FIELDS = {"asset_id", "reference_id", "common_group",
                 "valid_from", "valid_until", "common_bound", "certificate_sha256"}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("UTC timestamp required")
    parsed = dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValueError("UTC timestamp required")
    return parsed


def _id(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 128 and value == value.strip()


def _certificate(record, fields, bound_key, when, trusted):
    if not isinstance(record, dict) or set(record) != fields:
        return "calibration_metadata_missing"
    for key in fields & {"channel_id", "asset_id", "reference_id", "common_group"}:
        if not _id(record[key]):
            return "calibration_metadata_invalid"
    digest = record["certificate_sha256"]
    if not isinstance(digest, str) or not HEX.fullmatch(digest):
        return "calibration_metadata_invalid"
    try:
        start, end = timestamp(record["valid_from"]), timestamp(record["valid_until"])
        _bound(record[bound_key])
    except (ValueError, TypeError, OverflowError):
        return "calibration_metadata_invalid"
    if not start <= when < end:
        return "calibration_outside_validity"
    payload = trusted.get(digest)
    if not isinstance(payload, bytes) or not payload or len(payload) > 1_000_000 or hashlib.sha256(payload).hexdigest() != digest:
        return "calibration_artifact_unverified"
    return None


def provenance_status(primary, secondary, common, observed_at, trusted_artifacts):
    try:
        when = timestamp(observed_at)
    except (ValueError, TypeError, OverflowError):
        return "observation_timestamp_invalid"
    if not isinstance(trusted_artifacts, dict):
        return "calibration_artifact_unverified"
    for record, fields, bound in ((primary,FIELDS,"individual_bound"),
                                  (secondary,FIELDS,"individual_bound"),
                                  (common,COMMON_FIELDS,"common_bound")):
        problem = _certificate(record, fields, bound, when, trusted_artifacts)
        if problem:
            return problem
    if primary["channel_id"] == secondary["channel_id"]:
        return "duplicate_measurement_channel"
    # Different channels can share the same certificate, but distinct
    # channels and an explicitly declared common group are required.
    for key in ("asset_id", "reference_id", "common_group"):
        if not primary[key] == secondary[key] == common[key]:
            return "calibration_scope_mismatch"
    return "declared_provenance_consistent"


def advisory(frequencies, window_powers, primary_centers, ratio, primary, secondary,
             common, observed_at, trusted_artifacts, tolerance, floor, margin):
    status = provenance_status(primary, secondary, common, observed_at, trusted_artifacts)
    if status != "declared_provenance_consistent":
        return {"scope": "research_advisory_only", "provenance": status, "suggestion": None,
                "reason": status, "next_action": "obtain_applicable_calibration_evidence",
                "operational_authorization": False}
    result = common_mode_guard(frequencies, window_powers, primary_centers, ratio,
                               primary["individual_bound"], secondary["individual_bound"],
                               common["common_bound"], tolerance, floor, margin)
    if result["intersection"] is None:
        action = "reconcile_measurement_conflict"
    elif result["suggestion"] is None:
        action = "obtain_better_reference_measurement_or_review_spectrum"
    else:
        action = "engineering_review_of_conditional_suggestion"
    return {**result, "scope": "research_advisory_only", "provenance": status,
            "next_action": action, "operational_authorization": False}
