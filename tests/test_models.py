from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline

from src.models import (
    HGB_PARAMS,
    MODE_HGB_PARAMS,
    build_calibrated_hgb,
    build_hgb_pipeline,
    build_mode_pipeline,
    build_preprocessor,
)


def test_canonical_preprocessor_contract():
    pre = build_preprocessor()
    assert list(pre.transformers[0][2]) == ["type"]


def test_preprocessor_supports_feature_override():
    raw_features = [
        "type",
        "air_temp_k",
        "process_temp_k",
        "rot_speed_rpm",
        "torque_nm",
        "tool_wear_min",
    ]
    pre = build_preprocessor(raw_features)
    assert list(pre.transformers[1][2]) == raw_features[1:]


def test_canonical_hgb_pipeline_contract():
    pipe = build_hgb_pipeline()
    assert isinstance(pipe, Pipeline)
    assert isinstance(pipe.named_steps["model"], HistGradientBoostingClassifier)
    assert pipe.named_steps["model"].get_params()["max_iter"] == HGB_PARAMS["max_iter"]
    assert pipe.named_steps["model"].get_params()["learning_rate"] == HGB_PARAMS["learning_rate"]


def test_canonical_calibrated_model_contract():
    model = build_calibrated_hgb(cv=3, n_jobs=1)
    assert isinstance(model, CalibratedClassifierCV)
    assert model.method == "sigmoid"


def test_canonical_mode_model_contract():
    pipe = build_mode_pipeline()
    model = pipe.named_steps["model"]
    assert model.get_params()["class_weight"] == MODE_HGB_PARAMS["class_weight"]
    assert model.get_params()["max_iter"] == MODE_HGB_PARAMS["max_iter"]


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


def test_audits_use_canonical_engineered_features():
    from src.error_analysis import FEATURES as ERROR_FEATURES
    from src.features import MODEL_FEATURES
    from src.split_sensitivity import FEATURES as SPLIT_FEATURES

    assert ERROR_FEATURES == MODEL_FEATURES
    assert SPLIT_FEATURES == MODEL_FEATURES


def test_model_comparison_report_keeps_test_set_out_of_selection():
    from pathlib import Path

    report = Path("reports/model_comparison.md").read_text(encoding="utf-8")
    selection = report.split("## Selection", 1)[1].split("## Engineering interpretation", 1)[0]

    assert "held-out test set is reserved for final comparison" in selection
    assert "held-out PR-AUC and recall/F1 balance" not in selection
