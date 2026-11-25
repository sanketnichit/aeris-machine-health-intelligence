import hashlib
import json
import zipfile

import pytest

from scripts.verify_candidate_bundle import verify_bundle, REQUIRED_SOURCE

REV="a"*40
NAME=f"aeris-candidate-{REV[:12]}.zip"


def sums(root):
    files=sorted(p for p in root.iterdir() if p.name!="SHA256SUMS")
    (root/"SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files))


@pytest.fixture
def bundle(tmp_path):
    (tmp_path/"revision.txt").write_text(REV+"\n")
    report=tmp_path/"AERIS_technical_report.md"
    report.write_text("fixture report\n")
    (tmp_path/"environment.txt").write_text("fixture==1\n")
    (tmp_path/"readiness.json").write_text(json.dumps({
        "scope":"preflight_only_not_release_acceptance","revision":REV,"publication_authorized":False,
        "evidence_gate":True,"report_sha256":hashlib.sha256(report.read_bytes()).hexdigest(),
        "registered_evidence":25}))
    with zipfile.ZipFile(tmp_path/NAME,"w") as archive:
        for name in REQUIRED_SOURCE:
            archive.writestr(f"aeris-candidate-{REV[:12]}/{name}","fixture")
    sums(tmp_path)
    return tmp_path


def test_valid_candidate_integrity_is_not_publication(bundle):
    out=verify_bundle(bundle,REV)
    assert out["verified_files"]==5 and out["registered_evidence"]==25
    assert not out["publication_authorized"]


def test_wrong_expected_revision(bundle):
    with pytest.raises(ValueError,match="revision"):
        verify_bundle(bundle,"b"*40)


def test_modified_report_fails(bundle):
    (bundle/"AERIS_technical_report.md").write_text("tampered")
    with pytest.raises(ValueError,match="checksum"):
        verify_bundle(bundle)


def test_rehashed_report_still_mismatches_readiness(bundle):
    (bundle/"AERIS_technical_report.md").write_text("changed")
    sums(bundle)
    with pytest.raises(ValueError,match="provenance"):
        verify_bundle(bundle)


def test_unsafe_archive_path_rejected_even_if_rehashed(bundle):
    with zipfile.ZipFile(bundle/NAME,"a") as archive:
        archive.writestr("../outside.txt","unsafe")
    sums(bundle)
    with pytest.raises(ValueError,match="Unsafe"):
        verify_bundle(bundle)


def test_unexpected_bundle_file_rejected(bundle):
    (bundle/"extra.txt").write_text("extra")
    with pytest.raises(ValueError,match="Unexpected"):
        verify_bundle(bundle)
