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
        # The repository intentionally does not commit the benchmark CSV.
        # This test is exercised locally/CI when the dataset is provided.
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


def test_no_identifier_is_used_as_model_feature():
    model_source = Path("src/model_comparison.py").read_text(encoding="utf-8")
    assert '"UDI"' not in model_source
    assert '"Product ID"' not in model_source
    assert '"TWF"' not in model_source
    assert '"HDF"' not in model_source
    assert '"PWF"' not in model_source
    assert '"OSF"' not in model_source
    assert '"RNF"' not in model_source


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
