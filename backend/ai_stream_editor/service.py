from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import errno
import importlib.util
import logging
import math
import os
from pathlib import Path
import shutil
import sqlite3
import threading
from time import monotonic
from uuid import uuid4
from copy import deepcopy

from . import analysis, camera, media
from .config import Settings
from .instance import InstanceLock
from .schemas import ClipPatch
from .store import Store


TERMINAL = {"succeeded", "failed", "canceled"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ServiceError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


def local_path(value: str, *, directory: bool = False) -> Path:
    if "\x00" in value or value.startswith(("\\\\", "//")) or "://" in value:
        raise ServiceError(422, "Use um caminho absoluto local, não URL ou pasta de rede.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ServiceError(422, "Informe o caminho absoluto no computador.")
    try:
        if os.name == "nt":
            import ctypes
            if ctypes.windll.kernel32.GetDriveTypeW(str(path.anchor)) == 4:
                raise ServiceError(422, "Unidades de rede não são permitidas.")
            if path.is_reserved():
                raise ServiceError(422, "Use um arquivo comum em um caminho local.")
        path = path.resolve(strict=True)
        if str(path).startswith(("\\\\", "//")):
            raise ServiceError(422, "Pastas de rede não são permitidas.")
        if not (path.is_dir() if directory else path.is_file()):
            raise ServiceError(422, "A pasta não existe." if directory else "O arquivo não existe.")
    except (OSError, ValueError, RuntimeError) as exc:
        raise ServiceError(422, "O caminho não existe ou não pode ser acessado.") from exc
    return path


def validate_captions(captions: list[dict], duration: float):
    ids = set()
    previous_end = 0.0
    for caption in captions:
        start, end = caption["start_seconds"], caption["end_seconds"]
        if (caption["id"] in ids or not str(caption["text"]).strip()
                or not math.isfinite(start) or not math.isfinite(end)
                or start < previous_end - 0.001 or start < 0 or end <= start or end > duration + 0.001):
            raise ServiceError(422, "Legendas devem ter IDs únicos e intervalos ordenados, sem sobreposição, dentro do corte.")
        ids.add(caption["id"])
        previous_end = end


class Service:
    def __init__(self, settings: Settings, *, transcriber=None):
        self.settings = settings
        self.instance_lock = InstanceLock(settings.data_dir)
        self.lock = threading.RLock()
        self.terminal_jobs: dict[str, dict] = {}
        self.recent_exports: dict[str, dict] = {}
        try:
            self.store = Store(settings.data_dir)
            self.recover_exports()
            for job in self.store.all("job"):
                if job["status"] in {"running", "queued"} and job["id"] not in self.terminal_jobs:
                    job.update(status="failed", stage="Interrompido", error="O aplicativo foi interrompido. Inicie a operação novamente.", updated_at=now())
                    self.store.put("job", job)
        except Exception:
            self.instance_lock.close()
            raise
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ai-stream")
        self.cancellations: dict[str, threading.Event] = {}
        self.transcriber = transcriber or analysis.transcribe
        self.closing = False

    def close(self):
        try:
            with self.lock:
                self.closing = True
                for event in self.cancellations.values():
                    event.set()
                for job_id in list(self.cancellations):
                    try:
                        self.cancel_job(job_id)
                    except (OSError, sqlite3.Error):
                        logging.warning("Não foi possível salvar o cancelamento; o trabalho será identificado na próxima inicialização.")
        finally:
            try:
                self.executor.shutdown(wait=True, cancel_futures=False)
            finally:
                self.instance_lock.close()

    def require(self, kind: str, record_id: str) -> dict:
        if kind == "job" and record_id in self.terminal_jobs:
            return deepcopy(self.terminal_jobs[record_id])
        value = self.store.get(kind, record_id)
        if value is None:
            raise ServiceError(404, "Registro não encontrado.")
        return value

    def finish_job(self, job_id: str, **fields):
        with self.lock:
            job = self.require("job", job_id)
            job.update(fields, updated_at=now())
            try:
                self.store.put("job", job)
            except (OSError, sqlite3.Error):
                job["warning"] = "O estado final não pôde ser salvo. Confira o resultado antes de reiniciar."
                self.terminal_jobs[job_id] = job
                logging.warning("Falha ao persistir estado final de job local.")

    @staticmethod
    def file_identity(path: Path) -> dict:
        stat = path.stat()
        return {"device": stat.st_dev, "inode": stat.st_ino, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}

    def complete_export(self, pending: dict):
        export = {key: value for key, value in pending.items() if key not in {"file_identity", "job_snapshot"}}
        job = deepcopy(pending["job_snapshot"]) if "job_snapshot" in pending else self.require("job", pending["id"])
        finished_at = pending["created_at"]
        elapsed = None
        if job.get("started_at"):
            elapsed = max(0, (datetime.fromisoformat(finished_at) - datetime.fromisoformat(job["started_at"])).total_seconds())
        job.update(status="succeeded", stage="Concluído", error=None, progress=1.0,
                   result={"output_path": pending["output_path"]}, updated_at=now(),
                   finished_at=finished_at, elapsed_seconds=elapsed)
        try:
            self.store.put_many([("export", export), ("job", job)], remove_pending_export=pending["id"])
        except (OSError, sqlite3.Error):
            job["warning"] = "MP4 exportado. O histórico será recuperado ao reiniciar quando o banco estiver disponível."
            self.recent_exports[export["id"]] = export
            logging.warning("MP4 publicado; registro local pendente de recuperação.")
        finally:
            self.terminal_jobs[job["id"]] = job

    def recover_exports(self):
        for pending in self.store.all("export_pending"):
            job = self.store.get("job", pending["id"])
            if not job:
                continue
            if job["status"] == "succeeded" and self.store.get("export", pending["id"]):
                self.store.put_many([], remove_pending_export=pending["id"])
                continue
            path = Path(pending["output_path"])
            try:
                identity = self.file_identity(path)
            except OSError:
                identity = None
            # File identity survives rename/hardlink; an unrelated preexisting MP4 cannot become a success.
            if identity is not None and identity["inode"] and identity == pending["file_identity"]:
                self.complete_export(pending)
            else:
                job.update(status="failed", stage="Interrompido", progress=None, updated_at=now(),
                           error="Exportação interrompida sem resultado confirmado. Confira a pasta de destino e tente novamente.")
                self.store.put_many([("job", job)], remove_pending_export=pending["id"])

    def exports_for(self, project_id: str, clip_id: str | None = None):
        records = {item["id"]: item for item in self.store.related("export", project_id)}
        records.update({key: value for key, value in self.recent_exports.items() if value["project_id"] == project_id})
        return sorted((item for item in records.values() if clip_id is None or item["clip_id"] == clip_id),
                      key=lambda item: item["created_at"], reverse=True)

    def health(self):
        return {
            "status": "ok", "ffmpeg_available": shutil.which(self.settings.ffmpeg) is not None,
            "ffprobe_available": shutil.which(self.settings.ffprobe) is not None,
            "transcription_available": importlib.util.find_spec("faster_whisper") is not None,
            "model_ready": all((self.settings.model_dir / self.settings.model_name / name).is_file()
                               for name in ("model.bin", "config.json", "tokenizer.json")),
        }

    def project_view(self, project: dict):
        result = {key: project[key] for key in ("id", "source_path", "name", "duration_seconds", "width", "height", "fps", "has_audio", "created_at")}
        job = self.store.latest_job(project["id"], "analyze")
        if job:
            job = self.require("job", job["id"])
        source_status = self.source_status(project)
        result.update(analysis_job_id=job["id"] if job else None,
                      output_format=project.get("output_format", "9:16"),
                      analysis_status=job["status"] if job else "not_started",
                      analyzed_at=project.get("analyzed_at"),
                      clip_count=self.store.count_related("clip", project["id"]),
                      rotation_degrees=project.get("rotation_degrees", 0),
                      display_width=project.get("display_width", project["width"]),
                      display_height=project.get("display_height", project["height"]),
                      source_status=source_status, source_available=source_status == "available")
        return result

    @staticmethod
    def source_status(project: dict) -> str:
        try:
            source = local_path(project["source_path"])
            stat = source.stat()
        except FileNotFoundError:
            return "missing"
        except ServiceError as exc:
            return "missing" if isinstance(exc.__cause__, FileNotFoundError) else "unavailable"
        except OSError:
            return "unavailable"
        if stat.st_size != project.get("source_size", stat.st_size) or stat.st_mtime_ns != project.get("source_mtime_ns", stat.st_mtime_ns):
            return "changed"
        return "available"

    def clip_view(self, clip: dict):
        result = {key: clip[key] for key in ("id", "project_id", "start_seconds", "end_seconds", "title", "reason", "score", "review_status", "captions", "revision")}
        path = Path(clip["preview_file"]) if clip.get("preview_file") else None
        exists = path is not None and path.is_file() and path.resolve().is_relative_to(self.settings.data_dir.resolve() / "clips")
        ready = clip.get("preview_revision") == clip["revision"] and exists
        result["preview_status"] = "ready" if ready else ("stale" if exists else "missing")
        result["preview_url"] = f"http://127.0.0.1:8765/api/clips/{clip['id']}/preview?revision={clip['revision']}" if ready else None
        result.update(output_format=clip.get("output_format", "9:16"),
                      layout=clip.get("layout", "full_frame"), layout_warning=clip.get("layout_warning"))
        return result

    def create_project(self, source_path: str, *, project_id: str | None = None, source_info: dict | None = None,
                       output_format: str | None = None):
        if project_id:
            existing = self.store.get("project", project_id)
            if existing:
                return self.project_view(existing)
        config = self.store.get("automation", "source") or {}
        output_format = output_format or config.get("output_format", "16:9")
        if output_format not in {"16:9", "9:16"}:
            raise ServiceError(422, "Escolha 16:9 ou 9:16.")
        source = local_path(source_path)
        try:
            info = media.probe_video(source, ffprobe=self.settings.ffprobe)
        except media.MediaError as exc:
            raise ServiceError(422, str(exc)) from exc
        stat = source.stat()
        project = dict(info, id=project_id or str(uuid4()), source_path=str(source), name=source.name,
                       created_at=now(), source_size=stat.st_size, source_mtime_ns=stat.st_mtime_ns,
                       transcript=None, source=source_info, output_format=output_format)
        self.store.put("project", project)
        return self.project_view(project)

    def check_source(self, project: dict) -> Path:
        source = local_path(project["source_path"])
        stat = source.stat()
        if stat.st_size != project["source_size"] or stat.st_mtime_ns != project["source_mtime_ns"]:
            raise ServiceError(409, "O vídeo original mudou. Importe-o novamente antes de processar.")
        return source

    def gallery(self, review_status: str = "all", limit: int = 20, cursor: int | None = None):
        items = []
        scan_cursor = cursor
        while len(items) <= limit:
            rows = self.store.gallery_page(review_status, scan_cursor, limit + 1 - len(items))
            if not rows:
                break
            for rowid, clip, origin, created_at in rows:
                scan_cursor = rowid
                try:
                    self.preview(clip["id"], clip["revision"])
                except (ServiceError, OSError):
                    continue
                root = f"http://127.0.0.1:8765/api/clips/{clip['id']}"
                items.append((rowid, dict(
                    id=clip["id"], project_id=clip["project_id"], title=clip["title"],
                    reason=clip["reason"], score=clip["score"], review_status=clip["review_status"],
                    revision=clip["revision"], duration_seconds=clip["end_seconds"] - clip["start_seconds"],
                    output_format=clip.get("output_format", "9:16"), layout=clip.get("layout", "full_frame"),
                    layout_warning=clip.get("layout_warning"),
                    created_at=clip.get("created_at", created_at),
                    preview_url=f"{root}/preview?revision={clip['revision']}",
                    download_url=f"{root}/file?revision={clip['revision']}",
                    source=origin or dict(type="local", vod_id=None, channel_login=None, url=None, title=None))))
        return {"items": [item for _, item in items[:limit]],
                "next_cursor": items[limit - 1][0] if len(items) > limit else None}

    def update_job(self, job_id: str, **fields):
        with self.lock:
            job = self.require("job", job_id)
            job.update(fields, updated_at=now())
            self.store.put("job", job)

    def progress(self, job_id: str, stage: str, start: float = 0, span: float = 1):
        def update(value):
            fraction = start + span * max(0.0, min(1.0, float(value))) if value is not None and math.isfinite(value) else None
            self.update_job(job_id, stage=stage, progress=fraction)
        return update

    def submit(self, kind: str, project_id: str, clip_id: str | None, action):
        with self.lock:
            if self.closing:
                raise ServiceError(503, "O aplicativo está encerrando. Inicie-o novamente antes de enviar trabalho.")
            for job in self.store.related("job", project_id):
                if job["kind"] == kind and job["project_id"] == project_id and job["clip_id"] == clip_id and job["status"] in {"running", "queued"}:
                    raise ServiceError(409, "Já existe uma operação desse tipo para este item. Aguarde ou cancele antes de tentar novamente.")
            job_id = str(uuid4())
            job = dict(id=job_id, job_id=job_id, project_id=project_id, clip_id=clip_id, kind=kind,
                       status="queued", stage="Na fila", progress=None, error=None, result=None,
                       progress_scope="stage", started_at=None, finished_at=None, elapsed_seconds=None,
                       created_at=now(), updated_at=now())
            self.store.put("job", job)
            cancel = threading.Event()
            self.cancellations[job_id] = cancel
            self.executor.submit(self.run, job_id, cancel, action)
            return job

    def run(self, job_id, cancel, action):
        started = monotonic()
        try:
            with self.lock:
                if self.require("job", job_id)["status"] in TERMINAL:
                    return
                if cancel.is_set():
                    raise ServiceError(409, "Operação cancelada.")
                self.update_job(job_id, status="running", stage="Preparando", progress=None, started_at=now())
            result = action(job_id, cancel)
            # Actions check cancellation before publishing results; don't mislabel a completed export.
            if self.require("job", job_id)["status"] != "succeeded":
                self.finish_job(job_id, status="succeeded", stage="Concluído", progress=1.0, result=result,
                                finished_at=now(), elapsed_seconds=round(monotonic() - started, 6))
        except Exception as exc:
            if isinstance(exc, OSError) and exc.errno == errno.ENOSPC:
                message = "Espaço em disco insuficiente. Libere espaço e tente novamente."
            elif isinstance(exc, PermissionError):
                message = "Sem permissão para ler ou gravar o arquivo. Escolha uma pasta acessível e tente novamente."
            else:
                message = str(exc) if isinstance(exc, (ServiceError, media.MediaError, analysis.AnalysisError)) else "Falha inesperada no processamento local. Verifique ferramentas e espaço disponível."
            if self.require("job", job_id)["status"] != "succeeded":
                self.finish_job(job_id, status="canceled" if cancel.is_set() else "failed", stage="Cancelado" if cancel.is_set() else "Falhou", error=message, progress=None,
                                finished_at=now(), elapsed_seconds=round(monotonic() - started, 6))
        finally:
            with self.lock:
                self.cancellations.pop(job_id, None)

    def cancel_job(self, job_id: str):
        with self.lock:
            job = self.require("job", job_id)
            event = self.cancellations.get(job_id)
            if event and job["status"] not in TERMINAL:
                event.set()
                if job["status"] == "queued":
                    job.update(status="canceled", stage="Cancelado", progress=None, error="Operação cancelada antes de iniciar.", finished_at=now())
                else:
                    job["stage"] = "Cancelamento solicitado"
                job["updated_at"] = now()
                self.store.put("job", job)
            return job

    def analyze(self, project_id: str):
        with self.lock:
            project = self.require("project", project_id)
            if project["transcript"] is not None:
                raise ServiceError(409, "Este projeto já foi analisado. Seus cortes e correções foram preservados.")
            if not project["has_audio"]:
                raise ServiceError(422, "Este vídeo não possui áudio para transcrever.")

            def action(job_id, cancel):
                source = self.check_source(project)
                work = self.settings.data_dir / "projects" / project_id
                work.mkdir(parents=True, exist_ok=True)
                audio = work / f"{job_id}.wav"
                audio_created = False
                try:
                    extraction_started = monotonic()
                    self.update_job(job_id, stage="Extraindo áudio", progress=0)
                    media.extract_audio(source, audio, ffmpeg=self.settings.ffmpeg, ffprobe=self.settings.ffprobe, cancel=cancel,
                                        progress=self.progress(job_id, "Extraindo áudio"))
                    audio_created = True
                    extraction_seconds = monotonic() - extraction_started
                    transcription_started = monotonic()
                    self.update_job(job_id, stage="Transcrevendo em PT-BR", progress=None)
                    segments = self.transcriber(audio, self.settings.model_dir, model_name=self.settings.model_name,
                                                cancel=cancel, progress=self.progress(job_id, "Transcrevendo em PT-BR"))
                    transcription_seconds = monotonic() - transcription_started
                    suggestion_started = monotonic()
                    self.update_job(job_id, stage="Selecionando momentos", progress=None)
                    suggestions = analysis.suggest_clips(segments, project["duration_seconds"])
                    clips = []
                    records = []
                    with self.lock:
                        if cancel.is_set():
                            raise ServiceError(409, "Operação cancelada.")
                        for suggestion in suggestions:
                            if not 0 <= suggestion["start_seconds"] < suggestion["end_seconds"] <= project["duration_seconds"]:
                                raise ServiceError(422, "A sugestão contém limites fora do vídeo.")
                            validate_captions(suggestion["captions"], suggestion["end_seconds"] - suggestion["start_seconds"])
                            clip = dict(suggestion, id=str(uuid4()), project_id=project_id, revision=1,
                                        output_format=project.get("output_format", "9:16"),
                                        camera_mode="auto" if project.get("output_format") == "9:16" else "none",
                                        review_status="pending", preview_revision=None, preview_file=None)
                            records.append(("clip", clip))
                            clips.append(clip["id"])
                        project["transcript"] = segments
                        project["analyzed_at"] = now()
                        records.append(("project", project))
                        self.store.put_many(records)
                    empty_reason = None
                    if not clips:
                        empty_reason = ("A transcrição local não retornou segmentos de fala." if not segments else
                                        "Há transcrição, mas as regras textuais atuais não encontraram candidatos a corte.")
                    return {"clip_ids": clips, "analysis_method": "transcript_heuristic_v2",
                            "message": empty_reason or "Sugestões por regras sobre transcrição local; revise o contexto.",
                            "empty_reason": empty_reason,
                            "timings_seconds": {"extraction": round(extraction_seconds, 6),
                                                "transcription": round(transcription_seconds, 6),
                                                "suggestion_and_save": round(monotonic() - suggestion_started, 6)}}
                finally:
                    if audio_created:
                        audio.unlink(missing_ok=True)

            return self.submit("analyze", project_id, None, action)

    def patch_clip(self, clip_id: str, patch: ClipPatch):
        fields = patch.model_dump(exclude_unset=True)
        if any(value is None for value in fields.values()):
            raise ServiceError(422, "Campos enviados não podem ser null.")
        with self.lock:
            clip = self.require("clip", clip_id)
            project = self.require("project", clip["project_id"])
            expected = fields.pop("expected_revision", None)
            if expected is not None and expected != clip["revision"]:
                raise ServiceError(409, "O corte mudou. Recarregue antes de salvar.")
            start = fields.get("start_seconds", clip["start_seconds"])
            end = fields.get("end_seconds", clip["end_seconds"])
            if not 0 <= start < end <= project["duration_seconds"]:
                raise ServiceError(422, "O início e fim devem estar dentro do vídeo e formar um intervalo positivo.")
            changed_bounds = start != clip["start_seconds"] or end != clip["end_seconds"]
            corrections = clip.get("caption_corrections", {})
            self.remember_corrections(clip, project, corrections)
            if changed_bounds and "captions" not in fields:
                fields["captions"] = analysis.captions_for_window(project["transcript"] or [], start, end)
                for caption in fields["captions"]:
                    caption["text"] = corrections.get(caption["id"], {}).get(caption["text"], caption["text"])
            captions = fields.get("captions", clip["captions"])
            validate_captions(captions, end - start)
            content_changed = changed_bounds or captions != clip["captions"]
            if content_changed:
                clip["revision"] += 1
                clip["review_status"] = "pending"
            clip.update(fields)
            self.remember_corrections(clip, project, corrections)
            clip["caption_corrections"] = corrections
            self.store.put("clip", clip)
            return self.clip_view(clip)

    @staticmethod
    def remember_corrections(clip, project, corrections):
        baseline = {c["id"]: c["text"] for c in analysis.captions_for_window(
            project["transcript"] or [], clip["start_seconds"], clip["end_seconds"])}
        for caption in clip["captions"]:
            original = baseline.get(caption["id"])
            if original is not None:
                corrections.setdefault(caption["id"], {})[original] = caption["text"]

    def render(self, clip_id: str):
        with self.lock:
            snapshot = self.require("clip", clip_id)
            project = self.require("project", snapshot["project_id"])

            def action(job_id, cancel):
                source = self.check_source(project)
                folder = self.settings.data_dir / "clips" / clip_id
                folder.mkdir(parents=True, exist_ok=True)
                destination = folder / f"{job_id}.mp4"
                published = False
                rendered = False
                try:
                    output_format = snapshot.get("output_format", "9:16")
                    camera_box = None
                    layout = "source_preserved" if output_format == "16:9" else "full_frame"
                    layout_warning = None
                    if output_format == "9:16" and snapshot.get("camera_mode") == "auto":
                        self.update_job(job_id, stage="Localizando a câmera", progress=None)
                        camera_box, camera_status = camera.detect(source, snapshot["start_seconds"], snapshot["end_seconds"],
                                                                  ffmpeg=self.settings.ffmpeg, cancel=cancel)
                        if camera_box is not None:
                            layout = "camera_top_content_bottom"
                        else:
                            layout_warning = ("A câmera não foi localizada com segurança. O conteúdo inteiro foi preservado no vertical."
                                              if camera_status != "unavailable" else
                                              "A detecção local de câmera está indisponível. O conteúdo inteiro foi preservado no vertical.")
                    self.update_job(job_id, stage="Gerando preview", progress=None)
                    media.render_clip(source, destination, snapshot["start_seconds"], snapshot["end_seconds"], snapshot["captions"],
                                      ffmpeg=self.settings.ffmpeg, ffprobe=self.settings.ffprobe, cancel=cancel,
                                      progress=self.progress(job_id, "Gerando preview"), output_format=output_format, camera_box=camera_box)
                    rendered = True
                    with self.lock:
                        current = self.require("clip", clip_id)
                        if cancel.is_set() or current["revision"] != snapshot["revision"]:
                            raise ServiceError(409, "O corte mudou durante o render. Gere o preview novamente.")
                        current.update(preview_file=str(destination), preview_revision=snapshot["revision"],
                                       output_format=output_format, layout=layout, layout_warning=layout_warning)
                        self.store.put("clip", current)
                        published = True
                        return {"preview_url": self.clip_view(current)["preview_url"], "output_format": output_format,
                                "layout": layout, "layout_warning": layout_warning}
                finally:
                    if rendered and not published:
                        destination.unlink(missing_ok=True)

            return self.submit("render", snapshot["project_id"], clip_id, action)

    def preview(self, clip_id: str, revision: int | None = None) -> Path:
        clip = self.require("clip", clip_id)
        if revision is not None and revision != clip["revision"]:
            raise ServiceError(409, "Este endereço de preview pertence a uma revisão antiga. Recarregue o corte.")
        if clip.get("preview_revision") != clip["revision"] or not clip.get("preview_file"):
            raise ServiceError(409, "Gere um preview atualizado antes de continuar.")
        path = Path(clip["preview_file"])
        if not path.is_file() or not path.resolve().is_relative_to(self.settings.data_dir.resolve() / "clips"):
            raise ServiceError(409, "O preview não está disponível. Gere-o novamente.")
        return path

    def export(self, clip_id: str, output_directory: str):
        directory = local_path(output_directory, directory=True)
        with self.lock:
            snapshot = self.require("clip", clip_id)
            if snapshot["review_status"] != "approved":
                raise ServiceError(409, "Aprove o corte antes de exportar.")
            preview = self.preview(clip_id)

            def action(job_id, cancel):
                temporary = directory / f".ai-stream-{job_id}.partial"
                created = False
                try:
                    self.update_job(job_id, stage="Exportando", progress=None)
                    total = preview.stat().st_size
                    done = 0
                    with preview.open("rb") as source, temporary.open("xb") as target:
                        created = True
                        while block := source.read(1024 * 1024):
                            if cancel.is_set():
                                raise ServiceError(409, "Operação cancelada.")
                            target.write(block)
                            done += len(block)
                            self.progress(job_id, "Exportando")(done / total if total else None)
                        target.flush()
                        os.fsync(target.fileno())
                    with self.lock:
                        current = self.require("clip", clip_id)
                        if cancel.is_set() or current["revision"] != snapshot["revision"] or current["review_status"] != "approved":
                            raise ServiceError(409, "O corte mudou durante a exportação. Revise e exporte novamente.")
                        number = 1
                        while True:
                            suffix = "" if number == 1 else f"_{number}"
                            output = directory / f"corte_{clip_id[:8]}{suffix}.mp4"
                            pending = dict(id=job_id, job_id=job_id, project_id=snapshot["project_id"],
                                           clip_id=clip_id, revision=snapshot["revision"], created_at=now(),
                                           output_path=str(output), file_identity=self.file_identity(temporary),
                                           job_snapshot=self.require("job", job_id))
                            self.store.put("export_pending", pending)
                            try:
                                if os.name == "nt":
                                    os.rename(temporary, output)
                                else:
                                    os.link(temporary, output)
                                    temporary.unlink()
                                self.complete_export(pending)
                                return {"output_path": str(output)}
                            except FileExistsError:
                                number += 1
                finally:
                    if created:
                        temporary.unlink(missing_ok=True)

            return self.submit("export", snapshot["project_id"], clip_id, action)
