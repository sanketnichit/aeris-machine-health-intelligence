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
