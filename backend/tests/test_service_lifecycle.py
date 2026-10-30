import errno
from pathlib import Path
import threading
import time

import pytest

from ai_stream_editor import analysis
from ai_stream_editor.config import Settings
from ai_stream_editor.schemas import ClipPatch
from ai_stream_editor.service import Service, ServiceError


@pytest.fixture
def service(tmp_path):
    instance = Service(Settings(data_dir=tmp_path / "data"))
    try:
        yield instance
    finally:
        instance.close()


def finished(service, job):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        current = service.require("job", job["id"])
        if current["status"] in {"succeeded", "failed", "canceled"}:
            return current
        time.sleep(.01)
    pytest.fail("Job did not reach a terminal state")


def seed_clip(service, tmp_path):
    source = tmp_path / "fixture-source.mp4"
    source.write_bytes(b"synthetic unit fixture, not media")
    stat = source.stat()
    segments = [{"start_seconds": 1, "end_seconds": 4, "text": "Primeira frase completa.",
                 "words": [{"text": "Primeira", "start_seconds": 1, "end_seconds": 2},
                           {"text": "frase", "start_seconds": 2, "end_seconds": 3},
                           {"text": "completa.", "start_seconds": 3, "end_seconds": 4}]},
                {"start_seconds": 7, "end_seconds": 9, "text": "Outra frase."}]
    project = dict(id="project", source_path=str(source), source_size=stat.st_size,
                   source_mtime_ns=stat.st_mtime_ns, name=source.name, duration_seconds=20,
                   width=320, height=180, fps=10, has_audio=True, created_at="2026-10-29", transcript=segments)
    clip = dict(id="clip", project_id="project", start_seconds=0, end_seconds=10,
                captions=analysis.captions_for_window(segments, 0, 10), revision=1,
                review_status="approved", title="Synthetic fixture", reason="Unit test", score=.5,
                preview_revision=1, preview_file=str(service.settings.data_dir / "clips" / "fixture.mp4"))
    Path(clip["preview_file"]).parent.mkdir(parents=True)
    Path(clip["preview_file"]).write_bytes(b"synthetic preview fixture")
    service.store.put_many([("project", project), ("clip", clip)])
    return clip


def test_queued_cancellation_is_immediate_and_never_executes(service):
    started, release, invoked = threading.Event(), threading.Event(), threading.Event()

    def blocked(job_id, cancel):
        started.set()
        assert release.wait(5)
        return {}

    first = service.submit("render", "first", None, blocked)
    assert started.wait(5)
    try:
        second = service.submit("render", "second", None, lambda *a: invoked.set())
        canceled = service.cancel_job(second["id"])
        assert canceled["status"] == "canceled"
        assert not invoked.is_set()
    finally:
        release.set()
    assert finished(service, first)["status"] == "succeeded"
    service.close()
    assert not invoked.is_set()
    assert service.require("job", second["id"])["status"] == "canceled"


def test_shutdown_cancels_active_work_and_releases_instance_lock(service):
    started = threading.Event()

    def blocked(job_id, cancel):
        started.set()
        assert cancel.wait(5)
        raise ServiceError(409, "Cancelado")

    job = service.submit("render", "project", None, blocked)
    assert started.wait(5)
    service.close()
    assert service.require("job", job["id"])["status"] == "canceled"
    with pytest.raises(ServiceError, match="encerrando"):
        service.submit("render", "project", None, lambda *a: {})
    with ServiceContext(service.settings):
        pass


class ServiceContext:
    def __init__(self, settings):
        self.service = Service(settings)

    def __enter__(self):
        return self.service

    def __exit__(self, *args):
        self.service.close()


@pytest.mark.parametrize("failure, message", [(OSError(errno.ENOSPC, "fixture"), "Espaço em disco"),
                                             (PermissionError("fixture"), "Sem permissão")])
def test_storage_failure_is_actionable(service, failure, message):
    def fail(*args):
        raise failure
    job = finished(service, service.submit("export", "project", None, fail))
    assert job["status"] == "failed" and message in job["error"]


def test_correction_survives_outside_window_but_not_different_words(service, tmp_path):
    clip = seed_clip(service, tmp_path)
    captions = clip["captions"]
    captions[0]["text"] = "Primeira frase corrigida."
    service.patch_clip("clip", ClipPatch(captions=captions, expected_revision=1))
    trimmed = service.patch_clip("clip", ClipPatch(start_seconds=2.1))
    assert trimmed["captions"][0]["text"] == "frase completa."
    hidden = service.patch_clip("clip", ClipPatch(start_seconds=5))
    assert all(c["id"] != captions[0]["id"] for c in hidden["captions"])
    restored = service.patch_clip("clip", ClipPatch(start_seconds=0))
    assert restored["captions"][0]["text"] == "Primeira frase corrigida."
    assert restored["review_status"] == "pending" and restored["preview_status"] == "stale"


