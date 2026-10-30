r"""Real isolated shutdown smoke; synthetic media, existing offline model, no installs.

From backend: .venv\Scripts\python.exe tests\smoke_shutdown.py --run-real
Only its own ephemeral-port server receives CTRL_BREAK. Never signals 8765/5173.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
MODEL_DIR = Path(r"C:\Users\jvmon\AppData\Local\AIStreamEditor\models")
SYNTHETIC_VIDEO = BACKEND / ".test-data/analysis-validation/run-8b7cd0b063/fixture-ptbr-10min.mp4"


class _ProcessEntry(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]


def owned_descendants(parent_pid):
    """Inspect PID/parent/name only; retain exclusively descendants of this server."""
    if os.name != "nt":
        return None
    kernel = ctypes.windll.kernel32
    snapshot = kernel.CreateToolhelp32Snapshot
    snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    snapshot.restype = wintypes.HANDLE
    first, following = kernel.Process32FirstW, kernel.Process32NextW
    for function in (first, following):
        function.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry)]
        function.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    handle = snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        return None
    entries = []
    entry = _ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        available = first(handle, ctypes.byref(entry))
        while available:
            entries.append((entry.th32ProcessID, entry.th32ParentProcessID, entry.szExeFile))
            available = following(handle, ctypes.byref(entry))
    finally:
        close(handle)
    owned = {parent_pid}
    result = []
    while True:
        found = [(pid, parent, name) for pid, parent, name in entries if parent in owned and pid not in owned]
        if not found:
            return result
        for pid, parent, name in found:
            owned.add(pid)
            result.append({"pid": pid, "parent_pid": parent, "executable": name})


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=.2):
            return True
    except OSError:
        return False


def native_events(log):
    events = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("SHUTDOWN_SMOKE "):
            events.append(json.loads(line[len("SHUTDOWN_SMOKE "):]))
    return events


def child(port, data_dir):
    import uvicorn
    from ai_stream_editor import analysis
    from ai_stream_editor.api import create_app
    from ai_stream_editor.config import Settings

    load = analysis._load_model

    def emit(event):
        print("SHUTDOWN_SMOKE " + json.dumps({"event": event, "monotonic": time.monotonic()}), flush=True)

    class ObservedNativeModel:
        def __init__(self, native):
            self.native = native

        def transcribe(self, *args, **kwargs):
            iterator, info = self.native.transcribe(*args, **kwargs)

            def observed():
                try:
                    while True:
                        emit("native_next_begin")
                        try:
                            segment = next(iterator)
                        except StopIteration:
                            emit("native_next_end")
                            return
                        emit("native_next_end")
                        yield segment
                finally:
                    iterator.close()

            return observed(), info

    # Observation only: the real cached model, arrays, arguments and segments are unchanged.
    analysis._load_model = lambda path: ObservedNativeModel(load(path))
    settings = Settings(data_dir=data_dir, model_name="base")
    app = create_app(settings)
    uvicorn.run(app, host="127.0.0.1", port=port,
                loop="asyncio:SelectorEventLoop" if sys.platform == "win32" else "asyncio",
                timeout_graceful_shutdown=10, access_log=False)


def run():
    folder = BACKEND / ".test-data" / ("shutdown-" + uuid4().hex[:10])
    folder.mkdir(parents=True)
    data_dir = folder / "data"
    log = folder / "server.log"
    report = folder / "evidence.json"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as free_port:
        free_port.bind(("127.0.0.1", 0))
        port = free_port.getsockname()[1]
    if port in {8765, 5173}:
        raise RuntimeError("The OS selected a protected product port; no server was started.")
    evidence = {"created_at": datetime.now(timezone.utc).isoformat(), "port": port,
                "fixture": str(SYNTHETIC_VIDEO), "fixture_kind": "artificial PT-BR speech, silence and testsrc2; not a real VOD",
                "data_dir": str(data_dir), "model_dir": str(MODEL_DIR), "model": "base",
                "runtime": "real faster-whisper CPU/int8; native generator timing markers only",
                "protected_ports_before": {str(p): port_open(p) for p in (8765, 5173)},
                "forced_cleanup": False, "success": False}
    environment = dict(os.environ, AI_STREAM_DATA_DIR=str(data_dir), AI_STREAM_MODEL_DIR=str(MODEL_DIR),
                       AI_STREAM_MODEL="base", HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
                       PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", PYTHONUNBUFFERED="1")
    opener = build_opener(ProxyHandler({}))

    def api(path, body=None):
        request = Request(f"http://127.0.0.1:{port}" + path,
                          data=json.dumps(body).encode("utf-8") if body is not None else None,
                          headers={"Content-Type": "application/json"} if body is not None else {})
        with opener.open(request, timeout=3) as response:
            return json.load(response)

    process = None
    tracked = {}
    try:
        with log.open("w", encoding="utf-8") as output:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--child",
                                        "--port", str(port), "--data-dir", str(data_dir)],
                                       cwd=BACKEND, env=environment, stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            evidence["server_pid"] = process.pid
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Isolated server exited during startup; see server.log.")
                try:
                    health = api("/api/health")
                    if health.get("status") == "ok":
                        break
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("Isolated API did not become ready within 30 seconds.")
                time.sleep(.05)
            evidence["health"] = health
            project = api("/api/projects", {"source_path": str(SYNTHETIC_VIDEO)})
            job = api(f"/api/projects/{project['id']}/analyze", {})
            evidence.update(project_id=project["id"], job_id=job["id"])
            deadline = time.monotonic() + 30
            while True:
                current = api(f"/api/jobs/{job['id']}")
                descendants = owned_descendants(process.pid)
                if descendants is not None:
                    tracked.update({p["pid"]: p for p in descendants})
                events = native_events(log)
                active = bool(events) and events[-1]["event"] == "native_next_begin"
                if current["status"] == "running" and current["stage"] == "Transcrevendo em PT-BR" and active:
                    evidence["observed_job"] = {key: current.get(key) for key in ("status", "stage", "progress", "started_at")}
                    evidence["native_event_before_signal"] = events[-1]
                    break
                if current["status"] in {"succeeded", "failed", "canceled"}:
                    raise RuntimeError("Analysis ended before an active native decode was observed.")
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("No active native decode observed within 30 seconds.")
                time.sleep(.02)
            started = time.monotonic()
            evidence["signal"] = "CTRL_BREAK_EVENT" if os.name == "nt" else "SIGTERM"
            process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGTERM)
            process.wait(timeout=30)
            evidence.update(shutdown_seconds=round(time.monotonic() - started, 4),
                            server_exit_code=process.returncode, port_closed=not port_open(port))
        text = log.read_text(encoding="utf-8", errors="replace")
        evidence["graceful_shutdown_logged"] = "Application shutdown complete" in text
        evidence["traceback_logged"] = "Traceback (most recent call last)" in text
        evidence["native_events"] = native_events(log)
        evidence["tracked_owned_descendants"] = list(tracked.values())
        evidence["remaining_owned_descendants"] = owned_descendants(process.pid)
        evidence["descendant_check"] = "Windows Toolhelp PID/parent/name filtered to this server; no CIM or command lines"
        # Read the private DB before creating Service; recovery must not mask shutdown failure.
        with sqlite3.connect((data_dir / "projects.sqlite3").as_uri() + "?mode=ro", uri=True) as database:
            row = database.execute("SELECT data FROM records WHERE kind='job' AND id=?", (job["id"],)).fetchone()
            saved = json.loads(row[0])
            project_row = database.execute("SELECT data FROM records WHERE kind='project' AND id=?", (project["id"],)).fetchone()
            saved_project = json.loads(project_row[0])
            clip_count = database.execute("SELECT count(*) FROM records WHERE kind='clip'").fetchone()[0]
        evidence["persisted_job_before_reopen"] = {key: saved.get(key) for key in (
            "id", "status", "stage", "error", "result", "started_at", "finished_at", "elapsed_seconds")}
        evidence.update(database_read_before_recovery=True, transcript_saved_before_reopen=saved_project["transcript"] is not None,
                        clips_saved_before_reopen=clip_count)
        assert saved["status"] == "canceled", "Shutdown did not persist cancellation before recovery."
        assert saved_project["transcript"] is None and clip_count == 0
        assert evidence["port_closed"] and evidence["graceful_shutdown_logged"]
        assert not evidence["traceback_logged"]
        assert evidence["remaining_owned_descendants"] == [], "Owned descendants remain or process inspection unavailable."
        from ai_stream_editor.config import Settings
        from ai_stream_editor.service import Service
        reopened = Service(Settings(data_dir=data_dir))
        try:
            evidence["instance_lock_reacquired_after_proof"] = True
            evidence["status_after_reopen"] = reopened.require("job", job["id"])["status"]
        finally:
            reopened.close()
        evidence["success"] = True
    except Exception as exc:
        evidence["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if process is not None and process.poll() is None:
            try:
                process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGTERM)
                process.wait(timeout=30)
            except (OSError, subprocess.TimeoutExpired):
                evidence["forced_cleanup"] = True
                process.kill()  # Only the exact isolated child created by this test.
                process.wait(timeout=10)
        evidence["protected_ports_after"] = {str(p): port_open(p) for p in (8765, 5173)}
        report.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
        print("EVIDENCE " + str(report), flush=True)
        print(json.dumps(evidence, ensure_ascii=False, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-real", action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--data-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        if not args.data_dir or not args.port or args.port in {8765, 5173}:
            parser.error("The isolated child requires private data and an unprotected port.")
        child(args.port, args.data_dir)
        return
    if not args.run_real:
        parser.error("Explicitly pass --run-real for the isolated local integration test.")
    if os.name != "nt":
        parser.error("This smoke validates Windows CTRL_BREAK and requires Windows.")
    if not (MODEL_DIR / "base/model.bin").is_file() or not SYNTHETIC_VIDEO.is_file():
        parser.error("Existing offline base model or explicitly synthetic fixture absent; no downloads attempted.")
    run()


if __name__ == "__main__":
    main()
