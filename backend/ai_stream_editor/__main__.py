import argparse
import json
import sys
from pathlib import Path

from .analysis import AnalysisError, prepare_model
from .config import Settings, local_directory


def main():
    parser = argparse.ArgumentParser(description="AI Stream Editor local")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="API apenas em 127.0.0.1:8765")
    serve.add_argument("--data-dir", type=Path)
    prepare = commands.add_parser("prepare-model", help="Baixar somente pesos públicos; nenhum áudio é enviado")
    prepare.add_argument("--model", choices=["tiny", "base", "small"])
    prepare.add_argument("--model-dir", type=Path)
    doctor = commands.add_parser("doctor", help="Diagnóstico somente leitura, sem instalar ou criar banco")
    doctor.add_argument("--data-dir", type=Path)
    doctor.add_argument("--no-api", action="store_true", help="Não consultar a API local")
    storage = commands.add_parser("storage", help="Relatório de espaço somente leitura, sem exclusão")
    storage.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    if args.command == "prepare-model":
        try:
            directory = local_directory(args.model_dir) if args.model_dir else settings.model_dir
            path = prepare_model(directory, args.model or settings.model_name)
        except (AnalysisError, ValueError) as exc:
            parser.exit(1, f"{exc}\n")
        print(f"Modelo pronto em {path}")
        return
    if args.data_dir:
        try:
            settings = Settings(data_dir=args.data_dir, model_name=settings.model_name,
                                ffmpeg=settings.ffmpeg, ffprobe=settings.ffprobe)
        except ValueError as exc:
            parser.exit(1, f"{exc}\n")
    if args.command in {"doctor", "storage"}:
        from .diagnostics import diagnose, storage_report
        report = diagnose(settings, check_api=not args.no_api) if args.command == "doctor" else storage_report(settings.data_dir)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.command == "doctor" and not report["ready"]:
            parser.exit(1)
        return
    import uvicorn
    from .api import create_app
    # Windows Proactor can strand a closing video socket after a client reset on Python 3.12.
    loop = "asyncio:SelectorEventLoop" if sys.platform == "win32" else "asyncio"
    uvicorn.run(create_app(settings, start_automation=True), host="127.0.0.1", port=8765, loop=loop,
                timeout_graceful_shutdown=10)


if __name__ == "__main__":
    main()
