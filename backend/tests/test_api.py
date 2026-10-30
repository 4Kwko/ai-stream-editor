import hashlib
from pathlib import Path
import subprocess
import threading
import time

from fastapi.testclient import TestClient
import pytest

from ai_stream_editor.api import create_app
from ai_stream_editor.config import Settings
from ai_stream_editor import service as service_module
from ai_stream_editor.store import Store


def fake_transcriber(audio, model_dir, **kwargs):
    """Fixture only: API integration tests do not claim real speech recognition."""
    assert audio.is_file()
    return [{"start_seconds": 0, "end_seconds": 2, "text": "Olha isso, finalmente consegui!",
             "words": [{"start_seconds": 0, "end_seconds": .5, "text": "Olha"},
                       {"start_seconds": .5, "end_seconds": 1, "text": "isso,"},
                       {"start_seconds": 1, "end_seconds": 1.5, "text": "finalmente"},
                       {"start_seconds": 1.5, "end_seconds": 2, "text": "consegui!"}]}]


@pytest.fixture
def video(tmp_path):
    path = tmp_path / "original com espaços.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=10",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000", "-t", "2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)], check=True, timeout=20)
    return path


@pytest.fixture
def client(tmp_path, monkeypatch):
    real_render = service_module.media.render_clip

    def small_render(*args, **kwargs):
        return real_render(*args, **kwargs, width=180, height=320)

    monkeypatch.setattr(service_module.media, "render_clip", small_render)
    app = create_app(Settings(data_dir=tmp_path / "data"), transcriber=fake_transcriber)
    with TestClient(app, base_url="http://127.0.0.1:8765") as http:
        yield http


def wait_job(client, response):
    assert response.status_code == 202, response.text
    job_id = response.json()["job_id"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in {"succeeded", "failed", "canceled"}:
            return job
        time.sleep(.03)
    pytest.fail(f"Job did not terminate: {job_id}")


def analyzed_clip(client, video):
    response = client.post("/api/projects", json={"source_path": str(video)})
    assert response.status_code == 201, response.text
    project = response.json()
    job = wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))
    assert job["status"] == "succeeded", job
    clips = client.get(f"/api/projects/{project['id']}/clips").json()
    assert clips
    return project, clips[0]


def test_import_edit_render_range_export_and_preserve_original(client, video, tmp_path):
    before = hashlib.sha256(video.read_bytes()).hexdigest()
    project, clip = analyzed_clip(client, video)
    resumed = client.get(f"/api/projects/{project['id']}").json()
    assert resumed["analysis_job_id"] and resumed["analysis_status"] == "succeeded"
    assert resumed["analyzed_at"] and resumed["clip_count"] == 1
    assert "transcript" not in resumed
    assert client.get(f"/api/projects/{project['id']}/jobs").json()[0]["kind"] == "analyze"
    assert client.get(f"/api/clips/{clip['id']}/preview").status_code == 409
    assert clip["captions"] and clip["review_status"] == "pending"
    assert client.post(f"/api/clips/{clip['id']}/export", json={"output_directory": str(tmp_path)}).status_code == 409
    captions = clip["captions"]
    captions[0]["text"] = "Legenda corrigida {sem efeitos}"
    changed = client.patch(f"/api/clips/{clip['id']}", json={"captions": captions, "expected_revision": 1}).json()
    assert changed["revision"] == 2
    rendered = wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))
    assert rendered["status"] == "succeeded", rendered
    ranged = client.get(f"/api/clips/{clip['id']}/preview", headers={"Range": "bytes=0-99"})
    assert ranged.status_code == 206 and len(ranged.content) == 100
    assert ranged.headers["content-range"].startswith("bytes 0-99/")
    assert client.get(f"/api/clips/{clip['id']}/preview", headers={"Range": "bytes=999999999-"}).status_code == 416
    approved = client.patch(f"/api/clips/{clip['id']}", json={"review_status": "approved"}).json()
    assert approved["preview_status"] == "ready" and approved["revision"] == 2
    outputs = []
    for _ in range(2):
        job = wait_job(client, client.post(f"/api/clips/{clip['id']}/export", json={"output_directory": str(tmp_path)}))
        assert job["status"] == "succeeded", job
        outputs.append(Path(job["result"]["output_path"]))
    assert outputs[0] != outputs[1] and all(p.is_file() for p in outputs)
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    history = client.get(f"/api/clips/{clip['id']}/exports").json()
    assert len(history) == 2 and all(e["revision"] == 2 for e in history)
    assert client.get(f"/api/projects/{project['id']}/exports").json() == history
    changed = client.patch(f"/api/clips/{clip['id']}", json={"end_seconds": 1.8}).json()
    assert changed["preview_status"] == "stale" and changed["review_status"] == "pending"
    assert changed["captions"][0]["text"] == captions[0]["text"]
    assert client.get(f"/api/clips/{clip['id']}/preview?revision=2").status_code == 409
    assert client.get(f"/api/clips/{clip['id']}/preview").status_code == 409
    assert client.post(f"/api/projects/{project['id']}/analyze").status_code == 409
    assert hashlib.sha256(video.read_bytes()).hexdigest() == before


