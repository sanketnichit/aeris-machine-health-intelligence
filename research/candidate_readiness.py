"""Non-publishing candidate preflight. This is not release acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from research.verify_evidence import ROOT, verify
from research.technical_report import generate_report

CONDITIONAL="paderborn_conditional_summary.json"
REQUIRED={"official_summary.json","mfpt_common_mode_summary.json","cmapss_multiregime_summary.json",
          "cmapss_regime_development_summary.json","paderborn_intake_summary.json",
          "paderborn_timebase_summary.json","paderborn_cohort_summary.json",
          "paderborn_documents_summary.json",CONDITIONAL}


def validate_terminal_outcome(report):
    if (report.get("scope")!="paderborn_conditional_timing_transfer_not_calibrated_validation"
            or report.get("specimens")!=17 or report.get("recordings")!=68
            or report.get("nonpilot_recordings")!=56
            or report.get("operational_authorization") is not False
            or report.get("clock_verified") is not False
            or report.get("geometry_visually_verified") is not False):
        raise ValueError("Invalid terminal conditional study scope")
    n=report.get("complete_geometry_candidates")
    if type(n) is not int or not 0<=n<=17:
        raise ValueError("Invalid geometry denominator")
    for mode in ("nominal","stored_time"):
        row=report["overall"][mode]
        values=[row[k] for k in ("correct_accepted","incorrect_accepted","fault_abstained","normal_incorrect_accepted")]
        if (row["fault_records"]!=44 or row["normal_records"]!=24
                or any(type(v) is not int or v<0 for v in values)
                or sum(values[:3])!=44 or values[3]>24):
            raise ValueError("Invalid terminal outcome denominators")
    return "conditional_study_registered" if n else "geometry_blocked_study_registered"



def preflight(root=ROOT, require_evaluation=False):
    entries=verify(root)
    names={r["file"] for r in entries}
    missing=sorted(REQUIRED-names)
    if require_evaluation and missing:
        raise ValueError(f"Required candidate evidence missing: {missing}")
    outcome=None
    if CONDITIONAL in names:
        entry=next(r for r in entries if r["file"]==CONDITIONAL)
        data=json.loads((root/entry["file"]).read_text(encoding="utf-8"))
        outcome=validate_terminal_outcome(data)
        by_name={r["file"]:r for r in entries}
        for field,name in (("cohort_blob_sha","paderborn_cohort_summary.json"),
                           ("documents_blob_sha","paderborn_documents_summary.json"),
                           ("intake_blob_sha","paderborn_intake_summary.json"),
                           ("policy_blob_sha","mfpt_transfer_summary.json")):
            if name not in by_name or data.get(field)!=by_name[name]["blob_sha"]:
                raise ValueError("Terminal outcome source fingerprint mismatch")
    report=generate_report(root).encode("utf-8")
    return {"scope":"preflight_only_not_release_acceptance",
            "registered_evidence":len(entries),"missing_required_evidence":missing,
            "evidence_gate":not missing,"terminal_research_outcome":outcome,
            "report_sha256":hashlib.sha256(report).hexdigest(),
            "pending_gates":["full_regression","clean_extracted_archive","browser_all_pages",
                             "authenticated_fleet_review","concurrent_workload","backup_recovery",
                             "human_review_and_explicit_publication"],
            "publication_authorized":False}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-evaluation",action="store_true")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=preflight(require_evaluation=args.require_evaluation)
    result["revision"]=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    data=json.dumps(result,indent=2,allow_nan=False)+"\n"
    if args.output:
        with args.output.open("x",encoding="utf-8") as f:
            f.write(data)
    print(data,end="")
