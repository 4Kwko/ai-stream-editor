"""One persistent VOD supervisor; heavy jobs still use Service's single worker."""

from datetime import datetime, timezone
import logging
from pathlib import Path
import threading
import time
from uuid import NAMESPACE_URL, uuid5

from .service import ServiceError, TERMINAL, now
from .twitch import SourceError, TwitchSource, channel_login, vod_id


def iso_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp else None


class Automation:
    poll_interval = 300
    max_attempts = 3

    def __init__(self, service, source=None):
        self.service = service
        self.source = source or TwitchSource(service.settings)
        self.stop = threading.Event()
        self.thread = None
        self.cycle_lock = threading.Lock()
        self.active = None
        self.status = "stopped"
        self.message = "A busca automática funciona enquanto os serviços estão em execução."
        if self.service.store.get("automation", "source") is None:
            self.service.store.put("automation", dict(id="source", enabled=True, channel_login="joaomontagner",
                                                      last_checked_at=None, next_poll_at=0, discovery_failures=0,
                                                      output_format="16:9"))
        elif "output_format" not in self.config():
            config = self.config()
            config["output_format"] = "16:9"
            self.service.store.put("automation", config)

    def config(self):
        return self.service.store.get("automation", "source")

    def records(self, login):
        return [r for r in self.service.store.all("vod") if r["channel_login"] == login]

    def view(self):
        with self.service.lock:
            config = self.config()
            active = dict(self.active) if self.active else None
            runtime = self.thread is not None and self.thread.is_alive()
            state = self.status if runtime else "stopped"
            if not config["enabled"] and active is None:
                state = "disabled"
            if active and active.get("job_id"):
                job = self.service.require("job", active["job_id"])
                active.update(progress=job.get("progress"), progress_scope="stage", stage=job["stage"])
            counts = dict(queued=0, processing=0, completed=0, failed=0, skipped=0)
            for record in self.records(config["channel_login"]):
                category = record["state"] if record["state"] in counts else "processing"
                counts[category] += 1
            return dict(enabled=config["enabled"], channel_login=config["channel_login"],
                        output_format=config["output_format"],
                        channel_url=f"https://www.twitch.tv/{config['channel_login']}",
                        poll_interval_seconds=self.poll_interval, runtime_active=runtime,
                        status=state, message=self.message,
                        gallery_updated_at=self.service.store.gallery_updated_at(),
                        last_checked_at=config.get("last_checked_at"),
                        next_check_at=iso_timestamp(config.get("next_poll_at")) if config["enabled"] else None,
                        active_vod=active, counts=counts)

    def configure(self, fields):
        if any(value is None for value in fields.values()):
            raise ServiceError(422, "Campos enviados não podem ser null.")
        if "output_format" in fields and fields["output_format"] not in {"16:9", "9:16"}:
            raise ServiceError(422, "Escolha 16:9 ou 9:16.")
        with self.service.lock:
            config = self.config()
            if "channel_login" in fields:
                try:
                    fields["channel_login"] = channel_login(fields["channel_login"])
                except ValueError as exc:
                    raise ServiceError(422, str(exc)) from exc
                if self.active and fields["channel_login"] != config["channel_login"]:
                    raise ServiceError(409, "Aguarde o VOD em processamento antes de trocar o canal.")
            changed = any(config.get(key) != value for key, value in fields.items())
            config.update(fields)
            if changed:
                config.update(next_poll_at=0, discovery_failures=0)
            self.service.store.put("automation", config)
        return self.view()

    def start(self):
        with self.service.lock:
            if self.thread and self.thread.is_alive():
                return
            self.stop.clear()
            self.status, self.message = "waiting", "Aguardando a próxima consulta de gravações disponíveis."
            self.thread = threading.Thread(target=self.run, name="vod-supervisor", daemon=True)
            self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join()

    def run(self):
        while not self.stop.is_set():
            try:
                self.cycle()
            except Exception:
                self.status = "attention"
                self.message = "A automação não pôde salvar ou recuperar seu estado. Confira disco e permissões."
                logging.warning("Automação local aguardando após falha de estado.")
                if self.stop.wait(self.poll_interval):
                    break
            self.stop.wait(1)

    def discover(self, config):
        self.status, self.message = "checking", "Consultando gravações disponíveis no canal."
        login = config["channel_login"]
        entries = self.source.discover(login, self.stop)
        with self.service.lock:
            current = self.config()
            if self.stop.is_set() or not current["enabled"] or current["channel_login"] != login:
                return
            first = self.service.store.get("watch", login) is None
            changes = []
            seen = set()
            for index, entry in enumerate(entries):
                key = vod_id(entry["id"])
                if key in seen:
                    continue
                seen.add(key)
                record_id = f"twitch:{login}:{key}"
                record = self.service.store.get("vod", record_id)
                if record is None:
                    record = dict(id=record_id, vod_id=key, channel_login=login,
                                  title=entry["title"], url=f"https://www.twitch.tv/videos/{key}",
                                  project_id=str(uuid5(NAMESPACE_URL, record_id)), state="skipped" if first and index > 0 else "queued",
                                  attempts=0, next_attempt_at=0, ready=False,
                                  observed_duration=entry["duration_seconds"],
                                  error=None, source_path=None, created_at=now())
                elif record["state"] == "queued" and not record["ready"]:
                    record["ready"] = record.get("observed_duration") == entry["duration_seconds"]
                    record["observed_duration"] = entry["duration_seconds"]
                changes.append(("vod", record))
            current.update(last_checked_at=now(), next_poll_at=time.time() + self.poll_interval, discovery_failures=0)
            changes.extend([("watch", dict(id=login)), ("automation", current)])
            self.service.store.put_many(changes)
        self.status = "waiting"
        self.message = "Aguardando uma gravação finalizada disponível neste canal."

    def cycle(self):
        if not self.cycle_lock.acquire(blocking=False):
            return
        try:
            config = self.config()
            if not config["enabled"] or self.stop.is_set():
                return
            if time.time() >= config.get("next_poll_at", 0):
                try:
                    self.discover(config)
                except SourceError as exc:
                    self.status = "configuration_required" if exc.configuration else "attention"
                    self.message = str(exc)
                    with self.service.lock:
                        current = self.config()
                        if current["channel_login"] == config["channel_login"]:
                            failures = current.get("discovery_failures", 0) + 1
                            current.update(last_checked_at=now(), discovery_failures=failures,
                                           next_poll_at=time.time() + min(3600, self.poll_interval * 2 ** min(failures - 1, 4)))
                            self.service.store.put("automation", current)
            config = self.config()
            if not config["enabled"] or self.stop.is_set():
                return
            for record in self.records(config["channel_login"]):
                if record["state"] in {"completed", "failed", "skipped"} or not record["ready"]:
                    continue
                if time.time() < record.get("next_attempt_at", 0):
                    continue
                with self.service.lock:
                    current = self.config()
                    if current["channel_login"] != config["channel_login"] or not current["enabled"]:
                        return
                    self.active = dict(id=record["vod_id"], title=record["title"], url=record["url"],
                                       stage="Preparando", project_id=record["project_id"], job_id=None,
                                       progress=None, progress_scope="stage")
                try:
                    self.process(record)
                finally:
                    with self.service.lock:
                        self.active = None
                break
        finally:
            self.cycle_lock.release()

    def save(self, record, **fields):
        record.update(fields, updated_at=now())
        self.service.store.put("vod", record)

    def stage(self, record, state, message):
        with self.service.lock:
            self.status, self.message = state, message
            self.active.update(stage=message, job_id=None, progress=None)
            self.save(record, state=state)

    def wait_job(self, job):
        with self.service.lock:
            self.active["job_id"] = job["id"]
        while not self.stop.is_set():
            result = self.service.require("job", job["id"])
            if result["status"] in TERMINAL:
                return result
            self.stop.wait(.1)
        raise InterruptedError("supervisor stopping")

    def process(self, record):
        try:
            if record["attempts"] >= self.max_attempts:
                self.save(record, state="failed", error="Limite de tentativas atingido.")
                return
            self.save(record, attempts=record["attempts"] + 1, error=None,
                      output_format=record.get("output_format", self.config()["output_format"]))
            project = self.service.store.get("project", record["project_id"])
            if project is None:
                if not record.get("source_path") or not Path(record["source_path"]).is_file():
                    self.stage(record, "downloading", "Obtendo a gravação pública do canal.")
                    source = self.source.download(record["channel_login"], record, self.stop)
                    self.save(record, source_path=str(source))
                origin = dict(type="twitch", vod_id=record["vod_id"], channel_login=record["channel_login"],
                              url=record["url"], title=record["title"])
                self.service.create_project(record["source_path"], project_id=record["project_id"], source_info=origin,
                                            output_format=record["output_format"])
                project = self.service.require("project", record["project_id"])
            if self.stop.is_set():
                raise InterruptedError("supervisor stopping")
            if project["transcript"] is None:
                self.stage(record, "analyzing", "Transcrevendo e selecionando momentos em PT-BR.")
                existing = self.service.store.latest_job(project["id"], "analyze")
                job = existing if existing and existing["status"] not in TERMINAL else self.service.analyze(project["id"])
                result = self.wait_job(job)
                if result["status"] != "succeeded":
                    raise SourceError(result.get("error") or "A análise não foi concluída.")
            failures = []
            for clip in self.service.store.related("clip", project["id"]):
                if self.stop.is_set():
                    raise InterruptedError("supervisor stopping")
                if self.service.clip_view(clip)["preview_status"] == "ready":
                    continue
                self.stage(record, "rendering", f"Gerando cortes {project.get('output_format', '9:16')} com legenda.")
                jobs = self.service.store.related("job", project["id"])
                active = next((j for j in jobs if j["kind"] == "render" and j["clip_id"] == clip["id"] and j["status"] not in TERMINAL), None)
                result = self.wait_job(active or self.service.render(clip["id"]))
                if result["status"] != "succeeded":
                    failures.append(result.get("error") or "Um corte não pôde ser gerado.")
            if failures:
                raise SourceError(f"{len(failures)} corte(s) não puderam ser gerados. Os demais permanecem na galeria.")
            self.save(record, state="completed", error=None)
            self.status, self.message = "waiting", "Cortes disponíveis. Aguardando novas gravações."
        except InterruptedError:
            return
        except Exception as exc:
            if self.stop.is_set():
                return
            deferred = isinstance(exc, SourceError) and exc.deferred
            retryable = exc.retryable if isinstance(exc, SourceError) else not isinstance(exc, PermissionError)
            message = str(exc) if isinstance(exc, (SourceError, ServiceError)) else "Falha local ao obter ou processar o VOD. Confira espaço e permissões."
            if deferred:
                self.save(record, state="queued", ready=False, attempts=max(0, record["attempts"] - 1),
                          observed_duration=None, error=None)
                self.status, self.message = "waiting", message
            else:
                retry = retryable and record["attempts"] < self.max_attempts
                self.save(record, state="queued" if retry else "failed", error=message,
                          next_attempt_at=time.time() + self.poll_interval * 2 ** (record["attempts"] - 1))
                self.status = "configuration_required" if isinstance(exc, SourceError) and exc.configuration else "attention"
                self.message = message
