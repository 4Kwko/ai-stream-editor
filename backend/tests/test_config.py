from pathlib import Path

import pytest

from ai_stream_editor.config import Settings


@pytest.mark.parametrize("value", ["relative/data", "//host/share/data", "\\\\host\\share\\data"])
def test_data_config_rejects_nonlocal_paths_without_creating_them(value):
    with pytest.raises(ValueError, match="locais|rede"):
        Settings(data_dir=Path(value))


def test_model_path_and_choice_are_local_and_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_STREAM_MODEL_DIR", "//host/models")
    with pytest.raises(ValueError, match="rede"):
        Settings(data_dir=tmp_path / "data")
    assert not (tmp_path / "data").exists()
    monkeypatch.delenv("AI_STREAM_MODEL_DIR")
    with pytest.raises(ValueError, match="modelo"):
        Settings(data_dir=tmp_path, model_name="remote/custom")
    assert Settings(data_dir=tmp_path).model_dir == tmp_path / "models"
