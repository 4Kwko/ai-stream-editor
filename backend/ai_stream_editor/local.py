"""Start the two known local services without taking ownership of existing ones."""

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time

from .diagnostics import local_response


def service_state(kind: str) -> str:
    port = 8765 if kind == "backend" else 5173
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=.3):
            pass
    except OSError:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", port))
            return "free"
        except OSError:
            return "unavailable"
    try:
        if kind == "backend":
            health = json.loads(local_response("http://127.0.0.1:8765/api/health"))
            recognized = health.get("status") == "ok" and all(key in health for key in (
                "ffmpeg_available", "ffprobe_available", "transcription_available", "model_ready"))
        else:
            html = local_response("http://127.0.0.1:5173/").decode("utf-8", errors="replace")
            recognized = "<title>AI Stream Editor</title>" in html and "/@vite/client" in html
        return "ready" if recognized else "occupied"
    except (OSError, ValueError):
        return "occupied"


def wait_ready(kind: str, process, timeout: float = 30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{kind} terminou antes de ficar disponível. Veja o erro acima.")
        if service_state(kind) == "ready":
            return
        time.sleep(.2)
    raise RuntimeError(f"{kind} não ficou disponível dentro do prazo. Nenhum processo existente será encerrado.")


def stop_owned(process):
    if process.poll() is not None:
        return
    try:
        process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGTERM)
        process.wait(timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        print(f"Processo iniciado aqui ({process.pid}) ainda está encerrando; não foi forçado a terminar.", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Inicializar API e interface locais, sem instalar dependências")
    parser.add_argument("--check-only", action="store_true", help="Conferir portas e dependências sem iniciar nada")
    args = parser.parse_args()
    if os.name == "nt":
        signal.signal(signal.SIGBREAK, signal.default_int_handler)
    root = Path(__file__).resolve().parents[2]
    states = {kind: service_state(kind) for kind in ("backend", "frontend")}
    for kind, state in states.items():
        print(f"{kind}: {state}", flush=True)
    if any(state in {"occupied", "unavailable"} for state in states.values()):
        parser.exit(1, "Porta ocupada por serviço não reconhecido ou inacessível. Não alterei nem encerrei processos.\n")
    node = shutil.which("node")
    vite = root / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"
    if states["frontend"] == "free" and (not node or not vite.is_file()):
        parser.exit(1, "Prepare as dependências do frontend conforme frontend/README.md. Nada foi instalado.\n")
    if args.check_only:
        return
    commands = {
        "backend": [sys.executable, "-m", "ai_stream_editor", "serve"],
        "frontend": [node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
    }
    owned = []
    try:
        for kind in ("backend", "frontend"):
            if states[kind] == "ready":
                print(f"Reutilizando {kind} existente; ele não será encerrado por este inicializador.", flush=True)
                continue
            process = subprocess.Popen(commands[kind], cwd=root / kind,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            owned.append(process)
            wait_ready(kind, process)
        print("Abra http://127.0.0.1:5173. Ctrl+C encerra somente os serviços iniciados aqui.", flush=True)
        while owned:
            if any(process.poll() is not None for process in owned):
                raise RuntimeError("Um dos serviços iniciados terminou. Veja a saída acima e inicie novamente.")
            time.sleep(.5)
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 1
    finally:
        for process in reversed(owned):
            stop_owned(process)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
