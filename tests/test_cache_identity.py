from src.console_models import _cache_path


def test_cache_identity_is_stable_and_seed_specific(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    path = data / "sample.csv"
    path.write_text("value\n1\n", encoding="utf-8")

    first = _cache_path(path, random_state=42)
    assert first == _cache_path(path, random_state=42)
    assert first != _cache_path(path, random_state=7)


def test_cache_identity_changes_with_dataset_contents(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    path = data / "sample.csv"
    path.write_text("value\n1\n", encoding="utf-8")
    first = _cache_path(path)
    path.write_text("value\n2\n", encoding="utf-8")
    assert first != _cache_path(path)
