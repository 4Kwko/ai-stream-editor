from contextlib import asynccontextmanager
import errno

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings
from .automation import Automation
from .schemas import AutomationPatch, ClipPatch, ExportRequest, ProjectCreate
from .service import Service, ServiceError


ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8765", "http://localhost:8765"}


def create_app(settings: Settings | None = None, *, transcriber=None, start_automation=False, automation_source=None) -> FastAPI:
    service = Service(settings or Settings.from_env(), transcriber=transcriber)
    try:
        automation = Automation(service, automation_source)
    except Exception:
        service.close()
        raise

    @asynccontextmanager
    async def lifespan(app):
        try:
            if start_automation:
                automation.start()
            yield
        finally:
            try:
                automation.close()
            finally:
                service.close()

    app = FastAPI(title="AI Stream Editor local", version="0.1.0", lifespan=lifespan)
    app.state.service = service
    app.state.automation = automation
    app.add_middleware(CORSMiddleware, allow_origins=sorted(ORIGINS), allow_credentials=False,
                       allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Content-Type", "Range"],
                       expose_headers=["Content-Range", "Accept-Ranges"])
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin is not None and origin not in ORIGINS:
            return JSONResponse({"detail": "Origem não autorizada. Abra a interface local."}, status_code=403)
        return await call_next(request)

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)

    @app.exception_handler(OSError)
    async def storage_error(request, exc):
        if exc.errno == errno.ENOSPC:
            return JSONResponse({"detail": "Espaço em disco insuficiente. Libere espaço e tente novamente."}, status_code=507)
        return JSONResponse({"detail": "Não foi possível acessar os arquivos locais. Verifique o caminho, a permissão e o espaço disponível."}, status_code=422)

    @app.get("/api/health")
    def health():
        return service.health()

    @app.get("/api/automation")
    def automation_status():
        return automation.view()

    @app.patch("/api/automation")
    def configure_automation(body: AutomationPatch):
        return automation.configure(body.model_dump(exclude_unset=True))

    @app.get("/api/gallery")
    def gallery(review_status: str = Query(default="all", pattern="^(all|pending|approved|rejected)$"),
                limit: int = Query(default=20, ge=1, le=50), cursor: int | None = Query(default=None, ge=1)):
        return service.gallery(review_status, limit, cursor)

    @app.post("/api/projects", status_code=201)
    def create_project(body: ProjectCreate):
        return service.create_project(body.source_path)

    @app.get("/api/projects")
    def projects():
        return [service.project_view(item) for item in service.store.project_summaries()]

    @app.get("/api/projects/{project_id}")
    def project(project_id: str):
        return service.project_view(service.require("project", project_id))

    @app.post("/api/projects/{project_id}/analyze", status_code=202)
    def analyze(project_id: str):
        return service.analyze(project_id)

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        return service.require("job", job_id)

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel(job_id: str):
        return service.cancel_job(job_id)

    @app.get("/api/projects/{project_id}/clips")
    def clips(project_id: str):
        service.require("project", project_id)
        return [service.clip_view(item) for item in reversed(service.store.related("clip", project_id))]

    @app.get("/api/projects/{project_id}/jobs")
    def project_jobs(project_id: str):
        service.require("project", project_id)
        return [service.require("job", job["id"]) for job in service.store.related("job", project_id)]

    @app.get("/api/projects/{project_id}/exports")
    def project_exports(project_id: str):
        service.require("project", project_id)
        return service.exports_for(project_id)

    @app.get("/api/clips/{clip_id}/exports")
    def clip_exports(clip_id: str):
        clip = service.require("clip", clip_id)
        return service.exports_for(clip["project_id"], clip_id)

    @app.patch("/api/clips/{clip_id}")
    def patch(clip_id: str, body: ClipPatch):
        return service.patch_clip(clip_id, body)

    @app.post("/api/clips/{clip_id}/render", status_code=202)
    def render(clip_id: str):
        return service.render(clip_id)

    @app.get("/api/clips/{clip_id}/preview")
    def preview(clip_id: str, revision: int | None = Query(default=None, ge=1)):
        return FileResponse(service.preview(clip_id, revision), media_type="video/mp4", headers={"Cache-Control": "no-store"})

    @app.get("/api/clips/{clip_id}/file")
    def clip_file(clip_id: str, revision: int | None = Query(default=None, ge=1)):
        return FileResponse(service.preview(clip_id, revision), media_type="video/mp4",
                            filename=f"corte_{clip_id[:8]}.mp4", headers={"Cache-Control": "no-store"})

    @app.post("/api/clips/{clip_id}/export", status_code=202)
    def export(clip_id: str, body: ExportRequest):
        return service.export(clip_id, body.output_directory)

    return app
