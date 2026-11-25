from collections import Counter
import json
import pytest
from research.paderborn_cohort import load_registry,REGISTRY


def test_registry_partitions_all_publisher_specimens():
    rows=load_registry()
    assert Counter(r["cohort"] for r in rows)=={"primary":17,"separate_artificial":12,"mixed_unresolved":3}
    assert Counter(r["label"] for r in rows if r["cohort"]=="primary")=={"normal":6,"outer":5,"inner":6}
    assert [r["specimen"] for r in rows if r["mirror_md5"] is None]==["KA08"]
    assert sum(r["structural_pilot"] for r in rows)==3


def test_missing_primary_pin_fails(tmp_path):
    doc=json.loads(REGISTRY.read_text())
    doc["records"][0]["mirror_md5"]=None
    path=tmp_path/"registry.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match="fully pinned"):
        load_registry(path)


def test_mixed_specimen_cannot_enter_primary(tmp_path):
    doc=json.loads(REGISTRY.read_text())
    next(r for r in doc["records"] if r["specimen"]=="KB24")["cohort"]="primary"
    path=tmp_path/"registry.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match="cohort"):
        load_registry(path)
