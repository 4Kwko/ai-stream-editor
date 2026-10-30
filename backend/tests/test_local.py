from unittest.mock import Mock
import subprocess

import pytest

from ai_stream_editor import local


@pytest.mark.parametrize("kind,payload,expected", [
    ("backend", b'{"status":"ok","ffmpeg_available":true,"ffprobe_available":true,"transcription_available":true,"model_ready":false}', "ready"),
    ("backend", b'{"status":"ok"}', "occupied"),
    ("backend", b'not json', "occupied"),
    ("frontend", b'<title>AI Stream Editor</title><script src="/@vite/client"></script>', "ready"),
    ("frontend", b'<title>Another app</title>', "occupied"),
])
def test_recognizes_only_expected_services(monkeypatch, kind, payload, expected):
    monkeypatch.setattr(local.socket, "create_connection", lambda *a, **k: Mock(__enter__=Mock(), __exit__=Mock()))
    monkeypatch.setattr(local, "local_response", lambda *a: payload)
    assert local.service_state(kind) == expected


def test_port_access_denied_is_not_treated_as_free(monkeypatch):
    def denied(*a, **k):
        raise PermissionError("socket denied")
    monkeypatch.setattr(local.socket, "create_connection", denied)
    monkeypatch.setattr(local.socket, "socket", denied)
    assert local.service_state("backend") == "unavailable"


def test_timeout_on_unused_windows_port_can_be_verified_by_binding(monkeypatch):
    def timed_out(*a, **k):
        raise TimeoutError("fixture")
    probe = Mock(__enter__=Mock(), __exit__=Mock())
    monkeypatch.setattr(local.socket, "create_connection", timed_out)
    monkeypatch.setattr(local.socket, "socket", lambda *a: probe)
    assert local.service_state("backend") == "free"
    probe.__enter__.return_value.bind.assert_called_once_with(("127.0.0.1", 8765))


def test_stops_only_given_live_process_and_never_force_kills():
    process = Mock(pid=123)
    process.poll.return_value = None
    process.wait.side_effect = subprocess.TimeoutExpired("fixture", 30)
    local.stop_owned(process)
    process.send_signal.assert_called_once()
    process.kill.assert_not_called()
    process.terminate.assert_not_called()
    process.reset_mock()
    process.poll.return_value = 0
    local.stop_owned(process)
    process.send_signal.assert_not_called()


def test_wait_detects_early_exit():
    process = Mock()
    process.poll.return_value = 1
    with pytest.raises(RuntimeError, match="terminou"):
        local.wait_ready("backend", process)
