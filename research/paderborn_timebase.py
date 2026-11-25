"""Read actual Paderborn timing metadata on the exact registered pilot records."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import concurrent.futures

import rarfile
from scipy.io import loadmat
from research.verify_evidence import ROOT,verify
from research.paderborn_intake import acquire,inventory,member_bytes,PINS,named_channels
from src.recording_timebase import inspect_record


def run(directory):
    entries={x["file"]:x for x in verify(ROOT)}
    prior=entries["paderborn_intake_summary.json"]
    old=json.loads((ROOT/prior["file"]).read_text())
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        acquired=list(pool.map(lambda s:acquire(s,directory),PINS))
    rows=[]
    for source in acquired:
        specimen=source["specimen"]
        expected=next(x for x in old["archives"] if x["specimen"]==specimen)
        if source["sha256"]!=expected["sha256"]:
            raise ValueError("Registered archive changed")
        path=directory/(specimen+".rar")
        with rarfile.RarFile(path) as archive:
            found=inventory(specimen,[(i.filename,i.file_size) for i in archive.infolist() if not i.isdir()])
        for prev in expected["selected_recordings"]:
            name=prev["filename"]
            raw=member_bytes(path,found[name])
            if hashlib.sha256(raw).hexdigest()!=prev["sha256"]:
                raise ValueError("Registered recording changed")
            record=loadmat(io.BytesIO(raw),simplify_cells=True)[Path(name).stem]
            if named_channels(record)["sample_count"]!=prev["sample_count"]:
                raise ValueError("Registered sample count changed")
            rows.append({"specimen":specimen,"filename":name,"sha256":prev["sha256"],
                         **inspect_record(record)})
    return {"scope":"paderborn_timebase_metadata_audit_not_calibration_or_diagnostic_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "intake_blob_sha":prior["blob_sha"],"recordings":len(rows),"records":rows,
            "diagnostic_scoring_performed":False,"operational_authorization":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.directory)
    data=json.dumps(result,indent=2,allow_nan=False)+"\n"
    a.output.write_text(data)
    print(data,end="")
