"""Frozen Paderborn specimen registry and bounded archive-document inventory."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.request

import rarfile
from research.paderborn_intake import SOURCE,MIRROR,MAX_ARCHIVE,inventory,fingerprint,member_bytes

REGISTRY=Path(__file__).with_name("paderborn_cohort.json")
ID=re.compile(r"K[AIB]?\d{3}|K[ABI]\d{2}")
MD5=re.compile(r"[0-9a-f]{32}")


def load_registry(path=REGISTRY):
    data=json.loads(Path(path).read_text())
    rows=data["records"]
    if len(rows)!=32 or len({r["specimen"] for r in rows})!=32:
        raise ValueError("Expected 32 distinct specimens")
    for row in rows:
        if not ID.fullmatch(row["specimen"]) or row["origin"] not in ("healthy","artificial","accelerated"):
            raise ValueError("Invalid specimen identity or origin")
        expected="primary" if row["origin"]=="healthy" or row["origin"]=="accelerated" and row["label"]!="mixed" else ("separate_artificial" if row["origin"]=="artificial" else "mixed_unresolved")
        if row["cohort"]!=expected or row["label"] not in ("normal","inner","outer","mixed"):
            raise ValueError("Invalid cohort")
        if row["mirror_md5"] is not None and not MD5.fullmatch(row["mirror_md5"]):
            raise ValueError("Invalid mirror fingerprint")
    core=[r for r in rows if r["cohort"]=="primary"]
    if len(core)!=17 or any(r["mirror_md5"] is None for r in core):
        raise ValueError("Primary cohort not fully pinned")
    return rows


def acquire_pinned(row,directory):
    specimen=row["specimen"]
    pin=row["mirror_md5"]
    if not ID.fullmatch(specimen) or not isinstance(pin,str) or not MD5.fullmatch(pin):
        raise ValueError("Acquisition requires an explicit registered pin")
    path=directory/(specimen+".rar")
    if path.exists():
        raise ValueError("Refusing to overwrite")
    errors=[]
    for url in (SOURCE+path.name,MIRROR+path.name+"?download=1"):
        partial=path.with_suffix(".partial")
        try:
            with urllib.request.urlopen(url,timeout=90) as response,partial.open("xb") as out:
                size=0
                while chunk:=response.read(1024*1024):
                    size+=len(chunk)
                    if size>MAX_ARCHIVE:
                        raise ValueError("Archive byte limit exceeded")
                    out.write(chunk)
            digest=fingerprint(partial)
            if digest["md5"]!=pin:
                raise ValueError("Mirror fingerprint mismatch")
            partial.rename(path)
            return path,{"source":url,**digest}
        except (OSError,ValueError) as exc:
            errors.append(str(exc))
            partial.unlink(missing_ok=True)
    raise ValueError(f"{specimen}: acquisition failed: {errors}")


def document_inventory(path,specimen):
    with rarfile.RarFile(path) as archive:
        files=[(i.filename,i.file_size) for i in archive.infolist() if not i.isdir()]
    measurements=inventory(specimen,files)
    documents=[]
    for name,size in files:
        if PurePosixPath(name).suffix.lower()==".mat":
            continue
        entry={"name":name,"bytes":size}
        if PurePosixPath(name).suffix.lower() in (".pdf",".txt",".csv",".xlsx",".docx") and 0<size<=20*1024*1024:
            entry["sha256"]=hashlib.sha256(member_bytes(path,name)).hexdigest()
        documents.append(entry)
    return {"inventory_measurements":len(measurements),"non_mat_members":documents,
            "geometry_verified":False}


def run(directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    rows=load_registry()
    core=[r for r in rows if r["cohort"]=="primary"]
    def inspect(row):
        path,meta=acquire_pinned(row,directory)
        try:
            return {**row,**meta,**document_inventory(path,row["specimen"])}
        finally:
            path.unlink(missing_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        out=list(pool.map(inspect,core))
    return {"scope":"paderborn_primary_cohort_archive_inventory_not_diagnostic_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "registry_sha256":hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
            "specimens":len(out),"previous_structural_pilot":sum(r["structural_pilot"] for r in out),
            "inventory_measurements":sum(r["inventory_measurements"] for r in out),
            "diagnostic_scoring_performed":False,"archives":out}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    data=json.dumps(run(a.directory),indent=2,allow_nan=False)+"\n"
    a.output.write_text(data)
    print(data,end="")
