from research.technical_report import generate_report


def test_measurement_reliability_evidence_in_generated_report():
    text = generate_report()
    for title in ("MFPT closed-cell stability refinement", "MFPT decision counterexamples",
                  "MFPT diagnostic possibility sets", "MFPT measurement width and bias",
                  "MFPT systematic-bias budget"):
        assert title in text
    assert "112/112 repeated fault assessments" in text
    assert "| False | 224 | 84 | 7 |" in text
    assert "| 1% | 70 | 0 | 140 |" in text
    assert "not sensor calibration" in text
