from pathlib import Path

import pytest

from research.candidate_readiness import preflight,validate_terminal_outcome,CONDITIONAL
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


def test_final_gate_requires_terminal_research_outcome():
    result=preflight()
    names={r["file"] for r in verify()}
    if CONDITIONAL not in names:
        assert CONDITIONAL in result["missing_required_evidence"]
        assert result["terminal_research_outcome"] is None
    else:
        assert result["terminal_research_outcome"] in ("conditional_study_registered","geometry_blocked_study_registered")


def test_blocked_study_is_not_scientific_success_or_operational_permission():
    counts={"fault_records":44,"normal_records":24,"correct_accepted":0,
            "incorrect_accepted":0,"fault_abstained":44,"normal_incorrect_accepted":0}
    report={"scope":"paderborn_conditional_timing_transfer_not_calibrated_validation",
            "specimens":17,"recordings":68,"nonpilot_recordings":56,
            "operational_authorization":False,"clock_verified":False,"geometry_visually_verified":False,
            "complete_geometry_candidates":0,"overall":{"nominal":counts,"stored_time":counts}}
    assert validate_terminal_outcome(report)=="geometry_blocked_study_registered"
    report["operational_authorization"]=True
    with pytest.raises(ValueError,match="scope"):
        validate_terminal_outcome(report)
