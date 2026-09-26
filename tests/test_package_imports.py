import importlib

CORE_MODULES = [
    "load_data",
    "features",
    "validate_data",
    "eda",
    "train_baseline",
    "risk_model",
    "explain_model",
    "models",
    "console_models",
]


def test_all_core_aeris_modules_import_as_package():
    for name in CORE_MODULES:
        importlib.import_module(f"src.{name}")
