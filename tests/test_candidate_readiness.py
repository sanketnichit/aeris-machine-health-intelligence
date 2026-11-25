from pathlib import Path

import pytest

from research.candidate_readiness import preflight
from research.verify_evidence import verify


def test_candidate_preflight_does_not_authorize_publication():
    result=preflight()
    assert result["registered_evidence"]==len(verify())
    assert not result["publication_authorized"]
    assert "clean_extracted_archive" in result["pending_gates"]
    assert len(result["report_sha256"])==64
    if result["missing_required_evidence"]:
        with pytest.raises(ValueError,match="missing"):
            preflight(require_evaluation=True)
    else:
        assert preflight(require_evaluation=True)["evidence_gate"]


def test_candidate_workflow_has_no_publication_permission():
    root=Path(__file__).resolve().parents[1]
    workflow=(root/".github/workflows/next-candidate-acceptance.yml").read_text()
    assert "contents: read" in workflow
    assert "contents: write" not in workflow
    assert "gh release" not in workflow
    assert "candidate_readiness --require-evaluation" in workflow
    assert "git rev-parse --short=12 HEAD" in workflow
