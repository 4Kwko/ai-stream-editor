"""Explicit real-model smoke using locally generated speech, never a user's VOD."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from ai_stream_editor.api import create_app
from ai_stream_editor.config import Settings
from ai_stream_editor.media import probe_video


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--speech", type=Path, required=True, help="WAV de fala sintética gerada localmente")
    parser.add_argument("--model-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.speech.resolve().parent / ("run-" + uuid4().hex[:8])
    root.mkdir()
    source = root / "video_sintetico.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=0x123144:s=640x360:r=15",
                    "-i", str(args.speech.resolve()), "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(source)], check=True, timeout=60)
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    os.environ["AI_STREAM_MODEL_DIR"] = str(args.model_dir.resolve())
    os.environ["HF_HUB_OFFLINE"] = "1"
    app = create_app(Settings(data_dir=root / "data", model_name="base"))

    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        def job(response):
            assert response.status_code == 202, response.text
            job_id = response.json()["id"]
            deadline = time.monotonic() + 240
            previous = None
            while time.monotonic() < deadline:
                item = client.get(f"/api/jobs/{job_id}").json()
                if item["stage"] != previous:
                    print(item["stage"], flush=True)
                    previous = item["stage"]
                if item["status"] in {"succeeded", "failed", "canceled"}:
                    assert item["status"] == "succeeded", item
                    return item
                time.sleep(.1)
            raise TimeoutError("O teste real excedeu quatro minutos por operação.")

        project_response = client.post("/api/projects", json={"source_path": str(source)})
        assert project_response.status_code == 201, project_response.text
        project_id = project_response.json()["id"]
        analyzed = job(client.post(f"/api/projects/{project_id}/analyze"))
        clips = client.get(f"/api/projects/{project_id}/clips").json()
        assert clips and clips[0]["captions"], "A fala sintética não gerou legendas."
        clip = clips[0]
        captions = clip["captions"]
        captions[0]["text"] += " [revisado]"
        revised = client.patch(f"/api/clips/{clip['id']}", json={"captions": captions})
        assert revised.status_code == 200, revised.text
        job(client.post(f"/api/clips/{clip['id']}/render"))
        ranged = client.get(f"/api/clips/{clip['id']}/preview", headers={"Range": "bytes=0-99"})
        assert ranged.status_code == 206
        assert client.patch(f"/api/clips/{clip['id']}", json={"review_status": "approved"}).status_code == 200
        result = job(client.post(f"/api/clips/{clip['id']}/export", json={"output_directory": str(root)}))
        output = Path(result["result"]["output_path"])
        info = probe_video(output)
        assert info["width"] == 1080 and info["height"] == 1920 and info["has_audio"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
        evidence = {"source": str(source), "output": str(output), "project_id": project_id,
                    "clip_id": clip["id"], "captions": len(captions), "clips": len(clips),
                    "transcription_text_synthetic": " ".join(x["text"] for x in captions),
                    "media": info, "analysis_method": analyzed["result"]["analysis_method"],
                    "source_preserved": True, "preview_range_status": ranged.status_code}
        (root / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(evidence, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
