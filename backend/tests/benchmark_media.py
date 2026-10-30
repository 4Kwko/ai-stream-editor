"""Run the synthetic media matrix and retain its measurements and one visual sample."""

from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import platform
import subprocess
import time
import unittest

import test_media
from ai_stream_editor.media import render_clip


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs/media-validation"))
    args = parser.parse_args()
    folder = args.output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_media)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"synthetic_only": True, "platform": platform.platform(), "python": platform.python_version(),
              "total_seconds": round(time.perf_counter() - started, 4), "tests": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
              "measurements": test_media.MEASUREMENTS, "memory_measured": False}
    if result.wasSuccessful() and not result.skipped:
        source = test_media.fixture_video(folder / "padrão não uniforme çã.mp4", duration=1)
        output = folder / "legibilidade-1080.mp4"
        render_clip(source, output, 0, 1, [{"start_seconds": 0, "end_seconds": 1, "text": "Ação, João! Minecraft."}])
        image = folder / "legibilidade-1080.png"
        subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-ss", "0.4", "-i", str(output),
                        "-frames:v", "1", str(image)], check=True, capture_output=True, timeout=30)
        report["visual_sample"] = str(image.resolve())
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str((folder / "report.json").resolve()), **report}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
