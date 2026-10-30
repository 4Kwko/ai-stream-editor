"""Real FFmpeg, controlled face boxes/ASR; no Twitch requests."""

from copy import deepcopy
import hashlib
import subprocess

from fastapi.testclient import TestClient
import pytest

from ai_stream_editor import camera, media
from ai_stream_editor.api import create_app
from ai_stream_editor.config import Settings
from ai_stream_editor.store import Store
from ai_stream_editor.twitch import SourceError
from test_api import fake_transcriber, video, wait_job
from test_automation import FixtureSource, poll


@pytest.fixture
def app(tmp_path, monkeypatch, video):
    render = media.render_clip
    monkeypatch.setattr(media, "render_clip", lambda *a, **k: render(*a, **k, width=180, height=320))
    application = create_app(Settings(data_dir=tmp_path / "data"), transcriber=fake_transcriber,
                             automation_source=FixtureSource(video))
    with TestClient(application, base_url="http://127.0.0.1:8765") as client:
        yield application, client


def analyze(client, video):
    project = client.post("/api/projects", json=dict(source_path=str(video))).json()
    assert wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))["status"] == "succeeded"
    clip = client.get(f"/api/projects/{project['id']}/clips").json()[0]
    return project, clip


def test_default_landscape_preserves_full_source_and_never_runs_camera(app, video, monkeypatch):
    application, client = app
    monkeypatch.setattr(camera, "detect", lambda *a, **k: pytest.fail("camera ran in 16:9"))
    original_hash = hashlib.sha256(video.read_bytes()).hexdigest()
    assert client.get("/api/automation").json()["output_format"] == "16:9"
    project, clip = analyze(client, video)
    assert project["output_format"] == clip["output_format"] == "16:9"
    job = wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))
    assert job["status"] == "succeeded", job
    assert job["result"]["layout"] == "source_preserved"
    output = application.state.service.preview(clip["id"])
    probe = media.probe_video(output)
    assert (probe["width"], probe["height"]) == (320, 180) and probe["has_audio"]
    gallery = client.get("/api/gallery").json()["items"][0]
    assert gallery["output_format"] == "16:9" and gallery["layout"] == "source_preserved"
    assert gallery["layout_warning"] is None
    assert hashlib.sha256(video.read_bytes()).hexdigest() == original_hash


def test_vertical_camera_layout_and_config_changes_preserve_existing_profile(app, video, monkeypatch):
    application, client = app
    monkeypatch.setattr(camera, "detect", lambda *a, **k: (dict(x=0, y=0, width=.25, height=.5), "detected"))
    assert client.patch("/api/automation", json=dict(output_format="9:16")).status_code == 200
    project = client.post("/api/projects", json=dict(source_path=str(video))).json()
    client.patch("/api/automation", json=dict(output_format="16:9"))
    assert wait_job(client, client.post(f"/api/projects/{project['id']}/analyze"))["status"] == "succeeded"
    clip = client.get(f"/api/projects/{project['id']}/clips").json()[0]
    assert clip["output_format"] == "9:16"
    job = wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))
    assert job["status"] == "succeeded", job
    assert job["result"]["layout"] == "camera_top_content_bottom"
    assert job["result"]["layout_warning"] is None
    output = application.state.service.preview(clip["id"])
    probe = media.probe_video(output)
    assert (probe["width"], probe["height"]) == (180, 320)
    before = hashlib.sha256(output.read_bytes()).hexdigest()
    count = len(application.state.service.store.all("job"))
    client.patch("/api/automation", json=dict(output_format="9:16"))
    client.patch("/api/automation", json=dict(output_format="16:9"))
    client.patch(f"/api/clips/{clip['id']}", json=dict(review_status="approved"))
    assert len(application.state.service.store.all("job")) == count
    assert hashlib.sha256(output.read_bytes()).hexdigest() == before
    assert client.get("/api/gallery").json()["items"][0]["output_format"] == "9:16"


@pytest.mark.parametrize("reason", ["not_detected", "ambiguous", "unavailable", "timeout"])
def test_vertical_without_reliable_face_preserves_content_and_warns(app, video, monkeypatch, reason):
    _, client = app
    monkeypatch.setattr(camera, "detect", lambda *a, **k: (None, reason))
    client.patch("/api/automation", json=dict(output_format="9:16"))
    _, clip = analyze(client, video)
    job = wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))
    assert job["status"] == "succeeded", job
    item = client.get("/api/gallery").json()["items"][0]
    assert item["output_format"] == "9:16" and item["layout"] == "full_frame"
    assert item["layout_warning"]


