"""Non-publishing candidate preflight. This is not release acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from research.verify_evidence import ROOT, verify
from research.technical_report import generate_report

REQUIRED={"official_summary.json","mfpt_common_mode_summary.json","cmapss_multiregime_summary.json"}


def preflight(root=ROOT, require_evaluation=False):
    entries=verify(root)
    names={r["file"] for r in entries}
    missing=sorted(REQUIRED-names)
    if require_evaluation and missing:
        raise ValueError(f"Required candidate evidence missing: {missing}")
    report=generate_report(root).encode("utf-8")
    return {"scope":"preflight_only_not_release_acceptance",
            "registered_evidence":len(entries),"missing_required_evidence":missing,
            "evidence_gate":not missing,
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
