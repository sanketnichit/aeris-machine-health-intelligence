import importlib

MODULES = [
    "load_data",
    "features",
    "validate_data",
    "eda",
    "train_baseline",
    "model_comparison",
    "risk_model",
    "failure_mode_attribution",
    "explain_model",
    "evaluate_thresholds",
    "uncertainty_audit",
    "split_sensitivity",
    "error_analysis",
    "feature_stability",
    "calibration_audit",
    "feature_ablation",
    "models",
    "console_models",
]


def test_all_aeris_modules_import_as_package():
    for name in MODULES:
        importlib.import_module(f"src.{name}")
