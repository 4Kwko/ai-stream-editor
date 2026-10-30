r"""Offline benchmark on generated media, never a quality benchmark on a real VOD.

Run from backend: .venv\Scripts\python.exe tests\benchmark_analysis.py --run-real
No models are downloaded. Evidence is saved in a new .test-data directory.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from threading import Event, Thread, Timer
import time
from uuid import uuid4
import wave

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from ai_stream_editor import analysis, media


class _MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
            "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]


def memory_mib():
    if os.name != "nt":
        return None
    process = ctypes.windll.kernel32.GetCurrentProcess
    process.restype = wintypes.HANDLE
    counters = _MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    if not query(process(), ctypes.byref(counters), counters.cb):
        return None
    return {"working_set_mib": counters.WorkingSetSize / 1024 ** 2,
            "private_mib": counters.PrivateUsage / 1024 ** 2,
            "lifetime_peak_working_set_mib": counters.PeakWorkingSetSize / 1024 ** 2}


def measure(name, action, measurements):
    stop = Event()
    samples = []

    def sample():
        while not stop.is_set():
            value = memory_mib()
            if value is not None:
                samples.append(value)
            stop.wait(.05)

    before = memory_mib()
    sampler = Thread(target=sample, daemon=True)
    sampler.start()
    start, cpu_start = time.perf_counter(), time.process_time()
    print(f"START {name}", flush=True)
    try:
        return action()
    finally:
        stop.set()
        sampler.join(timeout=2)
        after = memory_mib()
        measurement = {"wall_seconds": round(time.perf_counter() - start, 4),
                       "python_process_cpu_seconds": round(time.process_time() - cpu_start, 4),
                       "memory_before": before, "memory_after": after,
                       "peak_sampled_working_set_mib": round(max(s["working_set_mib"] for s in samples), 3) if samples else None,
                       "peak_sampled_private_mib": round(max(s["private_mib"] for s in samples), 3) if samples else None}
        measurements[name] = measurement
        print("DONE " + name + " " + json.dumps(measurement), flush=True)


def ffmpeg(args, timeout=180):
    completed = subprocess.run(["ffmpeg", "-nostdin", "-n", "-hide_banner", "-loglevel", "error", *args],
                               capture_output=True, timeout=timeout)
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace")[-2000:])


def fixture(folder: Path, source: Path, duration: float, layout: str = "sparse"):
    if layout not in {"sparse", "continuous"}:
        raise ValueError("Choose sparse or continuous synthetic speech layout.")
    normalized = folder / "speech-16k.wav"
    ffmpeg(["-i", str(source), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(normalized)])
    with wave.open(str(normalized), "rb") as speech:
        params = speech.getparams()
        data = speech.readframes(speech.getnframes())
        speech_frames = speech.getnframes()
    if speech_frames == 0:
        raise ValueError("Synthetic speech fixture is empty.")
    total_frames = int(duration * 16000)
    if layout == "continuous":
        starts = range(0, total_frames, speech_frames)
    else:
        starts = [s * 16000 for s in (4, 94, 184, 294, 404, 494, 594)
                  if s * 16000 + speech_frames <= total_frames]
    audio = folder / "fixture-ptbr.wav"
    events = []
    with wave.open(str(audio), "wb") as output:
        output.setparams(params)
        written = 0
        for target in starts:
            while written < target:
                count = min(16000, target - written)
                output.writeframesraw(b"\0\0" * count)
                written += count
            count = min(speech_frames, total_frames - written)
            output.writeframesraw(data[:count * 2])
            written += count
            events.append({"start_seconds": target / 16000, "end_seconds": written / 16000,
                           "kind": "repeated_synthetic_ptbr_speech", "partial": count < speech_frames})
        while written < total_frames:
            count = min(16000, total_frames - written)
            output.writeframesraw(b"\0\0" * count)
            written += count
    video = folder / "fixture-ptbr-10min.mp4"
    ffmpeg(["-f", "lavfi", "-i", f"testsrc2=size=320x180:rate=8:duration={duration}",
            "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-t", str(duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "48k", str(video)], timeout=max(180, int(duration)))
    return video, events


def cancellation_probe(audio, model_dir, model_name):
    cancel = Event()
    requested = []
    start = time.perf_counter()

    def request():
        requested.append(time.perf_counter())
        cancel.set()

    timer = Timer(.05, request)
    timer.start()
    try:
        analysis.transcribe(audio, model_dir, model_name=model_name, cancel=cancel)
        return {"cancelled": False, "limitation": "Recognition completed before cancellation was observed."}
    except analysis.AnalysisError as exc:
        if not requested or "cancelado" not in str(exc):
            raise
        return {"cancelled": True, "request_after_seconds": round(requested[0] - start, 4),
                "request_to_return_seconds": round(time.perf_counter() - requested[0], 4),
                "message": str(exc),
                "scope": "warm model; cooperative check after native work returns, not immediate native interruption"}
    finally:
        timer.cancel()
        timer.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-real", action="store_true", help="Run existing offline model and FFmpeg.")
    parser.add_argument("--model-dir", type=Path,
                        default=Path.home() / "AppData/Local/AIStreamEditor/models")
    parser.add_argument("--model", choices=["tiny", "base", "small"], default="base")
    parser.add_argument("--duration", type=int, default=630)
    parser.add_argument("--speech-layout", choices=["sparse", "continuous"], default="sparse",
                        help="Continuous repeats the same synthetic utterance without added silence; not a real VOD.")
    parser.add_argument("--render-width", type=int, default=360)
    parser.add_argument("--render-height", type=int, default=640)
    args = parser.parse_args()
    if not args.run_real:
        parser.error("Explicitly pass --run-real; this performs real local processing.")
    if not 600 <= args.duration <= 900:
        parser.error("Use a synthetic duration from 600 to 900 seconds.")
    if args.render_width < 160 or args.render_width > 1080 or args.render_width % 2:
        parser.error("Render width must be even, from 160 to 1080.")
    if args.render_height * 9 != args.render_width * 16 or args.render_height % 2:
        parser.error("Use an even 9:16 render size, e.g. 360x640 or 1080x1920.")
    if not (args.model_dir / args.model / "model.bin").is_file():
        parser.error("The specified local model is absent. No download was attempted.")
    source = BACKEND / ".test-data/smoke/speech.wav"
    if not source.is_file():
        parser.error("The explicitly synthetic smoke/speech.wav is absent; no personal media is searched.")
    folder = BACKEND / ".test-data/analysis-validation" / ("run-" + uuid4().hex[:10])
    folder.mkdir(parents=True)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    measurements = {}
    evidence = {"created_at": datetime.now(timezone.utc).isoformat(),
                "fixture_kind": "artificial repeated Maria PT-BR utterance + testsrc2; not a real VOD",
                "speech_layout": args.speech_layout,
                "layout_note": "Continuous means no added silence between copies; pauses inside the original utterance remain.",
                "source_speech": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "platform": platform.platform(), "python": platform.python_version(),
                "logical_cpu_count": os.cpu_count(), "recognizer_cpu_threads": min(4, os.cpu_count() or 1),
                "model": args.model, "model_dir": str(args.model_dir), "device": "cpu", "compute_type": "int8",
                "versions": {name: importlib.metadata.version(name) for name in ["faster-whisper", "ctranslate2", "numpy"]},
                "memory_scope": "Python benchmark process incl. native recognition libraries; excludes FFmpeg child process; 50ms samples",
                "measurements": measurements}
    report = folder / "evidence.json"
    print("EVIDENCE " + str(report), flush=True)
    try:
        video, events = measure("fixture_generation", lambda: fixture(folder, source, args.duration, args.speech_layout), measurements)
        inserted_seconds = sum(event["end_seconds"] - event["start_seconds"] for event in events)
        evidence.update(events=events, source_video=str(video), input_media=media.probe_video(video),
                        inserted_utterance_seconds=round(inserted_seconds, 6),
                        inserted_utterance_ratio=round(inserted_seconds / args.duration, 6),
                        coverage_note="Inserted utterance spans, not measured voice activity or unique speech content.")
        report.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
        extracted = folder / "extracted.wav"
        measure("extraction", lambda: media.extract_audio(video, extracted), measurements)
        progress = []
        def on_progress(value):
            progress.append(value)
        transcript = measure("transcription", lambda: analysis.transcribe(extracted, args.model_dir,
                              model_name=args.model, progress=on_progress), measurements)
        (folder / "transcript.synthetic.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=False), encoding="utf-8")
        suggestions = measure("suggestions", lambda: analysis.suggest_clips(transcript, args.duration), measurements)
        evidence.update(transcript_segments=len(transcript), word_count=sum(len(s["words"]) for s in transcript),
                        suggestions=suggestions, progress_monotonic=progress == sorted(progress),
                        progress_end=progress[-1] if progress else None)
        # Rendering a short diagnostic selection does not claim editorial acceptance.
        first = suggestions[0] if suggestions else {"start_seconds": 2, "end_seconds": 26}
        start, end = first["start_seconds"], first["end_seconds"]
        captions = analysis.captions_for_window(transcript, start, end)
        output = folder / "diagnostic-preview.mp4"
        measure("render", lambda: media.render_clip(video, output, start, end, captions,
                width=args.render_width, height=args.render_height), measurements)
        evidence.update(render_selection="first suggestion" if suggestions else "manual synthetic diagnostic window",
                        render_start_seconds=start, render_end_seconds=end,
                        render_media=media.probe_video(output))
        evidence["native_cancellation"] = measure("cancellation", lambda: cancellation_probe(
            extracted, args.model_dir, args.model), measurements)
        silent = folder / "silence-30s.wav"
        with wave.open(str(silent), "wb") as silence:
            silence.setnchannels(1)
            silence.setsampwidth(2)
            silence.setframerate(16000)
            for _ in range(30):
                silence.writeframesraw(b"\0\0" * 16000)
        silent_transcript = measure("silence_transcription", lambda: analysis.transcribe(
            silent, args.model_dir, model_name=args.model), measurements)
        evidence.update(silence_seconds=30, silence_segments=len(silent_transcript),
                        silence_suggestions=len(analysis.suggest_clips(silent_transcript, 30)),
                        source_preserved=hashlib.sha256(source.read_bytes()).hexdigest() == evidence["source_sha256"],
                        files_bytes={p.name: p.stat().st_size for p in folder.iterdir() if p.is_file() and p != report})
    except Exception as exc:
        evidence["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print("SUCCESS " + str(report), flush=True)


if __name__ == "__main__":
    main()
