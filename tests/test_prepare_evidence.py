import json
import shutil

import pytest

from research.prepare_evidence import prepare
from research.verify_evidence import blob_sha, verify


def fixture(tmp_path):
    root = tmp_path / "registered"
    root.mkdir()
    original = {"scope": "fixture", "revision": "a"*40,
                "run_url": "https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/1"}
    payload = json.dumps(original).encode()
    (root / "old.json").write_bytes(payload)
    manifest = {"schema_version": 1, "hash_algorithm": "git-blob-sha1",
                "files": {"old.json": {"blob_sha": blob_sha(payload), "bytes": len(payload)}}}
    (root / "manifest.json").write_text(json.dumps(manifest))
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"scope": "test only", "revision": "b"*40, "count": 5}))
    return root, source, tmp_path / "stage"


def test_staged_pair_verifies_and_original_is_unchanged(tmp_path):
    root, source, stage = fixture(tmp_path)
    original = (root / "manifest.json").read_bytes()
    entry = prepare(source, "new.json", 2, 3, "c"*64, "fixture source", stage, root)
    assert (root / "manifest.json").read_bytes() == original
    assert not (root / "new.json").exists()
    assert entry["blob_sha"] == blob_sha((stage / "new.json").read_bytes())
    shutil.copyfile(root / "old.json", stage / "old.json")
    assert len(verify(stage)) == 2
    assert json.loads((stage / "new.json").read_bytes())["count"] == 5


@pytest.mark.parametrize("name", ["old.json", "../evil.json", "manifest.json"])
def test_reject_overwrite_or_invalid_path(tmp_path, name):
    root, source, stage = fixture(tmp_path)
    with pytest.raises(ValueError):
        prepare(source, name, 2, 3, "c"*64, "fixture source", stage, root)
    assert not stage.exists()


@pytest.mark.parametrize("report", [{"scope": "test"}, {"revision": "b"*40},
                                   {"scope": "test", "revision": "b"*40, "run_url": "wrong"}])
def test_reject_missing_or_conflicting_metadata(tmp_path, report):
    root, source, stage = fixture(tmp_path)
    source.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        prepare(source, "new.json", 2, 3, "c"*64, "fixture source", stage, root)
    assert not stage.exists()


def test_existing_stage_is_not_overwritten(tmp_path):
    root, source, stage = fixture(tmp_path)
    stage.mkdir()
    with pytest.raises(FileExistsError):
        prepare(source, "new.json", 2, 3, "c"*64, "fixture source", stage, root)
