"""Controlled source/ASR; real FFmpeg, database, API and supervisor."""

from copy import deepcopy
import hashlib
import threading
import time

from fastapi.testclient import TestClient
import pytest

from ai_stream_editor import analysis, media
from ai_stream_editor.api import create_app
from ai_stream_editor.automation import Automation
from ai_stream_editor.config import Settings
from ai_stream_editor.service import Service
from ai_stream_editor.twitch import SourceError
from test_api import fake_transcriber, video


class FixtureSource:
    def __init__(self, path, entries=None):
        self.path = path
        self.entries = entries if entries is not None else [entry("1")]
        self.discoveries = 0
        self.downloads = []

    def discover(self, login, cancel):
        self.discoveries += 1
        return deepcopy(self.entries)

    def download(self, login, record, cancel):
        self.downloads.append(record["vod_id"])
        return self.path


def entry(key, duration=2):
    return dict(id=key, title=f"Fixture {key}", duration_seconds=duration)


def poll(automation):
    config = automation.config()
    config["next_poll_at"] = 0
    automation.service.store.put("automation", config)
    automation.cycle()


def until(predicate):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.02)
    pytest.fail("condition did not become true")


@pytest.fixture
def app(tmp_path, monkeypatch, video):
    renderer = media.render_clip
    monkeypatch.setattr(media, "render_clip", lambda *a, **k: renderer(*a, **k, width=180, height=320))
    source = FixtureSource(video)
    app = create_app(Settings(data_dir=tmp_path / "data"), transcriber=fake_transcriber, automation_source=source)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        yield app, client, source


def test_pipeline_ready_gallery_review_file_and_missing_original(app, video, monkeypatch):
    application, client, source = app
    automation = application.state.automation
    service = application.state.service
    original_hash = hashlib.sha256(video.read_bytes()).hexdigest()
    assert client.get("/api/gallery").json() == dict(items=[], next_cursor=None)
    assert source.discoveries == 0  # GET does not start any work.
    poll(automation)
    assert not source.downloads  # Wait for a second stable duration observation.
    poll(automation)
    assert source.downloads == ["1"]
    record = automation.records("joaomontagner")[0]
    assert record["state"] == "completed"
    gallery = client.get("/api/gallery?review_status=pending").json()
    item = gallery["items"][0]
    assert item["source"]["vod_id"] == "1" and item["source"]["type"] == "twitch"
    assert "captions" not in item and "source_path" not in str(gallery)
    assert item["duration_seconds"] > 0 and item["download_url"]
    job_count = len(service.store.all("job"))
    gallery_updated_at = client.get("/api/automation").json()["gallery_updated_at"]
    assert gallery_updated_at
    clip = service.require("clip", item["id"])
    before = service.preview(clip["id"]).read_bytes()
    for review in ("approved", "rejected", "pending"):
        response = client.patch(f"/api/clips/{clip['id']}", json={"review_status": review, "expected_revision": 1})
        assert response.status_code == 200, response.text
        assert response.json()["revision"] == 1
        assert client.get(f"/api/gallery?review_status={review}").json()["items"][0]["review_status"] == review
    assert len(service.store.all("job")) == job_count
    assert client.get("/api/automation").json()["gallery_updated_at"] == gallery_updated_at
    assert service.preview(clip["id"]).read_bytes() == before
    assert hashlib.sha256(video.read_bytes()).hexdigest() == original_hash
    video.rename(video.with_suffix(".moved.mp4"))  # Only this test's generated fixture.
    response = client.get(f"/api/clips/{clip['id']}/file?revision=1", headers={"Range": "bytes=0-99"})
    assert response.status_code == 206 and response.content == before[:100]
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"
    assert client.get(f"/api/clips/{clip['id']}/file?revision=2").status_code == 409
    assert client.get("/api/gallery").json()["items"]
    poll(automation)
    assert source.downloads == ["1"] and len(service.store.all("job")) == job_count


def test_first_scan_skips_old_history_and_defers_growing_archive(app):
    application, _, source = app
    automation = application.state.automation
    source.entries = [entry("3"), entry("2"), entry("1")]
    poll(automation)
    source.entries[0]["duration_seconds"] = 3
    poll(automation)
    assert not source.downloads
    records = {r["vod_id"]: r for r in automation.records("joaomontagner")}
    assert records["2"]["state"] == records["1"]["state"] == "skipped"
    poll(automation)
    assert source.downloads == ["3"]
    poll(automation)
    assert source.downloads == ["3"]


def test_silence_is_completed_without_renders_or_retries(app):
    application, client, source = app
    application.state.service.transcriber = lambda *a, **k: []
    automation = application.state.automation
    poll(automation)
    poll(automation)
    for _ in range(3):
        poll(automation)
    assert source.downloads == ["1"]
    assert automation.records("joaomontagner")[0]["state"] == "completed"
    assert not client.get("/api/gallery").json()["items"]
    assert [j["kind"] for j in application.state.service.store.all("job")] == ["analyze"]