def test_validation_and_local_origin_protection(client, video):
    for source in ["https://example.test/a.mp4", "relative.mp4", "\\\\host\\video.mp4", "//host/video.mp4", str(video.parent)]:
        assert client.post("/api/projects", json={"source_path": source}).status_code == 422
    assert client.get("/api/health", headers={"Host": "evil.test"}).status_code == 400
    assert client.get("/api/health", headers={"Origin": "https://evil.test"}).status_code == 403
    assert client.post("/api/projects", headers={"Origin": "null"}, json={"source_path": str(video)}).status_code == 403
    preflight = client.options("/api/projects", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST"})
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert client.get("/api/projects/missing").status_code == 404
    for route in ["jobs", "exports"]:
        assert client.get(f"/api/projects/missing/{route}").status_code == 404
    assert client.get("/api/clips/missing/exports").status_code == 404
    _, clip = analyzed_clip(client, video)
    for patch in [{"start_seconds": 2}, {"end_seconds": 99}, {"start_seconds": None}, {"captions": None},
                  {"captions": [{"id": "x", "text": "x", "start_seconds": 1, "end_seconds": .5}]},
                  {"review_status": "anything"}, {"source_path": str(video)}]:
        assert client.patch(f"/api/clips/{clip['id']}", json=patch).status_code == 422
    assert client.patch(f"/api/clips/{clip['id']}", json={"expected_revision": 99}).status_code == 409


def test_concurrent_edit_cannot_publish_stale_render(client, video, monkeypatch):
    _, clip = analyzed_clip(client, video)
    started, finish = threading.Event(), threading.Event()

    def blocked_render(source, output, *args, **kwargs):
        started.set()
        assert finish.wait(5)
        output.write_bytes(b"test-render-fixture")

    monkeypatch.setattr(service_module.media, "render_clip", blocked_render)
    response = client.post(f"/api/clips/{clip['id']}/render")
    assert started.wait(5)
    try:
        assert client.post(f"/api/clips/{clip['id']}/render").status_code == 409
        changed = client.patch(f"/api/clips/{clip['id']}", json={"end_seconds": 1.8})
        assert changed.status_code == 200
    finally:
        finish.set()
    job = wait_job(client, response)
    assert job["status"] == "failed" and "mudou" in job["error"]
    assert client.get(f"/api/clips/{clip['id']}/preview").status_code == 409
    assert not list((client.app.state.service.settings.data_dir / "clips").rglob("*.mp4"))


def test_cancel_job_and_model_failure_are_visible(client, video, monkeypatch):
    project = client.post("/api/projects", json={"source_path": str(video)}).json()
    started = threading.Event()

    def until_cancel(audio, model_dir, *, cancel, **kwargs):
        started.set()
        assert cancel.wait(5)
        raise service_module.analysis.AnalysisError("Processamento cancelado.")

    client.app.state.service.transcriber = until_cancel
    response = client.post(f"/api/projects/{project['id']}/analyze")
    assert started.wait(5)
    active_project = client.get(f"/api/projects/{project['id']}").json()
    assert active_project["analysis_job_id"] == response.json()["id"]
    assert active_project["analysis_status"] == "running"
    assert client.post(f"/api/jobs/{response.json()['id']}/cancel").status_code == 200
    assert wait_job(client, response)["status"] == "canceled"
    assert client.get(f"/api/projects/{project['id']}/clips").json() == []
    client.app.state.service.transcriber = lambda *a, **k: (_ for _ in ()).throw(service_module.analysis.AnalysisError("Modelo não preparado."))
    job = wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))
    assert job["status"] == "failed" and "Modelo" in job["error"]