@pytest.mark.parametrize("mutation", ["edit", "reject", "cancel"])
def test_export_checks_state_after_copy_and_cleans_only_its_temp(service, tmp_path, monkeypatch, mutation):
    seed_clip(service, tmp_path)
    entered, release = threading.Event(), threading.Event()
    real_fsync = __import__("os").fsync

    def blocked_fsync(fd):
        entered.set()
        assert release.wait(5)
        real_fsync(fd)

    monkeypatch.setattr("ai_stream_editor.service.os.fsync", blocked_fsync)
    job = service.export("clip", str(tmp_path))
    assert entered.wait(5)
    try:
        with pytest.raises(ServiceError, match="operação"):
            service.export("clip", str(tmp_path))
        if mutation == "edit":
            service.patch_clip("clip", ClipPatch(end_seconds=9))
        elif mutation == "reject":
            service.patch_clip("clip", ClipPatch(review_status="rejected"))
        else:
            service.cancel_job(job["id"])
    finally:
        release.set()
    final = finished(service, job)
    assert final["status"] == ("canceled" if mutation == "cancel" else "failed")
    assert not list(tmp_path.glob("corte_*.mp4"))
    assert not list(tmp_path.glob(".ai-stream-*.partial"))
    assert service.store.related("export", "project") == []


def test_export_history_persists_and_late_cancel_does_not_change_success(service, tmp_path):
    seed_clip(service, tmp_path)
    job = finished(service, service.export("clip", str(tmp_path)))
    assert job["status"] == "succeeded"
    history = service.store.related("export", "project")
    assert len(history) == 1 and history[0]["revision"] == 1
    assert history[0]["output_path"] == job["result"]["output_path"]
    assert Path(history[0]["output_path"]).read_bytes() == b"synthetic preview fixture"
    assert service.cancel_job(job["id"])["status"] == "succeeded"
    service.close()
    with ServiceContext(service.settings) as resumed:
        assert resumed.store.related("export", "project") == history
        assert resumed.clip_view(resumed.require("clip", "clip"))["preview_status"] == "ready"


def test_export_terminal_state_waits_for_history_commit_outcome(service, tmp_path, monkeypatch):
    seed_clip(service, tmp_path)
    committing, release = threading.Event(), threading.Event()
    original = service.store.put_many

    def delayed_commit(records, **kwargs):
        if any(kind == "export" for kind, _ in records):
            committing.set()
            assert release.wait(5)
        return original(records, **kwargs)

    monkeypatch.setattr(service.store, "put_many", delayed_commit)
    job = service.export("clip", str(tmp_path))
    assert committing.wait(5)
    try:
        assert service.require("job", job["id"])["status"] == "running"
    finally:
        release.set()
    assert finished(service, job)["status"] == "succeeded"
    assert len(service.store.related("export", "project")) == 1


def test_cancel_waiting_for_publication_cannot_relabel_success(service, tmp_path, monkeypatch):
    seed_clip(service, tmp_path)
    publishing, release, cancel_called = threading.Event(), threading.Event(), threading.Event()
    real_put = service.store.put_many

    def blocked_commit(records, **kwargs):
        if any(kind == "export" for kind, value in records):
            publishing.set()
            assert release.wait(5)
        real_put(records, **kwargs)

    monkeypatch.setattr(service.store, "put_many", blocked_commit)
    job = service.export("clip", str(tmp_path))
    assert publishing.wait(5)

    def cancel_during_commit():
        cancel_called.set()
        service.cancel_job(job["id"])

    canceler = threading.Thread(target=cancel_during_commit)
    canceler.start()
    try:
        assert cancel_called.wait(5)
    finally:
        release.set()
    canceler.join(5)
    assert not canceler.is_alive()
    final = finished(service, job)
    assert final["status"] == "succeeded" and final["error"] is None
    assert Path(final["result"]["output_path"]).is_file()


def test_failed_initialization_releases_instance_lock(tmp_path, monkeypatch):
    import ai_stream_editor.service as service_module
    settings = Settings(data_dir=tmp_path / "failed-start")
    original_store = service_module.Store

    def failed_store(path):
        raise OSError("synthetic startup failure")

    monkeypatch.setattr(service_module, "Store", failed_store)
    with pytest.raises(OSError, match="startup failure"):
        Service(settings)
    monkeypatch.setattr(service_module, "Store", original_store)
    with ServiceContext(settings):
        pass


def test_missing_preview_not_reported_ready_and_old_url_refused(service, tmp_path):
    clip = seed_clip(service, tmp_path)
    with pytest.raises(ServiceError, match="revisão antiga"):
        service.preview("clip", revision=2)
    Path(clip["preview_file"]).unlink()
    assert service.clip_view(clip)["preview_status"] == "missing"
    with pytest.raises(ServiceError):
        service.preview("clip")


