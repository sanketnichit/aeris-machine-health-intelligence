import json

import pytest

from research.verify_evidence import blob_sha, parse, verify


def test_published_evidence_manifest():
    records = verify()
    assert len(records) >= 6
    assert any(r["file"] == "official_summary.json" for r in records)


def fixture(root):
    report = {"scope": "Example only", "revision": "a"*40,
              "run_url": "https://github.com/sanketnichit/aeris-machine-health-intelligence/actions/runs/1"}
    payload = json.dumps(report).encode()
    (root/"report.json").write_bytes(payload)
    (root/"manifest.json").write_text(json.dumps({"schema_version":1,"hash_algorithm":"git-blob-sha1",
        "files":{"report.json":{"blob_sha":blob_sha(payload),"bytes":len(payload)}}}),encoding="utf-8")


def test_modified_evidence_rejected(tmp_path):
    fixture(tmp_path)
    assert len(verify(tmp_path)) == 1
    path = tmp_path/"report.json"
    path.write_bytes(path.read_bytes().replace(b"Example",b"Changed"))
    with pytest.raises(ValueError,match="fingerprint mismatch"):
        verify(tmp_path)


def test_unregistered_evidence_rejected(tmp_path):
    fixture(tmp_path)
    (tmp_path/"unregistered.json").write_text("{}")
    with pytest.raises(ValueError,match="Unregistered"):
        verify(tmp_path)


@pytest.mark.parametrize("payload", [b'{"a":1,"a":2}', b'{"a":NaN}'])
def test_reject_ambiguous_json(payload):
    with pytest.raises(ValueError):
        parse(payload)
