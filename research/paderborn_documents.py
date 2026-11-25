"""Source-pinned document extraction candidates; never authorizes geometry.

Extract only bounded technical field candidates, not entire third-party PDFs.
Layout extraction is not a substitute for visual review of the actual table.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess

from research.verify_evidence import ROOT,verify
from research.paderborn_cohort import acquire_pinned,load_registry
from research.paderborn_intake import member_bytes

FIELDS={
    "rolling_elements":r"(?:number of (?:rolling elements|balls)|rolling element count)",
    "pitch_diameter_mm":r"(?:pitch circle diameter|pitch diameter)",
    "element_diameter_mm":r"(?:rolling element diameter|ball diameter|diameter of rolling elements)",
    "angle_deg":r"(?:pressure angle|contact angle)",
}
NUMBER=r"[-+]?(?:\d+(?:[.,]\d+)?|[.,]\d+)"
UNITS={"rolling_elements":r"(?:[-–—]|pcs\.?|pieces)?",
       "pitch_diameter_mm":r"mm","element_diameter_mm":r"mm","angle_deg":r"(?:°|deg(?:ree)?s?\.?)"}
LOG_FIELDS={
    "sampling_rate":r"sampling (?:rate|frequency)|sample rate",
    "duration":r"measurement duration|recording duration|measuring time",
    "clock":r"clock|timebase|time base|timestamp|time stamp|synchroni[sz]",
}


def technical_candidates(text):
    result={k:[] for k in FIELDS}
    for page,content in enumerate(text.split("\f"),1):
        for line_no,line in enumerate(content.splitlines(),1):
            for key,label in FIELDS.items():
                # A single numeric value following the named field and unit.
                match=re.search(r"\b"+label+r"\b\s*[:;]?\s*"+UNITS[key]+r"\s*[:;]?\s*("+NUMBER+r")\s*$",line,re.I)
                if match:
                    value=float(match.group(1).replace(",","."))
                    result[key].append({"page":page,"line":line_no,"value":value,
                                        "label":match.group(0)[:120]})
    return result


def summarize_fields(candidates):
    out={}
    for key,items in candidates.items():
        values=sorted({i["value"] for i in items})
        out[key]={"status":"unique_candidate" if len(values)==1 else "unresolved" if not values else "conflicting_candidates",
                  "value":values[0] if len(values)==1 else None,"candidates":items}
    return out


def extract_text(raw):
    if not isinstance(raw,bytes) or not raw.startswith(b"%PDF-") or len(raw)>2_000_000:
        raise ValueError("Invalid or oversized source PDF")
    result=subprocess.run(["pdftotext","-layout","-","-"],input=raw,capture_output=True,check=True,timeout=30)
    if len(result.stdout)>2_000_000:
        raise ValueError("Extracted document text exceeds limit")
    return result.stdout.decode("utf-8")


def document_summary(raw,kind):
    text=extract_text(raw)
    pages=[p for p in text.split("\f") if p.strip()]
    return {"text_pages":len(pages),"text_extraction_nonempty":bool(text.strip()),
            "geometry":summarize_fields(technical_candidates(text)) if kind=="fact_sheet" else {},
            "acquisition_keyword_pages":{k:[i for i,p in enumerate(text.split("\f"),1) if re.search(pattern,p,re.I)]
                                          for k,pattern in LOG_FIELDS.items()},
            "visual_review_completed":False,"geometry_verified":False,"clock_verified":False}


def run(directory):
    entries={x["file"]:x for x in verify(ROOT)}
    prior=entries["paderborn_cohort_summary.json"]
    old=json.loads((ROOT/prior["file"]).read_text())
    rows=load_registry()
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    def inspect(expected):
        row=next(r for r in rows if r["specimen"]==expected["specimen"])
        path,meta=acquire_pinned(row,directory)
        try:
            if meta["sha256"]!=expected["sha256"]:
                raise ValueError("Registered archive changed")
            out=[]
            for kind,name in (("fact_sheet",row["specimen"]+".pdf"),("measurement_log","measuring_log_"+row["specimen"]+".pdf")):
                candidates=[x for x in expected["non_mat_members"] if Path(x["name"]).name==name]
                if len(candidates)!=1:
                    raise ValueError("Expected unique pinned document")
                entry=candidates[0]
                raw=member_bytes(path,entry["name"])
                if hashlib.sha256(raw).hexdigest()!=entry["sha256"] or len(raw)!=entry["bytes"]:
                    raise ValueError("Document fingerprint mismatch")
                out.append({"kind":kind,"name":entry["name"],"sha256":entry["sha256"],**document_summary(raw,kind)})
            return {"specimen":row["specimen"],"documents":out}
        finally:
            path.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        out=list(pool.map(inspect,old["archives"]))
    return {"scope":"paderborn_document_geometry_candidates_not_verified_geometry_or_calibration",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "cohort_blob_sha":prior["blob_sha"],"specimens":len(out),
            "documents":sum(len(x["documents"]) for x in out),"specimen_records":out,
            "geometry_verified_specimens":0,"diagnostic_scoring_performed":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=run(a.directory)
    data=json.dumps(report,indent=2,allow_nan=False)+"\n"
    a.output.write_text(data,encoding="utf-8")
    print(data,end="")
