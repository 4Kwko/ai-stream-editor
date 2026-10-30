from ai_stream_editor.config import Settings
from ai_stream_editor import diagnostics


def test_storage_report_does_not_create_or_change_files(tmp_path):
    missing = tmp_path / "missing" / "data"
    report = diagnostics.storage_report(missing)
    assert not report["exists"] and report["categories_bytes"] == {}
    assert not missing.parent.exists()
    data = tmp_path / "data"
    (data / "clips").mkdir(parents=True)
    (data / "models").mkdir()
    (data / "clips" / "fixture.mp4").write_bytes(b"preview")
    (data / "models" / "model.bin").write_bytes(b"model")
    before = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in data.rglob("*") if p.is_file()}
    report = diagnostics.storage_report(data)
    after = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in data.rglob("*") if p.is_file()}
    assert report["categories_bytes"] == {"clips": 7, "models": 5}
    assert before == after


def test_missing_dependencies_and_model_are_explained_without_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostics, "command_output", lambda *args: "")
    settings = Settings(data_dir=tmp_path / "missing")
    report = diagnostics.diagnose(settings, check_api=False)
    assert not report["ready"]
    assert not report["checks"]["ffmpeg_available"]
    assert not report["checks"]["model_assets_present"]
    assert report["api"]["checked"] is False
    assert not settings.data_dir.exists()


def test_doctor_reports_real_ffmpeg_features_without_creating_database(tmp_path):
    report = diagnostics.diagnose(Settings(data_dir=tmp_path / "missing"), check_api=False)
    assert report["checks"]["ffmpeg_available"]
    assert report["checks"]["ffprobe_available"]
    assert report["checks"]["libx264_available"]
    assert report["checks"]["required_filters_available"]
    assert report["checks"]["scale_reset_sar_available"]
    assert not (tmp_path / "missing").exists()


def test_data_directory_cannot_be_an_existing_file(tmp_path):
    file = tmp_path / "data"
    file.write_bytes(b"keep")
    report = diagnostics.diagnose(Settings(data_dir=file), check_api=False)
    assert not report["checks"]["data_directory_accessible_advisory"]
    assert file.read_bytes() == b"keep"
