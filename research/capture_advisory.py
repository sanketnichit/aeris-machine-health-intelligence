"""Offline archived-capture advisory; never authorizes machine operation.

Only the frozen MFPT/CWRU spectral recipe is used. Applicability to a new
machine is unvalidated. Trusted pins are an externally managed input.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from research.mfpt_transfer import RATE, WINDOW, WINDOWS, FLOOR, MARGIN
from research.mfpt_order_uncertainty import TOL, envelope_bins
from research.verify_evidence import parse
from src.calibration_provenance import advisory, provenance_status, timestamp, HEX
from src.capture_archive import load_capture, CAPTURE_ID
from src.vibration_acquisition import read_capture, AXES

MAX_PIN_BYTES = 1_000_000
CONTEXT_FIELDS = {"capture_id","capture_sha256","asset_id","axis","observed_from","observed_until",
                  "primary_speed_hz","secondary_speed_hz","effective_orders",
                  "primary","secondary","common"}


def denied(reason, action="obtain_applicable_capture_and_measurement_evidence"):
    return {"scope":"research_advisory_only","suggestion":None,"reason":reason,
            "next_action":action,"operational_authorization":False}


def _number(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0


def evaluate_capture(capture_id, raw, analysis, context_pin, trusted_artifacts):
    if not isinstance(context_pin,str) or not HEX.fullmatch(context_pin):
        return denied("measurement_context_unverified")
    if not isinstance(trusted_artifacts,dict):
        return denied("measurement_context_unverified")
    payload=trusted_artifacts.get(context_pin)
    if not isinstance(payload,bytes) or not payload or len(payload)>MAX_PIN_BYTES or hashlib.sha256(payload).hexdigest()!=context_pin:
        return denied("measurement_context_unverified")
    try:
        context=parse(payload)
        if not isinstance(context,dict) or set(context)!=CONTEXT_FIELDS:
            return denied("measurement_context_invalid")
        if (not isinstance(capture_id,str) or not CAPTURE_ID.fullmatch(capture_id)
                or capture_id!=context["capture_id"] or analysis["asset_id"]!=context["asset_id"]
                or hashlib.sha256(raw).hexdigest()!=context["capture_sha256"]
                or analysis["capture_sha256"]!=context["capture_sha256"]):
            return denied("capture_context_mismatch")
        if (analysis["sample_rate_hz"]!=RATE or analysis["window_samples"]!=WINDOW
                or analysis["window_count"]!=WINDOWS or analysis["sample_count"]!=WINDOW*WINDOWS):
            return denied("unsupported_frozen_capture_shape")
        if (analysis["flagged_windows"]!=0 or not analysis["eligible_for_queue"]
                or analysis["declared_clipping_limit_m_s2"] is None):
            return denied("capture_quality_not_established")
        if context["axis"] not in AXES:
            return denied("measurement_context_invalid")
        start=timestamp(analysis["start_utc"])
        end=timestamp(analysis["windows"][-1]["timestamp"])
        observed_from=timestamp(context["observed_from"])
        observed_until=timestamp(context["observed_until"])
        if not observed_from<=start<=end<=observed_until:
            return denied("measurement_does_not_cover_capture")
        p,s,c=(context[k] for k in ("primary","secondary","common"))
        for point in (context["observed_from"],context["observed_until"]):
            status=provenance_status(p,s,c,point,trusted_artifacts)
            if status!="declared_provenance_consistent":
                return denied(status,"obtain_applicable_calibration_evidence")
        if any(record["asset_id"]!=context["asset_id"] for record in (p,s,c)):
            return denied("capture_calibration_asset_mismatch")
        a,b=context["primary_speed_hz"],context["secondary_speed_hz"]
        orders=context["effective_orders"]
        if (not _number(a) or not _number(b) or not isinstance(orders,dict)
                or set(orders)!={"inner","outer","ball"} or any(not _number(v) for v in orders.values())):
            return denied("measurement_context_invalid")
        centers={k:a*v for k,v in orders.items()}
        if any(not math.isfinite(v) or 3*v+TOL>=RATE/2 for v in centers.values()):
            return denied("order_geometry_outside_frozen_band")
        samples=np.asarray(read_capture(raw,analysis["input_unit"]),dtype=float)
        if samples.shape!=(WINDOW*WINDOWS,2):
            return denied("capture_shape_mismatch")
        axis=samples[:,AXES.index(context["axis"])]
        spectra=[envelope_bins(axis[i*WINDOW:(i+1)*WINDOW]) for i in range(WINDOWS)]
        if not all(np.array_equal(f,spectra[0][0]) for f,_ in spectra):
            return denied("inconsistent_frequency_bins")
        result=advisory(spectra[0][0],[power for _,power in spectra],centers,b/a,
                        p,s,c,context["observed_until"],trusted_artifacts,TOL,FLOOR,MARGIN)
        return {**result,"capture_id":capture_id,"capture_sha256":context["capture_sha256"],
                "measurement_context_sha256":context_pin,"axis":context["axis"],
                "recipe":"frozen_mfpt_envelope_12000hz_8192x4",
                "limitations":["external calibration and pin enrollment not authenticated by this tool",
                               "speed stationarity, geometry, sample clock and field applicability are declared, not independently verified"]}
    except (ValueError, TypeError, KeyError, OverflowError, IndexError, ArithmeticError):
        return denied("invalid_capture_or_measurement_inputs")


def load_pins(directory):
    directory=Path(directory)
    if not directory.is_dir():
        raise ValueError("Trusted pin directory required")
    result={}
    # Dedicated, externally controlled directory: only digest-named files.
    for i,path in enumerate(directory.iterdir()):
        if i>=64 or not path.is_file() or path.is_symlink() or not HEX.fullmatch(path.name):
            raise ValueError("Unexpected trusted pin entry")
        with path.open("rb") as handle:
            raw=handle.read(MAX_PIN_BYTES+1)
        if not raw or len(raw)>MAX_PIN_BYTES or hashlib.sha256(raw).hexdigest()!=path.name:
            raise ValueError("Trusted pin fingerprint mismatch")
        result[path.name]=raw
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--capture-id",required=True)
    parser.add_argument("--trusted-pins",type=Path,required=True)
    parser.add_argument("--context-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    raw,analysis=load_capture(args.archive,args.capture_id)
    result=evaluate_capture(args.capture_id,raw,analysis,args.context_sha256,load_pins(args.trusted_pins))
    with args.output.open("x",encoding="utf-8") as handle:
        json.dump(result,handle,indent=2,allow_nan=False)
        handle.write("\n")


if __name__=="__main__":
    main()
