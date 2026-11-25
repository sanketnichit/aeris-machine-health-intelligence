"""Paderborn source intake: fixed archives and named-channel structural audit.

No fault scoring, threshold fitting or raw third-party artifact publication.
"""
import argparse
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import urllib.request

import numpy as np
import rarfile
from scipy.io import loadmat

SOURCE="https://groups.uni-paderborn.de/kat/BearingDataCenter/"
MIRROR="https://zenodo.org/records/15845309/files/"
PINS={"K001":"af6dc58283d356cd438e7738a2d525b8",
      "KA04":"f87503ed69a624ba6e1d9e573e6c09fb",
      "KI04":"a5a634fcdcb33a8501e7411d30441c6d"}
CONDITIONS=("N15_M07_F10","N09_M07_F10","N15_M01_F10","N15_M07_F04")
MAX_ARCHIVE=220*1024*1024
MAX_MEMBER=20*1024*1024
EXPECTED_SAMPLES=256000


def fingerprint(path):
    sha=hashlib.sha256()
    md5=hashlib.md5(usedforsecurity=False)
    size=0
    with Path(path).open("rb") as handle:
        while chunk:=handle.read(1024*1024):
            size+=len(chunk)
            if size>MAX_ARCHIVE:
                raise ValueError("Archive exceeds byte limit")
            sha.update(chunk); md5.update(chunk)
    return {"sha256":sha.hexdigest(),"md5":md5.hexdigest(),"bytes":size}


def acquire(specimen,directory):
    if specimen not in PINS:
        raise ValueError("Unregistered specimen")
    path=Path(directory)/(specimen+".rar")
    if path.exists():
        raise ValueError("Refusing to overwrite an archive")
    # Use publisher source; pinned mirror is a separate fallback source.
    errors=[]
    for url in (SOURCE+path.name,MIRROR+path.name+"?download=1"):
        partial=path.with_suffix(".partial")
        try:
            with urllib.request.urlopen(url,timeout=60) as response, partial.open("xb") as out:
                size=0
                while chunk:=response.read(1024*1024):
                    size+=len(chunk)
                    if size>MAX_ARCHIVE:
                        raise ValueError("Archive exceeds byte limit")
                    out.write(chunk)
            digest=fingerprint(partial)
            if digest["md5"]!=PINS[specimen]:
                raise ValueError("Archive differs from versioned mirror fingerprint")
            partial.rename(path)
            return {"specimen":specimen,"source":url,**digest}
        except (OSError,ValueError) as exc:
            errors.append(f"{url}: {exc}")
            partial.unlink(missing_ok=True)
    raise ValueError("Source acquisition failed: "+"; ".join(errors))


def inventory(specimen,members):
    """Select exact expected basenames; never extract arbitrary paths."""
    expected={f"{condition}_{specimen}_{i}.mat" for condition in CONDITIONS for i in range(1,21)}
    found={}
    for name,size in members:
        if not isinstance(name,str) or "\\" in name:
            raise ValueError("Unexpected archive path")
        p=PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or ":" in name:
            raise ValueError("Unsafe archive path")
        if p.suffix.lower()!=".mat":
            continue
        if p.name not in expected or p.name in found or not 0<size<=MAX_MEMBER:
            raise ValueError("Unexpected, duplicate or oversized MAT member")
        found[p.name]=name
    if set(found)!=expected:
        raise ValueError("Incomplete expected measurement inventory")
    return found


def member_bytes(path,name):
    # stdout-only extraction: never writes arbitrary archive members to disk.
    run=subprocess.run(["bsdtar","-xOf",str(path),"--",name],capture_output=True,check=True,timeout=90)
    if not 0<len(run.stdout)<=MAX_MEMBER:
        raise ValueError("Unexpected extracted member size")
    return run.stdout


def named_channels(record):
    if not isinstance(record,dict) or "Y" not in record:
        raise ValueError("Missing expected Y channel structure")
    y=record["Y"]
    channels=[y] if isinstance(y,dict) else list(y)
    if any(not isinstance(c,dict) or not isinstance(c.get("Name"),str) for c in channels):
        raise ValueError("Invalid channel metadata")
    names=[c["Name"] for c in channels]
    if len(set(names))!=len(names):
        raise ValueError("Duplicate channel names")
    matches=[c for c in channels if c["Name"]=="vibration_1"]
    if len(matches)!=1:
        raise ValueError("Exactly one vibration_1 channel required")
    a=np.asarray(matches[0]["Data"])
    if a.ndim!=1 or np.iscomplexobj(a) or not np.issubdtype(a.dtype,np.number):
        raise ValueError("Expected real one-dimensional vibration data")
    if not 2<=len(a)<=1_000_000 or not np.isfinite(a).all() or np.min(a)==np.max(a):
        raise ValueError("Invalid or excessive vibration samples")
    return {"channel_names":names,"vibration_name":"vibration_1","sample_count":len(a),
            "unit_metadata":str(matches[0].get("Unit","not_present")),
            "raster_metadata":str(matches[0].get("Raster","not_present")),
            "finite_nonconstant":True,"expected_nominal_samples":EXPECTED_SAMPLES,
            "nominal_sample_count_matches":len(a)==EXPECTED_SAMPLES}


def inspect_mat(raw,filename):
    data=loadmat(io.BytesIO(raw),simplify_cells=True)
    key=Path(filename).stem
    if set(k for k in data if not k.startswith("__"))!={key}:
        raise ValueError("MAT identity does not match filename")
    return named_channels(data[key])


def inspect_archive(directory,entry):
    specimen=entry["specimen"]
    path=Path(directory)/(specimen+".rar")
    actual=fingerprint(path)
    if any(actual[k]!=entry[k] for k in ("sha256","md5","bytes")):
        raise ValueError("Archive fingerprint mismatch")
    with rarfile.RarFile(path) as archive:
        files=[(i.filename,i.file_size) for i in archive.infolist() if not i.isdir()]
        found=inventory(specimen,files)
    records=[]
    for condition in CONDITIONS:
        name=f"{condition}_{specimen}_1.mat"
        raw=member_bytes(path,found[name])
        records.append({"filename":name,"condition":condition,"sha256":hashlib.sha256(raw).hexdigest(),
                        **inspect_mat(raw,name)})
    return {**entry,"inventory_measurements":len(found),"selected_recordings":records,
            "diagnostic_scoring_performed":False}


def run(directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        entries=list(pool.map(lambda specimen:acquire(specimen,directory),PINS))
    rows=[inspect_archive(directory,e) for e in entries]
    return {"scope":"paderborn_source_intake_structural_only_not_diagnostic_validation",
            "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "publisher":"Paderborn University KAt Bearing DataCenter",
            "source_license":"CC BY-NC 4.0 (original publisher terms)",
            "mirror_doi":"10.5281/zenodo.15845309",
            "specimens":len(rows),"inventory_measurements":sum(r["inventory_measurements"] for r in rows),
            "inspected_recordings":sum(len(r["selected_recordings"]) for r in rows),
            "diagnostic_scoring_performed":False,
            "nominal_sample_count_mismatches":sum(not x["nominal_sample_count_matches"] for row in rows for x in row["selected_recordings"]),
            "archives":rows}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=run(args.directory)
    payload=json.dumps(report,indent=2,allow_nan=False)+"\n"
    args.output.write_text(payload,encoding="utf-8")
    print(payload,end="")
