"""Locate a stable face region locally; never identify a person or upload frames."""

import math
from pathlib import Path
from statistics import median
import subprocess
import time

from . import media


def stable_region(samples, width, height):
    groups = []
    for frame_index, faces in enumerate(samples):
        for x, y, w, h in faces:
            if min(w, h) <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
                continue
            rect = (float(x), float(y), float(w), float(h))
            cx, cy = (x + w / 2) / width, (y + h / 2) / height
            for group in groups:
                gx = median((r[0] + r[2] / 2) / width for r in group["rects"])
                gy = median((r[1] + r[3] / 2) / height for r in group["rects"])
                if abs(gx - cx) <= max(.035, w / width) and abs(gy - cy) <= max(.05, h / height):
                    if frame_index not in group["frames"]:
                        group["rects"].append(rect)
                        group["frames"].add(frame_index)
                    break
            else:
                groups.append(dict(rects=[rect], frames={frame_index}))
    threshold = max(4, math.ceil(len(samples) * 2 / 3))
    candidates = sorted((g for g in groups if len(g["frames"]) >= threshold),
                        key=lambda g: len(g["frames"]), reverse=True)
    if not candidates:
        return None, "not_detected"
    if len(candidates) > 1 and len(candidates[0]["frames"]) - len(candidates[1]["frames"]) <= 1:
        return None, "ambiguous"
    rects = candidates[0]["rects"]
    left, top = min(r[0] for r in rects), min(r[1] for r in rects)
    right, bottom = max(r[0] + r[2] for r in rects), max(r[1] + r[3] for r in rects)
    fw, fh = right - left, bottom - top
    crop_w = min(width, max(fw * 2.5, fh * 2.8 * 16 / 9))
    center_x = (left + right) / 2
    edge_width = 2 * min(center_x, width - center_x)
    if edge_width * 9 / 16 >= fh * 1.5:
        crop_w = min(crop_w, edge_width)
    crop_h = min(height, crop_w * 9 / 16)
    crop_x = min(max(0, (left + right - crop_w) / 2), width - crop_w)
    crop_y = min(max(0, (top + bottom - crop_h) / 2 + fh * .25), height - crop_h)
    return dict(x=crop_x / width, y=crop_y / height, width=crop_w / width, height=crop_h / height), "detected"


def read_frame(source, seconds, ffmpeg, cancel):
    command = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-protocol_whitelist", "file,pipe",
               "-ss", f"{seconds:.6f}", "-i", str(source), "-frames:v", "1",
               "-vf", "scale=960:540:force_original_aspect_ratio=decrease:force_divisible_by=2:reset_sar=1",
               "-threads", "1", "-pix_fmt", "gray", "-vcodec", "png", "-f", "image2pipe", "pipe:1"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    deadline = time.monotonic() + 10
    try:
        while True:
            if cancel is not None and cancel.is_set():
                raise media.MediaError("Processamento cancelado.")
            try:
                output, _ = process.communicate(timeout=.1)
                if process.returncode or len(output) > 4 * 1024**2:
                    return None
                return output
            except subprocess.TimeoutExpired:
                if time.monotonic() >= deadline:
                    return None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)


def detect(source: Path, start_seconds: float, end_seconds: float, *, ffmpeg="ffmpeg", cancel=None):
    source = media._local_source(source)
    try:
        import cv2
        import numpy as np
        classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        if classifier.empty():
            return None, "unavailable"
    except (ImportError, OSError):
        return None, "unavailable"
    cv2.setNumThreads(1)
    samples = []
    began = time.monotonic()
    width = height = 0
    for index in range(6):
        if cancel is not None and cancel.is_set():
            raise media.MediaError("Processamento cancelado.")
        if time.monotonic() - began > 20:
            return None, "timeout"
        encoded = read_frame(source, start_seconds + (end_seconds - start_seconds) * (index + .5) / 6,
                             ffmpeg, cancel)
        if not encoded:
            samples.append([])
            continue
        frame = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if frame is None:
            samples.append([])
            continue
        frame_height, frame_width = frame.shape
        if width and (width != frame_width or height != frame_height):
            return None, "ambiguous"
        height, width = frame_height, frame_width
        faces = classifier.detectMultiScale(cv2.equalizeHist(frame), scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))
        samples.append([tuple(map(int, face)) for face in faces])
    return stable_region(samples, width, height) if width and height else (None, "not_detected")
