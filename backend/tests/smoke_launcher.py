"""Explicit local smoke: starts only when API is free and reuses existing Vite."""

import json
import argparse
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import time
from uuid import uuid4
from uuid import UUID

from ai_stream_editor.local import service_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-clip", type=UUID, help="Corte sintético já existente para testar desconexão de vídeo")
    args = parser.parse_args()
    if service_state("backend") != "free" or service_state("frontend") != "ready":
        raise SystemExit("Requer porta 8765 livre e frontend reconhecido em 5173; nenhum processo foi alterado.")
    output = Path(".test-data") / f"launcher-{uuid4().hex[:8]}"
    output.mkdir(parents=True)
    log = output / "process.log"
    with log.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen([sys.executable, "-m", "ai_stream_editor.local"],
                                   stdout=stream, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
        try:
            deadline = time.monotonic() + 30
            while service_state("backend") != "ready":
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Inicializador não disponibilizou API; consulte process.log")
                time.sleep(.2)
            if args.preview_clip:
                for _ in range(3):
                    with socket.create_connection(("127.0.0.1", 8765), timeout=2) as client:
                        client.sendall(f"GET /api/clips/{args.preview_clip}/preview HTTP/1.1\r\nHost: 127.0.0.1:8765\r\n\r\n".encode("ascii"))
                        assert b"200 OK" in client.recv(4096)
                        # Abort the partial response like a player changing its source.
                        linger = struct.pack("hh" if os.name == "nt" else "ii", 1, 0)
                        client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
        finally:
            if process.poll() is None:
                process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
                process.wait(timeout=40)
    text = log.read_text(encoding="utf-8", errors="replace")
    evidence = {"launcher_exit_code": process.returncode,
                "backend_after": service_state("backend"), "frontend_after": service_state("frontend"),
                "graceful_api_shutdown": "Application shutdown complete" in text,
                "aborted_preview_requests": 3 if args.preview_clip else 0,
                "connection_reset_traceback": "ConnectionResetError" in text,
                "reused_existing_frontend": "frontend existente" in text}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(dict(evidence, folder=str(output)), indent=2))
    assert evidence["backend_after"] == "free" and evidence["frontend_after"] == "ready"
    assert evidence["graceful_api_shutdown"] and evidence["reused_existing_frontend"]
    assert not evidence["connection_reset_traceback"]


if __name__ == "__main__":
    main()