def test_partial_render_failure_keeps_other_ready_and_retry_skips_success(app, monkeypatch):
    application, client, source = app
    original_suggest = analysis.suggest_clips
    renderer = media.render_clip
    calls = []

    def two_suggestions(*args):
        candidate = original_suggest(*args)[0]
        second = deepcopy(candidate)
        second["title"] = "Segundo candidato controlado"
        return [candidate, second]

    def fail_once(*args, **kwargs):
        calls.append(args[1])
        if len(calls) == 1:
            raise media.MediaError("Falha controlada de render")
        return renderer(*args, **kwargs)

    monkeypatch.setattr(analysis, "suggest_clips", two_suggestions)
    monkeypatch.setattr(media, "render_clip", fail_once)
    automation = application.state.automation
    poll(automation)
    poll(automation)
    assert len(calls) == 2 and len(client.get("/api/gallery").json()["items"]) == 1
    first_update = client.get("/api/automation").json()["gallery_updated_at"]
    assert first_update  # Ready clips signal the UI even while the VOD still needs retry.
    record = automation.records("joaomontagner")[0]
    assert record["state"] == "queued" and record["next_attempt_at"] > time.time()
    automation.save(record, next_attempt_at=0)
    automation.cycle()
    assert len(calls) == 3 and source.downloads == ["1"]
    assert client.get("/api/automation").json()["gallery_updated_at"] > first_update
    assert len(client.get("/api/gallery").json()["items"]) == 2
    assert automation.records("joaomontagner")[0]["state"] == "completed"


def test_download_failures_bounded_and_do_not_block_new_vod(app):
    application, client, source = app
    automation = application.state.automation
    original_download = source.download
    failures = []

    def download(login, record, cancel):
        if record["vod_id"] == "1":
            failures.append(record["vod_id"])
            raise SourceError("Rede indisponível na fixture.")
        return original_download(login, record, cancel)

    source.download = download
    poll(automation)
    poll(automation)
    assert failures == ["1"]
    for _ in range(3):
        automation.cycle()
    assert failures == ["1"]
    source.entries.insert(0, entry("2"))
    poll(automation)
    poll(automation)
    assert source.downloads == ["2"] and client.get("/api/gallery").json()["items"]
    for _ in range(2):
        first = next(r for r in automation.records("joaomontagner") if r["vod_id"] == "1")
        automation.save(first, next_attempt_at=0)
        automation.cycle()
    assert len(failures) == 3
    first = next(r for r in automation.records("joaomontagner") if r["vod_id"] == "1")
    assert first["state"] == "failed"
    automation.cycle()
    assert len(failures) == 3


def test_invalid_download_never_becomes_analyzed_project(app, tmp_path):
    application, client, source = app
    invalid = tmp_path / "incomplete.mp4"
    invalid.write_bytes(b"partial fixture")
    source.path = invalid
    automation = application.state.automation
    poll(automation)
    poll(automation)
    assert not client.get("/api/projects").json()
    assert not application.state.service.store.all("job")
    assert automation.records("joaomontagner")[0]["error"]


def test_configuration_validation_and_gallery_parameters(app):
    application, client, source = app
    for body in ({"enabled": None}, {"channel_login": None}, {"channel_login": "https://www.twitch.tv/name"},
                 {"channel_login": "name/../../"}, {"secret": "not-accepted"}):
        assert client.patch("/api/automation", json=body).status_code == 422
    assert client.patch("/api/automation", json={"enabled": False}).json()["status"] == "disabled"
    poll(application.state.automation)
    assert source.discoveries == 0
    assert client.patch("/api/automation", json={"enabled": True}).status_code == 200
    for query in ("limit=0", "limit=51", "cursor=0", "review_status=invalid"):
        assert client.get("/api/gallery?" + query).status_code == 422
    application.state.automation.active = dict(id="1", job_id=None)
    assert client.patch("/api/automation", json={"channel_login": "other_channel"}).status_code == 409
    application.state.automation.active = None
    assert client.get("/api/automation").json()["channel_login"] == "joaomontagner"


def test_gallery_stable_pagination_legacy_and_missing_files(app):
    application, client, _ = app
    automation = application.state.automation
    service = application.state.service
    poll(automation)
    poll(automation)
    original = service.store.all("clip")[0]
    for index in range(5):
        clone = deepcopy(original)
        clone["id"] = f"pagination-{index}"
        if index == 3:
            clone["preview_file"] = str(service.settings.data_dir / "clips" / "absent.mp4")
        service.store.put("clip", clone)
    first = client.get("/api/gallery?limit=2").json()
    assert len(first["items"]) == 2 and first["next_cursor"]
    assert first["items"][0]["id"] == "pagination-4"
    client.patch("/api/clips/pagination-4", json={"review_status": "approved"})
    second = client.get(f"/api/gallery?limit=2&cursor={first['next_cursor']}").json()
    third = client.get(f"/api/gallery?limit=2&cursor={second['next_cursor']}").json()
    ids = [i["id"] for page in (first, second, third) for i in page["items"]]
    assert len(ids) == len(set(ids)) == 5 and third["next_cursor"] is None
    project = service.require("project", original["project_id"])
    project.pop("source")
    service.store.put("project", project)
    assert client.get("/api/gallery").json()["items"][0]["source"]["type"] == "local"


