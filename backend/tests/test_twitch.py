"""Provider boundaries are controlled; no test here queries Twitch."""

import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from ai_stream_editor.config import Settings
from ai_stream_editor import twitch
from ai_stream_editor.twitch import SourceError, TwitchSource, channel_login


@pytest.fixture
def source(tmp_path):
    return TwitchSource(Settings(data_dir=tmp_path / "data"))


def test_discovery_canonical_ids_urls_and_bounded_command(source, monkeypatch):
    commands = []

    def run(arguments, cancel):
        commands.append(arguments)
        return json.dumps(dict(id="joaomontagner", entries=[dict(id="v123", title="Teste", duration=30)]))

    monkeypatch.setattr(source, "run", run)
    result = source.discover("joaomontagner", threading.Event())
    assert result == [dict(id="123", title="Teste", url="https://www.twitch.tv/videos/123", duration_seconds=30)]
    assert "--flat-playlist" in commands[0] and commands[0][commands[0].index("--playlist-end") + 1] == "50"
    assert commands[0][-1] == "https://www.twitch.tv/joaomontagner/videos?filter=archives&sort=time"


@pytest.mark.parametrize("value", ["../secret", "a/b", "HTTP://twitch.tv/foo", "UPPER", "ab", ""])
def test_channel_rejects_urls_and_paths(value):
    with pytest.raises(ValueError):
        channel_login(value)


@pytest.mark.parametrize("response", ["not json", '{"id":"another","entries":[]}',
                                    '{"id":"joaomontagner","entries":null}',
                                    '{"id":"joaomontagner","entries":[{"id":"../../foo","duration":20}]}'])
def test_invalid_discovery_not_claimed_empty(source, monkeypatch, response):
    monkeypatch.setattr(source, "run", lambda *a, **k: response)
    with pytest.raises(SourceError):
        source.discover("joaomontagner", threading.Event())


@pytest.mark.parametrize("owner,is_live,deferred", [("other", False, False), ("joaomontagner", True, True),
                                                  ("joaomontagner", None, True)])
def test_owner_and_finalization_before_download(source, monkeypatch, owner, is_live, deferred):
    calls = []

    def run(arguments, cancel, **kwargs):
        calls.append(arguments)
        return json.dumps(dict(id="v123", uploader_id=owner, is_live=is_live, duration=30))

    monkeypatch.setattr(source, "run", run)
    with pytest.raises(SourceError) as caught:
        source.download("joaomontagner", dict(vod_id="123"), threading.Event())
    assert caught.value.deferred == deferred and len(calls) == 1
    assert not source.settings.data_dir.exists()


def test_partial_download_is_not_accepted(source, monkeypatch):
    calls = []

    def run(arguments, cancel, **kwargs):
        calls.append(arguments)
        if "--dump-single-json" in arguments:
            return json.dumps(dict(id="123", uploader_id="joaomontagner", is_live=False, duration=30))
        (kwargs["work"] / "source.mp4.part").write_bytes(b"partial")
        return ""

    monkeypatch.setattr(source, "run", run)
    with pytest.raises(SourceError, match="completo"):
        source.download("joaomontagner", dict(vod_id="123"), threading.Event())
    assert len(calls) == 2
    assert "--abort-on-unavailable-fragments" in calls[1]
    assert "--no-continue" in calls[1] and "--no-overwrites" in calls[1]


def test_missing_dependency_is_configuration_required(source, monkeypatch):
    monkeypatch.setattr(twitch.importlib.util, "find_spec", lambda _: None)
    with pytest.raises(SourceError) as caught:
        source.run([], threading.Event())
    assert caught.value.configuration


def test_warnings_do_not_hide_failed_discovery(source, monkeypatch):
    original = subprocess.Popen

    def spawn(command, **kwargs):
        if "yt_dlp" in command:
            command = [sys.executable, "-c", "import sys; print('{}'); print('WARNING: failed API request',file=sys.stderr)"]
        return original(command, **kwargs)

    monkeypatch.setattr(twitch.subprocess, "Popen", spawn)
    with pytest.raises(SourceError, match="consultar"):
        source.run([], threading.Event())


def test_timeout_is_bounded(source, monkeypatch):
    original = subprocess.Popen

    def spawn(command, **kwargs):
        if "yt_dlp" in command:
            command = [sys.executable, "-c", "import time; time.sleep(60)"]
        return original(command, **kwargs)

    monkeypatch.setattr(twitch.subprocess, "Popen", spawn)
    start = time.monotonic()
    with pytest.raises(SourceError, match="prazo"):
        source.run([], threading.Event(), timeout=.1)
    assert time.monotonic() - start < 5


def test_quota_also_checked_after_fast_process_exit(source, monkeypatch, tmp_path):
    original = subprocess.Popen
    source.max_bytes = 10
    source.reserve_bytes = 0

    def spawn(command, **kwargs):
        if "yt_dlp" in command:
            script = f"from pathlib import Path; Path({str(tmp_path / 'large.part')!r}).write_bytes(b'x'*1000)"
            command = [sys.executable, "-c", script]
        return original(command, **kwargs)

    monkeypatch.setattr(twitch.subprocess, "Popen", spawn)
    with pytest.raises(SourceError, match="limite local"):
        source.run([], threading.Event(), work=tmp_path)


def test_cancellation_terminates_owned_subprocess_tree(source, monkeypatch, tmp_path):
    child_file = tmp_path / "child-pid.json"
    original = subprocess.Popen
    commands = []
    script = ("import subprocess,sys,time,pathlib; "
              "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
              f"pathlib.Path({str(child_file)!r}).write_text(str(p.pid)); time.sleep(60)")

    def spawn(command, **kwargs):
        commands.append(command)
        if "yt_dlp" in command:
            command = [sys.executable, "-c", script]
        return original(command, **kwargs)

    monkeypatch.setattr(twitch.subprocess, "Popen", spawn)
    cancel = threading.Event()
    errors = []

    def run():
        try:
            source.run([], cancel)
        except SourceError as exc:
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    deadline = time.monotonic() + 5
    while not child_file.exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert child_file.exists()
    child_pid = int(child_file.read_text())
    handle = None
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100000, False, child_pid)
    cancel.set()
    worker.join(8)
    assert not worker.is_alive() and errors
    if handle:
        try:
            assert kernel.WaitForSingleObject(handle, 3000) == 0
        finally:
            kernel.CloseHandle(handle)
    first = commands[0]
    assert "--ignore-config" in first and "--no-plugin-dirs" in first and "--no-cache-dir" in first
    assert "--cookies-from-browser" not in first and "--netrc" not in first
