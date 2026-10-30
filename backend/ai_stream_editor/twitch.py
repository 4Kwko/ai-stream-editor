"""Public Twitch archives through the pinned yt-dlp, without user configuration."""

import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from . import media


class SourceError(RuntimeError):
    def __init__(self, message, *, retryable=True, configuration=False, deferred=False):
        super().__init__(message)
        self.retryable = retryable
        self.configuration = configuration
        self.deferred = deferred


def channel_login(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9_]{3,25}", value):
        raise ValueError("Informe o login Twitch em minúsculas, sem URL.")
    return value


def vod_id(value):
    value = str(value).removeprefix("v")
    if not re.fullmatch(r"[0-9]{1,24}", value):
        raise SourceError("A Twitch retornou um identificador de VOD inválido.", retryable=False)
    return value


def stop_process(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=10)


class TwitchSource:
    max_bytes = 8 * 1024**3
    reserve_bytes = 2 * 1024**3

    def __init__(self, settings):
        self.settings = settings

    def run(self, arguments, cancel, *, timeout=120, work=None):
        if importlib.util.find_spec("yt_dlp") is None:
            raise SourceError("Prepare a dependência local yt-dlp para buscar VODs.", configuration=True)
        command = [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-plugin-dirs",
                   "--no-cache-dir", "--no-colors", "--quiet", "--socket-timeout", "15",
                   "--retries", "1", "--fragment-retries", "1", *arguments]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(command, stdout=output, stderr=errors,
                                       creationflags=flags, start_new_session=os.name != "nt")
            started = time.monotonic()
            try:
                while process.poll() is None:
                    if cancel.wait(0.2):
                        raise SourceError("Obtenção do VOD interrompida.")
                    if time.monotonic() - started > timeout:
                        raise SourceError("A Twitch não concluiu a operação no prazo. Uma nova tentativa será limitada.")
                    if output.tell() > 6 * 1024**2 or errors.tell() > 1024**2:
                        raise SourceError("A resposta da fonte excedeu o limite.")
                    if work is not None:
                        if shutil.disk_usage(work).free < self.reserve_bytes:
                            raise SourceError("Espaço insuficiente para obter o VOD; preserve ao menos 2 GiB livres.", retryable=False)
                        if sum(p.stat().st_size for p in work.rglob("*") if p.is_file()) > self.max_bytes:
                            raise SourceError("O VOD excedeu o limite local de 8 GiB.", retryable=False)
            finally:
                stop_process(process)
            if work is not None:
                if shutil.disk_usage(work).free < self.reserve_bytes:
                    raise SourceError("Espaço insuficiente após obter o VOD; confira os arquivos locais.", retryable=False)
                if sum(p.stat().st_size for p in work.rglob("*") if p.is_file()) > self.max_bytes:
                    raise SourceError("O VOD excedeu o limite local de 8 GiB.", retryable=False)
            output.seek(0)
            errors.seek(0)
            raw = output.read(6 * 1024**2 + 1)
            diagnostics = errors.read(1024**2 + 1)
            if len(diagnostics) > 1024**2:
                raise SourceError("A resposta da fonte excedeu o limite.")
            diagnostic = diagnostics.decode("utf-8", errors="replace").lower()
            if process.returncode or "warning:" in diagnostic or "error:" in diagnostic:
                restricted = any(token in diagnostic for token in ("403", "401", "subscribers", "login", "log in", "private"))
                raise SourceError("O VOD não está acessível publicamente; nenhuma credencial foi buscada." if restricted else
                                  "Não foi possível consultar ou obter o VOD público. Confira rede e disponibilidade da Twitch.",
                                  retryable=not restricted)
            if len(raw) > 6 * 1024**2:
                raise SourceError("A resposta da fonte excedeu o limite.")
            return raw.decode("utf-8").strip()

    def discover(self, login, cancel):
        login = channel_login(login)
        url = f"https://www.twitch.tv/{login}/videos?filter=archives&sort=time"
        raw = self.run(["--flat-playlist", "--skip-download", "--playlist-end", "50",
                        "--dump-single-json", url], cancel)
        try:
            data = json.loads(raw)
            if data.get("id", "").lower() != login or not isinstance(data.get("entries"), list):
                raise ValueError("unexpected channel response")
            entries = []
            for item in data["entries"][:50]:
                key = vod_id(item["id"])
                duration = float(item.get("duration") or 0)
                if not math.isfinite(duration) or duration <= 0:
                    continue
                entries.append(dict(id=key, title=str(item.get("title") or "Live gravada")[:500],
                                    url=f"https://www.twitch.tv/videos/{key}", duration_seconds=duration))
            return entries
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise SourceError("A Twitch retornou uma lista de VODs inválida.") from exc

    def download(self, login, entry, cancel):
        login = channel_login(login)
        key = vod_id(entry["vod_id"])
        url = f"https://www.twitch.tv/videos/{key}"
        try:
            info = json.loads(self.run(["--skip-download", "--no-playlist", "--dump-single-json", url], cancel))
            if vod_id(info["id"]) != key or str(info.get("uploader_id", "")).lower() != login:
                raise SourceError("O VOD não pertence ao canal configurado.", retryable=False)
            if info.get("is_live") is not False:
                raise SourceError("Aguardando confirmação do término da gravação.", deferred=True)
            duration = float(info.get("duration") or 0)
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("invalid duration")
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceError("Metadados do VOD não puderam ser confirmados.") from exc
        folder = self.settings.data_dir / "downloads" / login / key / uuid4().hex
        folder.mkdir(parents=True, exist_ok=False)
        if shutil.disk_usage(folder).free < self.reserve_bytes:
            raise SourceError("Espaço insuficiente para obter o VOD; preserve ao menos 2 GiB livres.", retryable=False)
        ffmpeg = shutil.which(self.settings.ffmpeg)
        if not ffmpeg:
            raise SourceError("Prepare o FFmpeg local antes de obter VODs.", configuration=True)
        self.run(["--no-playlist", "--no-continue", "--no-overwrites", "--abort-on-unavailable-fragments",
                  "--concurrent-fragments", "1", "--max-filesize", str(self.max_bytes),
                  "--format", "b[height<=720][vcodec!=none][acodec!=none]",
                  "--remux-video", "mp4", "--ffmpeg-location", ffmpeg,
                  "--output", str(folder / "source.%(ext)s"), url], cancel, timeout=7200, work=folder)
        path = folder / "source.mp4"
        if not path.is_file() or cancel.is_set():
            raise SourceError("O download não publicou um MP4 completo.")
        try:
            probe = media.probe_video(path, ffprobe=self.settings.ffprobe)
            if not probe["has_audio"] or abs(probe["duration_seconds"] - duration) > max(2, duration * .02):
                raise SourceError("A mídia obtida está incompleta ou sem áudio; não será analisada.")
        except media.MediaError as exc:
            raise SourceError("A mídia obtida não passou na validação local.") from exc
        return path
