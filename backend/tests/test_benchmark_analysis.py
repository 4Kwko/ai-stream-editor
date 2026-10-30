"""Checks PCM scheduling only; container/normalization commands are explicitly stubbed."""

from pathlib import Path
import shutil
import sys
import wave

import pytest

from tests import benchmark_analysis as benchmark


@pytest.mark.parametrize("layout, expected_events", [("sparse", [(4, 7)]),
                                                   ("continuous", [(0, 3), (3, 6), (6, 9), (9, 10)])])
def test_fixture_density_has_exact_duration_and_no_extra_continuous_gap(tmp_path, monkeypatch, layout, expected_events):
    source = tmp_path / "synthetic-pcm.wav"
    with wave.open(str(source), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x64\x00" * 48000)
    folder = tmp_path / "generated"
    folder.mkdir()

    def fake_ffmpeg(args, **kwargs):
        destination = Path(args[-1])
        if destination.suffix == ".wav":
            shutil.copyfile(source, destination)
        else:
            destination.write_bytes(b"explicit unit fixture, not an MP4")

    monkeypatch.setattr(benchmark, "ffmpeg", fake_ffmpeg)
    _, events = benchmark.fixture(folder, source, 10, layout)
    assert [(e["start_seconds"], e["end_seconds"]) for e in events] == expected_events
    with wave.open(str(folder / "fixture-ptbr.wav"), "rb") as audio:
        assert audio.getnframes() == 160000
        pcm = audio.readframes(160000)
    if layout == "continuous":
        assert pcm == b"\x64\x00" * 160000
        assert events[-1]["partial"] is True
    else:
        assert pcm == b"\0\0" * 64000 + b"\x64\x00" * 48000 + b"\0\0" * 48000


def test_unknown_layout_rejected_before_media_commands(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, "ffmpeg", lambda *a, **k: pytest.fail("No commands should execute"))
    with pytest.raises(ValueError, match="layout"):
        benchmark.fixture(tmp_path, tmp_path / "absent.wav", 10, "unknown")


def test_render_dimensions_rejected_before_expensive_recognition(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["benchmark", "--run-real", "--render-width", "126", "--render-height", "224"])
    with pytest.raises(SystemExit) as exc:
        benchmark.main()
    assert exc.value.code == 2
    assert "160" in capsys.readouterr().err
