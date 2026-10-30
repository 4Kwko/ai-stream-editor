"""Local FFmpeg operations; source files are never changed."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import queue
import re
import subprocess
import tempfile
import textwrap
import threading
import time
from collections.abc import Callable
from fractions import Fraction


class MediaError(RuntimeError):
    pass


_STALL_TIMEOUT_SECONDS = 120


def _local_source(source: Path) -> Path:
    raw = os.fspath(source)
    if not raw or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw) or raw.startswith(("\\\\", "//")):
        raise MediaError("Informe um arquivo local, não uma URL ou caminho de rede.")
    try:
        path = Path(raw).expanduser().resolve(strict=True)
        regular = path.is_file()
    except (OSError, ValueError, RuntimeError) as exc:
        raise MediaError("O arquivo de origem não foi encontrado.") from exc
    if str(path).startswith(("\\\\", "//")) or not regular:
        raise MediaError("A origem precisa ser um arquivo local regular.")
    return path


def _probe(source: Path, selection: str, entries: str, ffprobe: str) -> dict:
    command = [ffprobe, "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", selection,
               "-show_entries", entries, "-of", "json", str(source)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=30, check=False,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError as exc:
        raise MediaError("FFprobe não encontrado. Instale ou configure o FFmpeg local.") from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaError("Não foi possível inspecionar o vídeo em até 30 segundos.") from exc
    if result.returncode or len(result.stdout) > 200_000:
        raise MediaError("O arquivo não pôde ser lido como mídia válida.")
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeError) as exc:
        raise MediaError("FFprobe retornou metadados inválidos.") from exc


def probe_video(source: Path, *, ffprobe: str = "ffprobe") -> dict:
    source = _local_source(source)
    data = _probe(source, "v:0", "stream=width,height,avg_frame_rate,duration,sample_aspect_ratio:stream_side_data=rotation:stream_tags=rotate:format=duration", ffprobe)
    videos = data.get("streams", [])
    if not videos:
        raise MediaError("O arquivo não contém uma faixa de vídeo.")
    video = videos[0]
    try:
        duration = 0.0
        for candidate in (data.get("format", {}).get("duration"), video.get("duration")):
            try:
                duration = float(candidate)
                if math.isfinite(duration) and duration > 0:
                    break
            except (TypeError, ValueError, OverflowError):
                duration = 0.0
        width, height = int(video.get("width", 0)), int(video.get("height", 0))
        if not math.isfinite(duration) or duration <= 0 or width <= 0 or height <= 0:
            raise ValueError("invalid dimensions or duration")
        try:
            fps = float(Fraction(video.get("avg_frame_rate", "0/1")))
        except (ValueError, ZeroDivisionError):
            fps = 0.0
        if not math.isfinite(fps) or fps < 0:
            fps = 0.0
        rotation = video.get("tags", {}).get("rotate", 0)
        for side_data in video.get("side_data_list", []):
            if "rotation" in side_data:
                rotation = side_data["rotation"]
                break
        try:
            rotation = float(rotation) % 360
            if not math.isfinite(rotation):
                rotation = 0.0
        except (TypeError, ValueError, OverflowError):
            rotation = 0.0
        try:
            aspect = float(Fraction(str(video.get("sample_aspect_ratio", "1:1")).replace(":", "/")))
            if not math.isfinite(aspect) or aspect <= 0:
                aspect = 1.0
        except (ValueError, ZeroDivisionError):
            aspect = 1.0
        display_width, display_height = max(1, round(width * aspect)), height
        if abs(rotation - 90) < 0.01 or abs(rotation - 270) < 0.01:
            display_width, display_height = display_height, display_width
    except (TypeError, ValueError, OverflowError) as exc:
        raise MediaError("O vídeo precisa ter duração e dimensões válidas.") from exc
    audio = _probe(source, "a:0", "stream=index", ffprobe)
    return {"duration_seconds": duration, "width": width, "height": height,
            "fps": fps, "has_audio": bool(audio.get("streams")),
            "rotation_degrees": rotation, "display_width": display_width, "display_height": display_height}


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def _run_ffmpeg(command: list[str], cwd: Path, duration: float, cancel: threading.Event | None,
                progress: Callable[[float], None] | None) -> None:
    if cancel is not None and cancel.is_set():
        raise MediaError("Processamento cancelado.")
    updates: queue.Queue[float] = queue.Queue(maxsize=8)
    with tempfile.TemporaryFile(dir=cwd) as errors:
        try:
            process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=errors,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError as exc:
            raise MediaError("FFmpeg não encontrado. Instale ou configure o FFmpeg local.") from exc
        except OSError as exc:
            raise MediaError("Não foi possível iniciar o processamento local.") from exc

        def read_progress() -> None:
            assert process.stdout is not None
            for line in iter(lambda: process.stdout.readline(4096), b""):
                if line.startswith(b"out_time_us="):
                    try:
                        value = max(0.0, min(0.99, int(line.split(b"=", 1)[1]) / 1_000_000 / duration))
                        updates.put_nowait(value)
                    except (ValueError, queue.Full):
                        pass

        reader = threading.Thread(target=read_progress, daemon=True)
        reader.start()
        last_activity = time.monotonic()
        last_value = -1.0
        try:
            while process.poll() is None:
                if cancel is not None and cancel.is_set():
                    raise MediaError("Processamento cancelado.")
                try:
                    value = updates.get(timeout=0.1)
                    if value > last_value:
                        last_activity = time.monotonic()
                        last_value = value
                    if progress:
                        progress(value)
                except queue.Empty:
                    pass
                if time.monotonic() - last_activity > _STALL_TIMEOUT_SECONDS:
                    raise MediaError("FFmpeg ficou sem avançar o processamento por tempo excessivo (andamento parado).")
            if cancel is not None and cancel.is_set():
                raise MediaError("Processamento cancelado.")
            if process.returncode:
                errors.seek(0, os.SEEK_END)
                errors.seek(max(0, errors.tell() - 2000))
                detail = errors.read().decode("utf-8", errors="replace").strip()
                raise MediaError("FFmpeg não conseguiu gerar o arquivo." + (f" {detail}" if detail else ""))
        finally:
            _stop(process)
            reader.join(timeout=2)
            if process.stdout:
                process.stdout.close()


def _destination(destination: Path, source: Path) -> Path:
    raw = os.fspath(destination)
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw) or raw.startswith(("\\\\", "//")):
        raise MediaError("O destino precisa ser local.")
    try:
        destination = Path(raw).expanduser().resolve()
        if str(destination).startswith(("\\\\", "//")) or destination == source or destination.exists():
            raise MediaError("O destino já existe ou não pode ser usado. Nenhum arquivo foi sobrescrito.")
        if not destination.parent.is_dir():
            raise MediaError("A pasta de destino não existe.")
    except (OSError, ValueError, RuntimeError) as exc:
        if isinstance(exc, MediaError):
            raise
        raise MediaError("O destino não pode ser acessado. Confira o caminho e a permissão de escrita.") from exc
    return destination


def _publish(staged: Path, destination: Path, cancel: threading.Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise MediaError("Processamento cancelado.")
    if not staged.is_file() or staged.stat().st_size == 0:
        raise MediaError("FFmpeg não produziu um arquivo válido.")
    try:
        os.link(staged, destination)
    except FileExistsError as exc:
        raise MediaError("O destino já existe. Nenhum arquivo foi sobrescrito.") from exc
    except OSError:
        # Some removable filesystems do not support hard links; exclusive creation still prevents overwrite.
        created = False
        try:
            with destination.open("xb") as output:
                created = True
                with staged.open("rb") as source:
                    while chunk := source.read(1024 * 1024):
                        if cancel is not None and cancel.is_set():
                            raise MediaError("Processamento cancelado.")
                        output.write(chunk)
        except Exception:
            if created:
                destination.unlink(missing_ok=True)
            raise


def _base(ffmpeg: str) -> list[str]:
    return [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-xerror", "-n",
            "-progress", "pipe:1", "-nostats", "-protocol_whitelist", "file,pipe"]


def extract_audio(source: Path, destination: Path, *, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe",
                  cancel: threading.Event | None = None,
                  progress: Callable[[float], None] | None = None) -> Path:
    if cancel is not None and cancel.is_set():
        raise MediaError("Processamento cancelado.")
    source = _local_source(source)
    metadata = probe_video(source, ffprobe=ffprobe)
    if not metadata["has_audio"]:
        raise MediaError("O vídeo não contém áudio para transcrição.")
    destination = _destination(destination, source)
    with tempfile.TemporaryDirectory(prefix=".audio-", dir=destination.parent) as scratch:
        directory = Path(scratch)
        staged = directory / "audio.wav"
        command = _base(ffmpeg) + ["-i", str(source), "-map", "0:a:0", "-vn", "-ac", "1",
                                   "-ar", "16000", "-c:a", "pcm_s16le", "-f", "wav", str(staged)]
        _run_ffmpeg(command, directory, metadata["duration_seconds"], cancel, progress)
        _publish(staged, destination, cancel)
    if progress:
        progress(1.0)
    return destination


def _timestamp(seconds: float) -> str:
    ticks = max(0, int(round(seconds * 100)))
    hours, ticks = divmod(ticks, 360_000)
    minutes, ticks = divmod(ticks, 6000)
    whole, hundredths = divmod(ticks, 100)
    return f"{hours}:{minutes:02}:{whole:02}.{hundredths:02}"


def _ass(captions: list[dict], duration: float, width: int, height: int) -> str:
    font_size = max(18, round(height * 0.033))
    margin = round(width * 0.06)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,{margin},{margin},{round(height * 0.15)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if not isinstance(captions, list) or len(captions) > 10_000:
        raise MediaError("Lista de legendas inválida ou excessiva.")
    rows = []
    for caption in captions:
        try:
            start, end = float(caption["start_seconds"]), float(caption["end_seconds"])
            text = caption["text"]
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + 0.001):
                raise ValueError("caption bounds")
            if not isinstance(text, str) or len(text) > 2000:
                raise ValueError("caption text")
        except (TypeError, ValueError, KeyError) as exc:
            raise MediaError("A legenda tem texto ou tempos inválidos.") from exc
        text = text.replace("\\", "＼").replace("{", "｛").replace("}", "｝")
        text = "".join(character for character in text if character == "\n" or ord(character) >= 32)
        text = text.strip()
        if text:
            # Conservatively fit wide glyphs; timing between pages is proportional, not word alignment.
            characters = max(6, int((width - margin * 2) / font_size))
            lines = []
            for paragraph in text.split("\n"):
                lines.extend(textwrap.wrap(paragraph, width=characters, break_on_hyphens=False) or [""])
            pages = [r"\N".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
            pages = [page for page in pages if page.replace(r"\N", "").strip()]
            weights = [max(1, len(page.replace(r"\N", " "))) for page in pages]
            total = sum(weights)
            if len(pages) > 1 and total / (end - start) > 35:
                raise MediaError("A legenda longa é densa demais para o intervalo. Reduza o texto ou divida-o em legendas com mais tempo.")
            first_tick = math.floor(start * 100 + 1e-8)
            final_tick = max(first_tick + 1, math.ceil(end * 100 - 1e-8))
            elapsed = 0
            previous_tick = first_tick
            for index, (page, weight) in enumerate(zip(pages, weights)):
                elapsed += weight
                # Outward rounding keeps a short event from becoming a zero-centisecond ASS event.
                tick = round(first_tick + (final_tick - first_tick) * elapsed / total)
                tick = max(previous_tick + 1, min(tick, final_tick - len(pages) + index + 1))
                rows.append(f"Dialogue: 0,{_timestamp(previous_tick / 100)},{_timestamp(tick / 100)},Default,,0,0,0,,{page}\n")
                previous_tick = tick
    return header + "".join(rows)


def render_clip(source: Path, destination: Path, start_seconds: float, end_seconds: float,
                captions: list[dict], *, ffmpeg: str = "ffmpeg", cancel: threading.Event | None = None,
                progress: Callable[[float], None] | None = None, width: int = 1080, height: int = 1920,
                ffprobe: str = "ffprobe", output_format: str = "9:16", camera_box: dict | None = None) -> Path:
    if cancel is not None and cancel.is_set():
        raise MediaError("Processamento cancelado.")
    source = _local_source(source)
    metadata = probe_video(source, ffprobe=ffprobe)
    try:
        start, end = float(start_seconds), float(end_seconds)
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= metadata["duration_seconds"] + 0.001):
            raise ValueError("clip bounds")
        if type(width) is not int or type(height) is not int or min(width, height) < 160 or width % 2 or height % 2:
            raise ValueError("output dimensions")
        if output_format not in {"16:9", "9:16"}:
            raise ValueError("output format")
        width, height = (max(width, height), min(width, height)) if output_format == "16:9" else (min(width, height), max(width, height))
        if camera_box is not None:
            x, y, cw, ch = [float(camera_box[key]) for key in ("x", "y", "width", "height")]
            if (output_format != "9:16" or not all(math.isfinite(v) for v in (x, y, cw, ch)) or
                    min(x, y) < 0 or min(cw, ch) <= 0 or x + cw > 1.000001 or y + ch > 1.000001 or
                    cw * metadata["display_width"] < 2 or ch * metadata["display_height"] < 2):
                raise ValueError("camera bounds")
    except (KeyError, TypeError, ValueError) as exc:
        raise MediaError("Tempos de corte ou dimensões de saída inválidos.") from exc
    subtitle = _ass(captions, end - start, width, height)
    destination = _destination(destination, source)
    with tempfile.TemporaryDirectory(prefix=".render-", dir=destination.parent) as scratch:
        directory = Path(scratch)
        (directory / "captions.ass").write_text(subtitle, encoding="utf-8")
        staged = directory / "output.mp4"
        if output_format == "16:9":
            filters = (f"[0:v:0]scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2:reset_sar=1,"
                       f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                       "ass=filename=captions.ass,format=yuv420p[video]")
        elif camera_box is not None:
            top = max(2, round(width * 9 / 16) // 2 * 2)
            bottom = height - top
            filters = (
                "[0:v:0]split=3[cam][back][front];"
                f"[cam]crop=iw*{cw:.9f}:ih*{ch:.9f}:iw*{x:.9f}:ih*{y:.9f},"
                f"scale={width}:{top}:force_original_aspect_ratio=increase:reset_sar=1,crop={width}:{top}[camera];"
                f"[back]scale={width}:{bottom}:force_original_aspect_ratio=increase:reset_sar=1,crop={width}:{bottom},boxblur=20:2[bg];"
                f"[front]scale={width}:{bottom}:force_original_aspect_ratio=decrease:force_divisible_by=2:reset_sar=1[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[content];"
                "[camera][content]vstack=inputs=2,ass=filename=captions.ass,format=yuv420p[video]"
            )
        else:
            filters = (
                f"[0:v:0]split=2[back][front];"
                f"[back]scale={width}:{height}:force_original_aspect_ratio=increase:reset_sar=1,crop={width}:{height},boxblur=20:2[bg];"
                f"[front]scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2:reset_sar=1[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,ass=filename=captions.ass,format=yuv420p[video]"
            )
        command = _base(ffmpeg) + ["-ss", f"{start:.6f}", "-i", str(source), "-t", f"{end-start:.6f}",
            "-filter_complex_threads", "1", "-filter_complex", filters, "-map", "[video]", "-map", "0:a:0?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-threads", "2", "-c:a", "aac",
            "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", "-f", "mp4", str(staged)]
        _run_ffmpeg(command, directory, end-start, cancel, progress)
        _publish(staged, destination, cancel)
    if progress:
        progress(1.0)
    return destination
