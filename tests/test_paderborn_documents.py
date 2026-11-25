from research.paderborn_documents import technical_candidates,summarize_fields


def test_named_unit_fields_and_page_provenance():
    text="Number of rolling elements    -    8\nPitch circle diameter mm 29,05\nRolling element diameter mm 6.75\nPressure angle deg 0\f"
    out=summarize_fields(technical_candidates(text))
    assert [out[k]["value"] for k in ("rolling_elements","pitch_diameter_mm","element_diameter_mm","angle_deg")]==[8,29.05,6.75,0]
    assert out["pitch_diameter_mm"]["candidates"][0]["page"]==1


def test_unrelated_or_wrong_unit_not_inferred():
    text="Outer diameter mm 40\nPitch circle diameter cm 2.9\nContact angle 15 20\n"
    out=summarize_fields(technical_candidates(text))
    assert all(v["status"]=="unresolved" for v in out.values())


def test_duplicate_equal_values_vs_conflicting_candidates():
    text="Pitch circle diameter mm 29.05\fPitch circle diameter mm 28.55\nNumber of balls 8\nNumber of balls 8"
    out=summarize_fields(technical_candidates(text))
    assert out["pitch_diameter_mm"]["status"]=="conflicting_candidates"
    assert out["pitch_diameter_mm"]["value"] is None
    assert out["rolling_elements"]["value"]==8
