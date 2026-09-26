from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = {
    "UDI",
    "Product ID",
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
}


def test_ai4i_schema_and_shape():
    path = Path("data/ai4i2020.csv")
    if not path.exists():
        return

    df = pd.read_csv(path)

    assert df.shape[0] == 10_000
    assert set(df.columns) == EXPECTED_COLUMNS


def test_failure_label_is_binary():
    path = Path("data/ai4i2020.csv")
    if not path.exists():
        return

    df = pd.read_csv(path)
    assert set(df["Machine failure"].unique()).issubset({0, 1})


def test_model_feature_contract_excludes_target_side_fields():
    from src.features import MODEL_FEATURES

    forbidden = {
        "UDI",
        "Product ID",
        "TWF",
        "HDF",
        "PWF",
        "OSF",
        "RNF",
        "machine_failure",
    }

    assert forbidden.isdisjoint(MODEL_FEATURES)


def test_loader_normalizes_ai4i_column_names_and_reads_utf8_bom(tmp_path):
    from src.load_data import load_raw

    path = tmp_path / "ai4i2020.csv"
    pd.DataFrame(
        [
            {
                "UDI": 1,
                "Product ID": "L1",
                "Type": "L",
                "Air temperature [K]": 298.0,
                "Process temperature [K]": 308.0,
                "Rotational speed [rpm]": 1500,
                "Torque [Nm]": 40.0,
                "Tool wear [min]": 10,
                "Machine failure": 0,
                "TWF": 0,
                "HDF": 0,
                "PWF": 0,
                "OSF": 0,
                "RNF": 0,
            }
        ]
    ).to_csv(path, index=False, encoding="utf-8-sig")

    frame = load_raw(path)

    assert list(frame.columns) == [
        "udi",
        "product_id",
        "type",
        "air_temp_k",
        "process_temp_k",
        "rot_speed_rpm",
        "torque_nm",
        "tool_wear_min",
        "machine_failure",
        "twf",
        "hdf",
        "pwf",
        "osf",
        "rnf",
    ]
    assert frame.loc[0, "machine_failure"] == 0


def test_loader_reports_missing_dataset_path(tmp_path):
    from src.load_data import load_raw

    missing = tmp_path / "missing.csv"

    try:
        load_raw(missing)
    except FileNotFoundError as exc:
        assert "ai4i2020.csv" in str(exc)
    else:
        raise AssertionError("load_raw should raise FileNotFoundError for a missing dataset")


def test_validation_report_catches_basic_contract_violations():
    from src.validate_data import validate

    frame = pd.DataFrame(
        [
            {
                "udi": 1,
                "product_id": "L1",
                "type": "L",
                "air_temp_k": 300.0,
                "process_temp_k": 299.0,
                "rot_speed_rpm": 1500,
                "torque_nm": 40.0,
                "tool_wear_min": 10,
                "machine_failure": 1,
                "twf": 0,
                "hdf": 0,
                "pwf": 0,
                "osf": 0,
                "rnf": 0,
            },
            {
                "udi": 1,
                "product_id": "L1",
                "type": "X",
                "air_temp_k": 298.0,
                "process_temp_k": 308.0,
                "rot_speed_rpm": -1,
                "torque_nm": -2.0,
                "tool_wear_min": -3,
                "machine_failure": 0,
                "twf": 0,
                "hdf": 0,
                "pwf": 0,
                "osf": 0,
                "rnf": 0,
            },
        ]
    )

    report = validate(frame)

    assert "Fully duplicated rows: 0" in report
    assert "Duplicate UDI values: 1" in report
    assert "rot_speed_rpm negative: 1" in report
    assert "torque_nm negative: 1" in report
    assert "tool_wear_min negative: 1" in report
    assert "process_temp < air_temp: 1" in report
    assert "Unique type values: ['L', 'X']" in report
    assert "Rows where machine_failure disagrees with any failure-mode flag: 1" in report
    assert "Failure (1): 1 (50.00%)" in report


def test_loader_rejects_missing_required_columns(tmp_path):
    from src.load_data import load_raw

    path = tmp_path / "ai4i2020.csv"
    pd.DataFrame([{"UDI": 1, "Product ID": "L1"}]).to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )

    try:
        load_raw(path)
    except ValueError as exc:
        assert "required AI4I columns" in str(exc)
        assert "machine_failure" in str(exc)
    else:
        raise AssertionError("load_raw should reject an incomplete AI4I schema")