@pytest.mark.parametrize("kind", ["render", "analyze"])
def test_processing_collision_does_not_remove_existing_file(service, tmp_path, monkeypatch, kind):
    seed_clip(service, tmp_path)
    monkeypatch.setattr("ai_stream_editor.service.uuid4", lambda: "fixture-collision")
    if kind == "render":
        existing = service.settings.data_dir / "clips" / "clip" / "fixture-collision.mp4"
        target = "ai_stream_editor.service.media.render_clip"
        action = lambda: service.render("clip")
    else:
        project = service.require("project", "project")
        project["transcript"] = None
        service.store.put("project", project)
        existing = service.settings.data_dir / "projects" / "project" / "fixture-collision.wav"
        target = "ai_stream_editor.service.media.extract_audio"
        action = lambda: service.analyze("project")
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"preexisting unrelated fixture")

    def collision(*a, **k):
        raise __import__("ai_stream_editor.media", fromlist=["MediaError"]).MediaError("Arquivo de destino já existe.")

    monkeypatch.setattr(target, collision)
    job = finished(service, action())
    assert job["status"] == "failed"
    assert existing.read_bytes() == b"preexisting unrelated fixture"


def test_mapped_network_drive_rejected_before_path_resolution(tmp_path, monkeypatch):
    import os
    import ctypes
    from ai_stream_editor.service import local_path
    if os.name != "nt":
        pytest.skip("Windows drive type check")
    calls = []
    monkeypatch.setattr(ctypes.windll.kernel32, "GetDriveTypeW", lambda anchor: calls.append(anchor) or 4)
    with pytest.raises(ServiceError, match="rede"):
        local_path(str(tmp_path / "does-not-exist.mp4"))
    assert calls


def test_published_export_recovers_after_database_commit_failure(service, tmp_path, monkeypatch):
    import sqlite3
    seed_clip(service, tmp_path)
    original_put = service.store.put_many

    def failed_export_commit(records, **kwargs):
        if any(kind == "export" for kind, value in records):
            raise sqlite3.OperationalError("controlled database unavailable")
        return original_put(records, **kwargs)

    monkeypatch.setattr(service.store, "put_many", failed_export_commit)
    job = finished(service, service.export("clip", str(tmp_path)))
    assert job["status"] == "succeeded" and "warning" in job
    path = Path(job["result"]["output_path"])
    assert path.read_bytes() == b"synthetic preview fixture"
    assert len(service.exports_for("project")) == 1
    assert service.store.get("export_pending", job["id"]) is not None
    service.close()
    with ServiceContext(service.settings) as resumed:
        recovered = resumed.require("job", job["id"])
        assert recovered["status"] == "succeeded" and recovered["result"]["output_path"] == str(path)
        assert len(resumed.exports_for("project")) == 1
        assert resumed.store.get("export_pending", job["id"]) is None


def test_export_success_is_not_written_twice(service, tmp_path, monkeypatch):
    seed_clip(service, tmp_path)
    original_put = service.store.put

    def reject_redundant_success(kind, value):
        if kind == "job" and value["status"] == "succeeded":
            pytest.fail("Export success must be committed only with its history")
        return original_put(kind, value)

    monkeypatch.setattr(service.store, "put", reject_redundant_success)
    job = finished(service, service.export("clip", str(tmp_path)))
    assert job["status"] == "succeeded" and job["error"] is None


def test_shutdown_releases_resources_even_when_cancel_cannot_be_persisted(service, monkeypatch):
    started = threading.Event()

    def blocked(job_id, cancel):
        started.set()
        assert cancel.wait(5)
        raise ServiceError(409, "Canceled fixture")

    job = service.submit("render", "project", None, blocked)
    assert started.wait(5)

    def denied(*a, **k):
        raise PermissionError("controlled database permission failure")

    monkeypatch.setattr(service.store, "put", denied)
    service.close()
    assert service.require("job", job["id"])["status"] == "canceled"
    assert service.instance_lock.file.closed
    assert all(not thread.is_alive() for thread in service.executor._threads)
    with ServiceContext(service.settings):
        pass


def test_recovery_cannot_accept_unrelated_file_with_same_name(service, tmp_path):
    clip = seed_clip(service, tmp_path)
    output = tmp_path / "unrelated.mp4"
    output.write_bytes(b"not our output")
    pending = dict(id="interrupted-export", job_id="interrupted-export", project_id="project", clip_id="clip",
                   revision=1, created_at="2026-10-29T20:00:00+00:00", output_path=str(output),
                   file_identity=service.file_identity(Path(clip["preview_file"])))
    service.store.put_many([("export_pending", pending), ("job", dict(id=pending["id"], status="running"))])
    service.close()
    with ServiceContext(service.settings) as resumed:
        assert resumed.require("job", pending["id"])["status"] == "failed"
        assert resumed.exports_for("project") == []
    assert output.read_bytes() == b"not our output"
