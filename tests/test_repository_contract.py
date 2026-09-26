from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_and_extended_repository_boundaries():
    required_core = [
        "app.py",
        "src/features.py",
        "src/load_data.py",
        "src/models.py",
        "src/risk_model.py",
        "src/console_models.py",
        "reports/risk_model.md",
        "reports/explainability.md",
        "docs/model_card.md",
        "docs/reproducibility_audit.md",
    ]
    required_extended = [
        "extended-validation/README.md",
        "extended-validation/src/model_comparison.py",
        "extended-validation/src/feature_ablation.py",
        "extended-validation/src/uncertainty_audit.py",
        "extended-validation/reports/model_comparison.md",
        "extended-validation/reports/uncertainty_audit.md",
    ]
    for relative in required_core + required_extended:
        assert (ROOT / relative).is_file(), relative


def test_removed_application_only_and_old_validation_paths_stay_absent():
    forbidden = [
        "docs/interview_walkthrough.md",
        "docs/resume_bullets.md",
        "src/model_comparison.py",
        "src/feature_ablation.py",
        "src/uncertainty_audit.py",
        "reports/model_comparison.md",
        "reports/feature_ablation.md",
        "reports/uncertainty_audit.md",
    ]
    for relative in forbidden:
        assert not (ROOT / relative).exists(), relative


def test_readme_points_reviewers_to_extended_validation():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "extended-validation/README.md" in readme
    assert "python extended-validation/src/model_comparison.py" in readme
    assert "python src/model_comparison.py" not in readme
    assert "docs/interview_walkthrough.md" not in readme
    assert "docs/resume_bullets.md" not in readme
    assert "src/console_models.py, reusing" not in readme


def test_gitignore_keeps_committed_figures_trackable():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "figures/*.png" not in gitignore
    assert "figures/01_class_balance.svg" not in gitignore


def test_dataset_setup_contract():
    script = ROOT / "scripts/download_dataset.py"
    assert script.is_file()

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    dataset_readme = (ROOT / "data/README.md").read_text(encoding="utf-8")

    assert "python scripts/download_dataset.py" in readme
    assert "python scripts/download_dataset.py" in dataset_readme
    assert "data/ai4i2020.csv" in dataset_readme
