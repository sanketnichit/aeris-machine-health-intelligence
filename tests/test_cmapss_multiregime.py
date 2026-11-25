import hashlib
import io
import zipfile

import numpy as np
import pandas as pd
import pytest

import scripts.download_cmapss_all as acquisition
from research.cmapss_multiregime import fit_candidates, predict, POPULATIONS
from src.prognostics import COLUMNS


def test_archive_hash_rejects_unknown_bytes():
    with pytest.raises(ValueError,match="fingerprint"):
        acquisition.extract(b"not a NASA archive")


def archive_bytes(duplicate=False):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as z:
        for name in acquisition.NAMES:
            z.writestr("dataset/"+name,name.encode())
        if duplicate:
            z.writestr("duplicate/"+acquisition.NAMES[0],b"duplicate")
    return buf.getvalue()


def test_explicit_member_selection(monkeypatch):
    raw=archive_bytes()
    monkeypatch.setattr(acquisition,"ARCHIVE_SHA256",hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(acquisition,"HASHES",{n:hashlib.sha256(n.encode()).hexdigest() for n in acquisition.NAMES[:3]})
    assert acquisition.extract(raw)=={n:n.encode() for n in acquisition.NAMES}


def test_duplicate_member_is_rejected(monkeypatch):
    raw=archive_bytes(True)
    monkeypatch.setattr(acquisition,"ARCHIVE_SHA256",hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError,match="duplicate"):
        acquisition.extract(raw)


def frame(lengths):
    rows=[]
    for unit,length in enumerate(lengths,1):
        for cycle in range(1,length+1):
            rows.append([unit,cycle,0.,0.,0.]+[float(cycle+j+unit) for j in range(21)])
    return pd.DataFrame(rows,columns=COLUMNS)


def test_frozen_candidates_produce_one_nonnegative_endpoint_per_unit():
    train=frame([12,16,20,24])
    test=frame([5,8])
    fitted=fit_candidates(train)
    units,age,values=predict(fitted,test)
    assert units.tolist()==[1,2] and age.tolist()==[5,8]
    assert set(values)=={"age_reference","constant","snapshot_hgb","relative_hgb","adaptive_mean"}
    assert all(v.shape==(2,) and np.isfinite(v).all() and (v>=0).all() for v in values.values())
    assert np.array_equal(values["adaptive_mean"],values["age_reference"])


def test_population_denominators():
    assert sum(n[1] for n in POPULATIONS.values())==707
    assert sum(n[1] for s,n in POPULATIONS.items() if s!="FD001")==607