def test_legacy_clips_stay_vertical_without_new_camera_detection(app, video, monkeypatch):
    application, client = app
    project, clip = analyze(client, video)
    service = application.state.service
    legacy = service.require("clip", clip["id"])
    legacy.pop("output_format")
    legacy.pop("camera_mode")
    service.store.put("clip", legacy)
    monkeypatch.setattr(camera, "detect", lambda *a, **k: pytest.fail("legacy profile changed"))
    job = wait_job(client, client.post(f"/api/clips/{clip['id']}/render"))
    assert job["status"] == "succeeded", job
    item = client.get("/api/gallery").json()["items"][0]
    assert item["output_format"] == "9:16" and item["layout"] == "full_frame"
    assert item["layout_warning"] is None


@pytest.mark.parametrize("value", ["4:3", "horizontal", "16/9", None])
def test_invalid_configuration_never_changes_format(app, value):
    _, client = app
    assert client.patch("/api/automation", json=dict(output_format=value)).status_code == 422
    assert client.get("/api/automation").json()["output_format"] == "16:9"


def test_configuration_migration_keeps_channel_and_pause(tmp_path):
    settings = Settings(data_dir=tmp_path / "legacy")
    store = Store(settings.data_dir)
    store.put("automation", dict(id="source", channel_login="joaomontagner", enabled=False,
                                  last_checked_at=None, next_poll_at=0))
    application = create_app(settings, transcriber=fake_transcriber)
    with TestClient(application, base_url="http://127.0.0.1:8765") as client:
        view = client.get("/api/automation").json()
        assert view["output_format"] == "16:9" and not view["enabled"]
        assert view["channel_login"] == "joaomontagner"


def test_vod_retry_keeps_format_captured_at_start(app, monkeypatch):
    application, client = app
    auto = application.state.automation
    source = auto.source
    download = source.download
    failed_once = False

    def fail_once(*args):
        nonlocal failed_once
        if not failed_once:
            failed_once = True
            raise SourceError("Transient fixture failure")
        return download(*args)

    monkeypatch.setattr(source, "download", fail_once)
    monkeypatch.setattr(camera, "detect", lambda *a, **k: (None, "not_detected"))
    client.patch("/api/automation", json=dict(output_format="9:16"))
    poll(auto)
    poll(auto)
    record = auto.records("joaomontagner")[0]
    assert record["output_format"] == "9:16" and record["state"] == "queued"
    client.patch("/api/automation", json=dict(output_format="16:9"))
    auto.save(record, next_attempt_at=0)
    auto.cycle()
    item = client.get("/api/gallery").json()["items"][0]
    assert item["output_format"] == "9:16"
    assert auto.records("joaomontagner")[0]["state"] == "completed"


def test_real_camera_stack_pixels_and_original_preserved(tmp_path):
    source = tmp_path / "synthetic-camera.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "color=blue:s=320x180:r=10,drawbox=x=0:y=0:w=80:h=90:color=red:t=fill",
                    "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)], check=True, timeout=20)
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "stack.mp4"
    media.render_clip(source, output, 0, 1, [], width=180, height=320,
                      camera_box=dict(x=0, y=0, width=.25, height=.5))
    frame = subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-frames:v", "1", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "pipe:1"], capture_output=True, check=True, timeout=20).stdout
    def pixel(x, y):
        return frame[(y * 180 + x) * 3:(y * 180 + x) * 3 + 3]
    r, g, b = pixel(90, 40)
    assert r > 200 and g < 50 and b < 50  # Controlled camera is above.
    r, g, b = pixel(90, 210)
    assert b > 200 and r < 50 and g < 50  # Full blue content remains below.
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original


@pytest.mark.parametrize("box", [dict(x=-.1,y=0,width=.2,height=.2), dict(x=.9,y=0,width=.2,height=.2),
                               dict(x=0,y=0,width=float("nan"),height=.2), dict(x=0,y=0,width=0,height=.2), {}])
def test_bad_camera_coordinates_rejected_before_publish(tmp_path, video, box):
    output = tmp_path / "invalid.mp4"
    with pytest.raises(media.MediaError):
        media.render_clip(video, output, 0, 1, [], camera_box=box)
    assert not output.exists()
