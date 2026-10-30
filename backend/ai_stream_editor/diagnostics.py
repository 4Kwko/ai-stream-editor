"""Read-only checks of the product runtime; never prepares models or databases."""

from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from urllib.request import ProxyHandler, build_opener

from .config import Settings


def local_response(url: str) -> bytes:
    with build_opener(ProxyHandler({})).open(url, timeout=2) as response:
        return response.read(65536)


def command_output(executable: str, *args: str) -> str:
    try:
        result = subprocess.run([executable, *args], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def storage_report(data_dir: Path) -> dict:
    data_dir = data_dir.expanduser().absolute()
    parent = data_dir
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    try:
        free = shutil.disk_usage(parent).free
    except OSError:
        free = None
    writable = parent.is_dir() and os.access(parent, os.R_OK | os.W_OK)
    result = {"path": str(data_dir), "exists": data_dir.is_dir(),
              "parent_writable_advisory": os.access(parent, os.W_OK), "free_bytes": free,
              "usable_advisory": writable and (not data_dir.exists() or data_dir.is_dir()),
              "categories_bytes": {}, "unreadable_entries": 0,
              "note": "Somente leitura. Permissão é uma indicação, sem tentativa de gravação. Nenhum arquivo é apagado."}
    if not data_dir.is_dir():
        return result

    def unreadable(error):
        result["unreadable_entries"] += 1

    for root, dirs, files in os.walk(data_dir, onerror=unreadable, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink() and not (Path(root) / d).is_junction()]
        relative = Path(root).relative_to(data_dir)
        category = relative.parts[0] if relative.parts else "database_and_other"
        for name in files:
            path = Path(root) / name
            try:
                if not path.is_symlink():
                    sizes = result["categories_bytes"]
                    sizes[category] = sizes.get(category, 0) + path.stat().st_size
            except OSError:
                unreadable(None)
    return result


def diagnose(settings: Settings, *, check_api: bool = True) -> dict:
    packages = {}
    for package in ("fastapi", "uvicorn", "faster-whisper", "ctranslate2", "av"):
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            packages[package] = None
    filters = command_output(settings.ffmpeg, "-hide_banner", "-filters")
    encoders = command_output(settings.ffmpeg, "-hide_banner", "-encoders")
    scale_options = command_output(settings.ffmpeg, "-hide_banner", "-h", "filter=scale")
    required_filters = ("scale", "crop", "setsar", "boxblur", "overlay", "ass", "format")
    filter_names = {line.split()[1] for line in filters.splitlines() if len(line.split()) >= 3}
    model = settings.model_dir / settings.model_name
    assets = {name: (model / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json")}
    api = {"checked": check_api, "available": False}
    if check_api:
        try:
            payload = json.loads(local_response("http://127.0.0.1:8765/api/health"))
            api["available"] = payload.get("status") == "ok" and "model_ready" in payload
        except (OSError, ValueError):
            pass
    storage = storage_report(settings.data_dir)
    checks = {"python_supported": tuple(__import__("sys").version_info) >= (3, 12),
              "packages_installed": all(packages.values()),
              "ffmpeg_available": bool(command_output(settings.ffmpeg, "-version")),
              "ffprobe_available": bool(command_output(settings.ffprobe, "-version")),
              "libx264_available": "libx264" in encoders,
              "required_filters_available": all(name in filter_names for name in required_filters),
              "scale_reset_sar_available": "reset_sar" in scale_options,
              "model_assets_present": all(assets.values()),
              "data_directory_accessible_advisory": storage["usable_advisory"]}
    return {"ready": all(checks.values()), "python": platform.python_version(), "checks": checks,
            "packages": packages, "model_path": str(model), "model_assets": assets,
            "required_filters": {name: name in filter_names for name in required_filters},
            "storage": storage, "api": api}