def test_no_partial_analysis_saved_on_invalid_suggestion(client, video, monkeypatch):
    project = client.post("/api/projects", json={"source_path": str(video)}).json()
    good = {"start_seconds": 0, "end_seconds": 2, "title": "Fixture", "reason": "Teste", "score": .5, "captions": []}
    bad = dict(good, captions=[{"id": "bad", "text": "x", "start_seconds": 0, "end_seconds": 99}])
    monkeypatch.setattr(service_module.analysis, "suggest_clips", lambda *a: [good, bad])
    job = wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))
    assert job["status"] == "failed"
    assert client.get(f"/api/projects/{project['id']}/clips").json() == []
    assert client.app.state.service.store.get("project", project["id"])["transcript"] is None


def test_successful_empty_analysis_and_recent_project_metadata(client, video, monkeypatch):
    project = client.post("/api/projects", json={"source_path": str(video)}).json()
    assert project["analysis_job_id"] is None and project["analysis_status"] == "not_started"
    monkeypatch.setattr(service_module.analysis, "suggest_clips", lambda *a: [])
    job = wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))
    assert job["status"] == "succeeded" and job["result"]["clip_ids"] == []
    assert "regras textuais" in job["result"]["empty_reason"]
    assert job["result"]["message"] == job["result"]["empty_reason"]
    assert job["progress_scope"] == "stage"
    assert job["elapsed_seconds"] >= 0 and job["started_at"] and job["finished_at"]
    assert all(value >= 0 for value in job["result"]["timings_seconds"].values())
    projects = client.get("/api/projects").json()
    assert projects[0]["id"] == project["id"] and projects[0]["clip_count"] == 0
    assert projects[0]["analysis_job_id"] == job["id"]
    assert projects[0]["analysis_status"] == "succeeded"
    assert "transcript" not in projects[0]


def test_empty_transcript_reason_does_not_claim_cause_or_bad_model(client, video):
    client.app.state.service.transcriber = lambda *a, **k: []
    project = client.post("/api/projects", json={"source_path": str(video)}).json()
    job = wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))
    assert job["status"] == "succeeded" and job["result"]["clip_ids"] == []
    assert job["result"]["empty_reason"] == "A transcrição local não retornou segmentos de fala."


@pytest.mark.parametrize("state", ["missing", "changed", "unavailable"])
def test_project_reports_source_state_without_reprocessing(client, video, monkeypatch, state):
    project = client.post("/api/projects", json={"source_path": str(video)}).json()
    assert project["source_available"] is True and project["source_status"] == "available"
    if state == "missing":
        video.rename(video.with_name("moved-fixture.mp4"))
    elif state == "changed":
        with video.open("ab") as stream:
            stream.write(b"changed synthetic fixture")
    else:
        original_stat = Path.stat

        def denied(path, *args, **kwargs):
            if path == video:
                raise PermissionError("controlled source metadata failure")
            return original_stat(path, *args, **kwargs)

        monkeypatch.setattr(Path, "stat", denied)
    for response in [client.get(f"/api/projects/{project['id']}"), client.get("/api/projects")]:
        assert response.status_code == 200
        data = response.json()
        current = data[0] if isinstance(data, list) else data
        assert current["source_available"] is False and current["source_status"] == state
        assert current["analysis_status"] == "not_started"


def test_missing_source_does_not_block_export_of_approved_current_preview(client, video, tmp_path):
    project, clip = analyzed_clip(client, video)
    assert wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))["status"] == "succeeded"
    client.patch(f"/api/clips/{clip['id']}", json={"review_status": "approved"})
    video.rename(video.with_name("moved-after-render.mp4"))
    assert client.get(f"/api/projects/{project['id']}").json()["source_status"] == "missing"
    job = wait_job(client, client.post(f"/api/clips/{clip['id']}/export", json={"output_directory": str(tmp_path)}))
    assert job["status"] == "succeeded" and Path(job["result"]["output_path"]).is_file()


