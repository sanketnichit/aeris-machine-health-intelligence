"""Local immutable capture-advisory review journal, separate from fleet control.

Only computed offline advisories are inserted. Manual review is a record of
inspection, not acceptance of a diagnosis or authorization to act.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from research.capture_advisory import evaluate_capture, load_pins
from src.capture_archive import load_capture, CAPTURE_ID
from src.calibration_provenance import HEX

MAX_RECORDS=1000
MAX_REPORT_BYTES=1_000_000


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")


def now():
    return datetime.now(timezone.utc).isoformat()


def connect(path):
    db=sqlite3.connect(path,timeout=10)
    db.row_factory=sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("""CREATE TABLE IF NOT EXISTS advisories (
            advisory_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL, capture_id TEXT NOT NULL,
            context_sha256 TEXT NOT NULL, report BLOB NOT NULL, created_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS reviews (
            advisory_id TEXT PRIMARY KEY REFERENCES advisories(advisory_id),
            reviewed_at TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT NOT NULL
        )""")
        db.commit()
        return db
    except BaseException:
        db.close()
        raise


def readonly(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro",uri=True,timeout=10)
    db.row_factory=sqlite3.Row
    return db


def identity(asset,capture,context,payload):
    return hashlib.sha256(canonical([asset,capture,context,hashlib.sha256(payload).hexdigest()])).hexdigest()


def verified(row):
    raw=row["report"]
    if identity(row["asset_id"],row["capture_id"],row["context_sha256"],raw)!=row["advisory_id"]:
        raise ValueError("Advisory journal fingerprint mismatch")
    report=json.loads(raw)
    if report.get("scope")!="research_advisory_only" or report.get("operational_authorization") is not False:
        raise ValueError("Invalid advisory scope")
    return report


def analyze_and_record(journal,archive,capture_id,context_sha256,trusted_pins):
    if Path(journal).resolve()==Path(archive).resolve():
        raise ValueError("Journal and capture archive must be separate")
    if not isinstance(context_sha256,str) or not HEX.fullmatch(context_sha256):
        raise ValueError("Invalid context fingerprint")
    raw,analysis=load_capture(archive,capture_id)
    report=evaluate_capture(capture_id,raw,analysis,context_sha256,load_pins(trusted_pins))
    if report.get("scope")!="research_advisory_only" or report.get("operational_authorization") is not False:
        raise ValueError("Unexpected advisory scope")
    payload=canonical(report)
    if len(payload)>MAX_REPORT_BYTES:
        raise ValueError("Advisory report exceeds journal limit")
    asset=analysis["asset_id"]
    ident=identity(asset,capture_id,context_sha256,payload)
    with closing(connect(journal)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        old=db.execute("SELECT * FROM advisories WHERE advisory_id=?",(ident,)).fetchone()
        if old is not None:
            verified(old)
            return {"advisory_id":ident,"created":False,"report":report}
        if db.execute("SELECT COUNT(*) FROM advisories").fetchone()[0]>=MAX_RECORDS:
            raise ValueError("Advisory journal full; no historical entries removed")
        db.execute("INSERT INTO advisories VALUES (?,?,?,?,?,?)",
                   (ident,asset,capture_id,context_sha256,payload,now()))
    return {"advisory_id":ident,"created":True,"report":report}


def list_advisories(journal,limit=100):
    if type(limit) is not int or not 1<=limit<=MAX_RECORDS:
        raise ValueError("Invalid journal limit")
    with closing(readonly(journal)) as db:
        rows=db.execute("""SELECT a.*,r.reviewed_at,r.reviewer,r.note
            FROM advisories a LEFT JOIN reviews r USING(advisory_id)
            ORDER BY a.created_at DESC,a.advisory_id LIMIT ?""",(limit,)).fetchall()
        return [{"advisory_id":r["advisory_id"],"asset_id":r["asset_id"],
                 "capture_id":r["capture_id"],"context_sha256":r["context_sha256"],
                 "created_at":r["created_at"],"report":verified(r),
                 "review_status":"reviewed" if r["reviewed_at"] else "pending",
                 "review":None if not r["reviewed_at"] else
                     {"reviewed_at":r["reviewed_at"],"reviewer":r["reviewer"],"note":r["note"]}}
                for r in rows]


def record_review(journal,advisory_id,reviewer,note):
    if not isinstance(advisory_id,str) or not HEX.fullmatch(advisory_id):
        raise ValueError("Invalid advisory identity")
    if any(not isinstance(v,str) or not v.strip() or len(v)>maximum or not v.isprintable()
           for v,maximum in ((reviewer,128),(note,500))):
        raise ValueError("Reviewer and printable review note required")
    if not Path(journal).is_file():
        raise ValueError("Unknown journal")
    with closing(connect(journal)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT * FROM advisories WHERE advisory_id=?",(advisory_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown advisory")
        verified(row)
        if db.execute("SELECT 1 FROM reviews WHERE advisory_id=?",(advisory_id,)).fetchone():
            raise ValueError("Advisory already reviewed; original review preserved")
        db.execute("INSERT INTO reviews VALUES (?,?,?,?)",(advisory_id,now(),reviewer.strip(),note.strip()))
    return {"advisory_id":advisory_id,"review_status":"reviewed","operational_authorization":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal",type=Path,required=True)
    sub=parser.add_subparsers(dest="command",required=True)
    add=sub.add_parser("analyze")
    add.add_argument("--archive",type=Path,required=True)
    add.add_argument("--capture-id",required=True)
    add.add_argument("--context-sha256",required=True)
    add.add_argument("--trusted-pins",type=Path,required=True)
    listing=sub.add_parser("list")
    listing.add_argument("--limit",type=int,default=100)
    review=sub.add_parser("review")
    review.add_argument("--advisory-id",required=True)
    review.add_argument("--reviewer",required=True)
    review.add_argument("--note",required=True)
    args=parser.parse_args()
    if args.command=="analyze":
        result=analyze_and_record(args.journal,args.archive,args.capture_id,args.context_sha256,args.trusted_pins)
    elif args.command=="list":
        result=list_advisories(args.journal,args.limit)
    else:
        result=record_review(args.journal,args.advisory_id,args.reviewer,args.note)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
