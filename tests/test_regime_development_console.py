from src.multiregime_console import development_rows


def test_development_table_keeps_undefined_retained_metrics():
    data={"scenarios":[{"source":"FD001","target":"FD003","landmark":50,
        "calibration_survivors":20,"endpoints":20,"support_rejected":1,
        "accepted":0,"coverage":0.,"metrics":{"regime":{"mae":25.}},
        "raw_interval_coverage":.8,"accepted_interval_coverage":None,
        "accepted_mae":None,"reasons":{"declared_domain_mismatch":20}}]}
    rows=development_rows(data,"FD001","FD003")
    assert rows.iloc[0]["Accepted forecasts"]==0
    assert rows.iloc[0]["Accepted MAE"] is None
    assert rows.iloc[0]["Raw interval coverage"]==.8
    assert "declared_domain_mismatch" in rows.iloc[0]["Reasons"]