def test_api_storage_errors_are_safe_and_actionable(client, video, monkeypatch):
    import errno

    def disk_full(*args):
        raise OSError(errno.ENOSPC, "private fixture path not for display")

    monkeypatch.setattr(client.app.state.service, "create_project", disk_full)
    response = client.post("/api/projects", json={"source_path": str(video)})
    assert response.status_code == 507
    assert "Espaço em disco" in response.json()["detail"]
    assert "private fixture" not in response.text


def test_export_collision_preserves_existing_temporary_file(client, video, tmp_path, monkeypatch):
    _, clip = analyzed_clip(client, video)
    assert wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))["status"] == "succeeded"
    client.patch(f"/api/clips/{clip['id']}", json={"review_status": "approved"})
    existing = tmp_path / ".ai-stream-fixture-collision.partial"
    existing.write_bytes(b"existing user data")
    monkeypatch.setattr(service_module, "uuid4", lambda: "fixture-collision")
    job = wait_job(client, client.post(f"/api/clips/{clip['id']}/export", json={"output_directory": str(tmp_path)}))
    assert job["status"] == "failed"
    assert existing.read_bytes() == b"existing user data"
    assert not list(tmp_path.glob("corte_*.mp4"))


def test_export_warning_keeps_success_and_history_available_over_http(client, video, tmp_path, monkeypatch):
    import sqlite3
    project, clip = analyzed_clip(client, video)
    assert wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))["status"] == "succeeded"
    client.patch(f"/api/clips/{clip['id']}", json={"review_status": "approved"})
    original_put = client.app.state.service.store.put_many

    def unavailable_export_history(records, **kwargs):
        if any(kind == "export" for kind, value in records):
            raise sqlite3.OperationalError("controlled fixture failure; never alter database permissions")
        return original_put(records, **kwargs)

    monkeypatch.setattr(client.app.state.service.store, "put_many", unavailable_export_history)
    response = client.post(f"/api/clips/{clip['id']}/export", json={"output_directory": str(tmp_path)})
    job = wait_job(client, response)
    assert job["status"] == "succeeded" and job["error"] is None
    assert job["warning"] and Path(job["result"]["output_path"]).is_file()
    jobs = client.get(f"/api/projects/{project['id']}/jobs").json()
    assert next(item for item in jobs if item["id"] == job["id"])["warning"] == job["warning"]
    clip_history = client.get(f"/api/clips/{clip['id']}/exports").json()
    project_history = client.get(f"/api/projects/{project['id']}/exports").json()
    assert clip_history == project_history and len(clip_history) == 1
    assert clip_history[0]["output_path"] == job["result"]["output_path"]
    assert "job_snapshot" not in clip_history[0] and "file_identity" not in clip_history[0]
    assert client.post(f"/api/jobs/{job['id']}/cancel").json()["status"] == "succeeded"


def test_invalid_video_missing_audio_and_changed_original(client, video, tmp_path):
    invalid = tmp_path / "invalid.mp4"
    invalid.write_bytes(b"not a video")
    assert client.post("/api/projects", json={"source_path": str(invalid)}).status_code == 422
    silent = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-an", "-c:v", "copy", str(silent)], check=True, timeout=20)
    project = client.post("/api/projects", json={"source_path": str(silent)}).json()
    assert project["has_audio"] is False
    assert client.post(f"/api/projects/{project['id']}/analyze").status_code == 422
    project = client.post("/api/projects", json={"source_path": str(video)}).json()
    with video.open("ab") as stream:
        stream.write(b"changed fixture")
    job = wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))
    assert job["status"] == "failed" and "original mudou" in job["error"]


def test_persistence_recovery_and_instance_lock(tmp_path, video):
    settings = Settings(data_dir=tmp_path / "data")
    first = create_app(settings, transcriber=fake_transcriber)
    with TestClient(first, base_url="http://127.0.0.1:8765") as client:
        project, clip = analyzed_clip(client, video)
        with pytest.raises(RuntimeError, match="Outro backend"):
            create_app(settings)
    store = Store(settings.data_dir)
    store.put("job", {"id": "interrupted", "status": "running"})
    with TestClient(create_app(settings), base_url="http://127.0.0.1:8765") as client:
        assert client.get(f"/api/projects/{project['id']}").status_code == 200
        assert client.get(f"/api/projects/{project['id']}/clips").json()[0]["id"] == clip["id"]
        assert client.get("/api/jobs/interrupted").json()["status"] == "failed"
