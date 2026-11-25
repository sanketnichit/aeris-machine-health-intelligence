"""Selective research suggestions; margins are not calibrated probabilities."""
import argparse
import json
import math
from pathlib import Path
import subprocess

from research.cwru_extension import evaluate, ORDERS, RATE, WINDOW, WINDOWS
from research.verify_evidence import ROOT, verify

FILES = tuple((base+load, kind, .021, load)
              for base,kind in ((209,"inner"),(222,"ball"),(234,"outer"))
              for load in range(4))


def rank(fractions):
    if not isinstance(fractions,dict) or set(fractions)!=set(ORDERS):
        raise ValueError("Expected three defect-order fractions")
    if any(type(v) not in (float,int) or not math.isfinite(v) or not 0<=v<=1
           for v in fractions.values()):
        raise ValueError("Invalid spectral fraction")
    ordered = sorted(fractions.items(), key=lambda kv: (-kv[1],kv[0]))
    (kind,top),(_,second) = ordered[:2]
    return {"candidate":kind if top>second else None,"top":top,
            "margin":(top-second)/top if top else 0.0}


def decide(fractions, floor, threshold):
    result = rank(fractions)
    if threshold is None:
        reason = "development_rule_disabled"
    elif result["top"] <= floor:
        reason = "weak_order_evidence"
    elif result["candidate"] is None:
        reason = "tied_orders"
    elif result["margin"] < threshold:
        reason = "competing_orders"
    else:
        reason = "accepted_research_suggestion"
    return {**result,"suggestion":result["candidate"] if reason=="accepted_research_suggestion" else None,
            "reason":reason}


def assess(rows, floor, threshold):
    decisions=[]
    for row in rows:
        d=decide(row["median_fractions"]["envelope"],floor,threshold)
        truth=row["fault"]
        decisions.append({"file_id":row["file_id"],"truth":truth,**d,
                          "forced_correct":d["candidate"]==truth,
                          "accepted_correct":None if d["suggestion"] is None else d["suggestion"]==truth})
    accepted=sum(d["suggestion"] is not None for d in decisions)
    errors=sum(d["accepted_correct"] is False for d in decisions)
    return {"records":len(rows),"accepted":accepted,"incorrect_accepted":errors,
            "abstained":len(rows)-accepted,"coverage":accepted/len(rows) if rows else None,
            "retained_error":errors/accepted if accepted else None,
            "forced_errors":sum(not d["forced_correct"] for d in decisions),
            "decisions":decisions}


def fit(development):
    normal=[r for r in development if r["fault"]=="normal"]
    faults=[r for r in development if r["fault"]!="normal"]
    if len(normal)!=4 or len(faults)!=16:
        raise ValueError("Unexpected development population")
    floor=max(rank(r["median_fractions"]["envelope"])["top"] for r in normal)
    candidates=[]
    for i in range(21):
        threshold=i/20
        a=assess(faults,floor,threshold)
        candidates.append({"threshold":threshold,"accepted":a["accepted"],"incorrect_accepted":a["incorrect_accepted"]})
    valid=[r for r in candidates if r["accepted"]>=4 and r["incorrect_accepted"]==0]
    threshold=max(valid,key=lambda r:(r["accepted"],r["threshold"]))["threshold"] if valid else None
    return {"score_floor":floor,"margin_threshold":threshold,"candidates":candidates,
            "development_fault_assessment":assess(faults,floor,threshold),
            "development_normal_assessment":[{"file_id":r["file_id"],
               **decide(r["median_fractions"]["envelope"],floor,threshold)} for r in normal]}


def run(directory):
    verified=verify(ROOT)
    entry=next(r for r in verified if r["file"]=="cwru_extension_summary.json")
    dev=json.loads((ROOT/entry["file"]).read_text(encoding="utf-8"))["records"]
    if {r["file_id"] for r in dev} & {f[0] for f in FILES}:
        raise ValueError("Development and evaluation overlap")
    policy=fit(dev)
    rows=[evaluate(directory/f"{i}.mat",i,kind,diameter,load) for i,kind,diameter,load in FILES]
    assessment=assess(rows,policy["score_floor"],policy["margin_threshold"])
    return {"scope":"same_platform_severity_transfer_selective_research_suggestions_not_calibrated",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "development_blob_sha":entry["blob_sha"],"sample_rate_hz":RATE,
            "window_samples":WINDOW,"windows_per_record":WINDOWS,
            "policy":policy,"evaluation":assessment,"records":rows}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.directory)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({**result,"records":[{k:v for k,v in r.items() if k!="windows"} for r in result["records"]]},indent=2,allow_nan=False))
