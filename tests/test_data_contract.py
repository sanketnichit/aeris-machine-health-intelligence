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
