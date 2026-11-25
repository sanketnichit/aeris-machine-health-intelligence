from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.evidence_console import read_report
from src.measurement_console import measurement_rows, bias_rows, possibility_rows, witness_counts, fusion_rows


def test_measurement_width_rows_preserve_counts_and_containment():
    report = read_report("mfpt_measurement_width_summary.json")
    rows = measurement_rows(report, -.05)
    assert len(rows) == 6
    assert (rows.Correct + rows.Incorrect + rows.Withheld == 14).all()
    assert rows.iloc[0].Incorrect == 5
    assert not bool(rows.iloc[0]["Reference contained"])
    assert rows["Width (%)"].is_monotonic_increasing


def test_bias_rows_use_actual_denominators():
    rows = bias_rows(read_report("mfpt_bias_budget_summary.json"))
    assert rows.Correct.tolist() == [115, 70, 0]
    assert rows.Incorrect.tolist() == [6, 0, 0]
    assert (rows.Correct + rows.Incorrect + rows.Withheld == rows["Fault assessments"]).all()


def test_outer_set_table_preserves_counts():
    rows = possibility_rows(read_report("mfpt_possibility_summary.json"))
    assert rows[[f"Size {i}" for i in range(4)]].sum().tolist() == [37, 91, 32, 10]
    assert rows["Normal nonempty sets"].sum() == 0


def test_counterexample_summary_preserves_witness_groups():
    counts = witness_counts(read_report("mfpt_counterexample_summary.json"))
    assert counts["nominal_correct"] == {"abstention": 51, "competing_suggestion": 6}


def test_measurement_workspace_all_audits():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=30).run()
    app.sidebar.radio(key="research_page").set_value("MFPT measurement reliability").run()
    assert not app.exception
    assert any(m.label == "Recovered correct suggestions" and m.value == "6" for m in app.metric)
    for choice in ("Counterexamples", "Diagnostic possibilities", "Measurement width", "Systematic bias", "Two-channel fusion"):
        app.radio(key="mfpt_measurement_audit").set_value(choice).run()
        assert not app.exception
    app.radio(key="mfpt_measurement_audit").set_value("Measurement width").run()
    app.selectbox(key="mfpt_measurement_error").set_value(-.05).run()
    assert not app.exception
    assert any("biased reading" in w.value for w in app.warning)


def test_fusion_rows_expose_false_agreement():
    rows = fusion_rows(read_report("mfpt_measurement_fusion_summary.json"))
    assert rows["Fused correct"].sum() == 348
    assert rows["Fused incorrect"].sum() == 0
    assert rows["Accepted outside reference"].sum() == 74
    shared = rows.loc[rows["Secondary mode"] == "shared_bias"].iloc[0]
    assert shared["Compatible outside reference"] == 136
    assert shared["Conflicts"] == 0