def test_resume_committed_analysis_and_persisted_evaluation(tmp_path, video, monkeypatch):
    renderer = media.render_clip
    monkeypatch.setattr(media, "render_clip", lambda *a, **k: renderer(*a, **k, width=180, height=320))
    settings = Settings(data_dir=tmp_path / "persistent")
    source = FixtureSource(video)
    first = Service(settings, transcriber=fake_transcriber)
    automation = Automation(first, source)
    poll(automation)
    config = automation.config()
    automation.discover(config)  # Persist ready before simulating a stop between stages.
    record = automation.records("joaomontagner")[0]
    first.create_project(str(video), project_id=record["project_id"])
    job = first.analyze(record["project_id"])
    until(lambda: first.require("job", job["id"])["status"] == "succeeded")
    first.close()
    second = Service(settings, transcriber=lambda *a, **k: pytest.fail("reanalyzed completed transcript"))
    resumed = Automation(second, source)
    try:
        resumed.cycle()
        assert not source.downloads
        assert len(second.store.project_summaries()) == 1
        item = second.gallery()["items"][0]
        from ai_stream_editor.schemas import ClipPatch
        second.patch_clip(item["id"], ClipPatch(review_status="approved"))
    finally:
        second.close()
    third = Service(settings, transcriber=fake_transcriber)
    try:
        assert third.gallery("approved")["items"][0]["id"] == item["id"]
        assert len(third.store.all("job")) == 2
        assert Automation(third, source).records("joaomontagner")[0]["state"] == "completed"
    finally:
        third.close()


def test_supervisor_single_start_empty_channel_and_stop(app):
    application, _, source = app
    source.entries = []
    automation = application.state.automation
    automation.start()
    thread = automation.thread
    automation.start()
    assert automation.thread is thread
    until(lambda: automation.view()["last_checked_at"])
    view = automation.view()
    assert view["status"] == "waiting" and view["runtime_active"]
    assert source.discoveries == 1
    automation.close()
    assert not thread.is_alive()


def test_discovery_failure_is_attention_not_empty_and_backoff(app):
    application, _, source = app
    automation = application.state.automation
    source.discover = lambda *a: (_ for _ in ()).throw(SourceError("Falha controlada de rede"))
    poll(automation)
    assert automation.status == "attention"
    first = automation.config()["next_poll_at"]
    assert first > time.time()
    poll(automation)
    assert automation.config()["next_poll_at"] > first + 290
    source.discover = lambda *a: (_ for _ in ()).throw(SourceError("Dependência ausente", configuration=True))
    poll(automation)
    assert automation.status == "configuration_required"


def test_restart_before_next_poll_is_waiting_not_stopped(app):
    application, _, source = app
    automation = application.state.automation
    config = automation.config()
    config["next_poll_at"] = time.time() + 300
    automation.service.store.put("automation", config)
    automation.start()
    try:
        assert automation.view()["status"] == "waiting"
        assert automation.view()["runtime_active"]
        assert not source.discoveries
    finally:
        automation.close()


def test_disabled_during_queue_selection_does_not_start_new_download(app, monkeypatch):
    application, _, source = app
    automation = application.state.automation
    poll(automation)
    automation.discover(automation.config())
    original = automation.records
    disabled = False

    def records(login):
        nonlocal disabled
        result = original(login)
        if not disabled:
            disabled = True
            automation.configure(dict(enabled=False))
        return result

    monkeypatch.setattr(automation, "records", records)
    automation.cycle()
    assert not source.downloads and not automation.config()["enabled"]


def test_concurrent_cycle_and_shutdown_download_are_bounded(app):
    application, _, source = app
    automation = application.state.automation
    entered = threading.Event()
    release = threading.Event()

    def blocked_discovery(login, cancel):
        entered.set()
        release.wait(3)
        return []

    source.discover = blocked_discovery
    automation.start()
    assert entered.wait(3)
    automation.cycle()  # Must not launch a second discovery.
    release.set()
    until(lambda: automation.config().get("last_checked_at"))
    automation.close()
    automation.stop.clear()
    source.discover = lambda *a: [entry("5")]
    poll(automation)
    config = automation.config()
    automation.discover(config)
    started = threading.Event()

    def blocked_download(login, record, cancel):
        started.set()
        assert cancel.wait(3)
        raise SourceError("Canceled fixture")

    source.download = blocked_download
    automation.start()
    assert started.wait(3)
    began = time.monotonic()
    automation.close()
    assert time.monotonic() - began < 2
    assert not automation.thread.is_alive()
