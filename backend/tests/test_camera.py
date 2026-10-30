"""Stable-region logic uses controlled boxes; native negative uses synthetic video."""

import threading

import pytest

from ai_stream_editor import camera, media
from test_api import video


def test_stable_region_covers_face_and_stays_inside_source():
    samples = [[(25 + i % 2, 35, 30, 35)] for i in range(6)]
    box, status = camera.stable_region(samples, 320, 180)
    assert status == "detected"
    assert 0 <= box["x"] <= 1 - box["width"]
    assert 0 <= box["y"] <= 1 - box["height"]
    assert box["x"] * 320 <= 25 and (box["x"] + box["width"]) * 320 >= 56
    assert box["y"] * 180 <= 35 and (box["y"] + box["height"]) * 180 >= 70


def test_two_stable_faces_are_ambiguous():
    samples = [[(10, 20, 30, 30), (260, 120, 30, 30)] for _ in range(6)]
    assert camera.stable_region(samples, 320, 180) == (None, "ambiguous")


def test_camera_near_edge_keeps_face_centered_when_context_fits():
    box, status = camera.stable_region([[(45, 60, 30, 30)]] * 6, 320, 180)
    assert status == "detected"
    center = box["x"] + box["width"] / 2
    assert center == pytest.approx(60 / 320)
    assert box["y"] * 180 <= 60
    assert (box["y"] + box["height"]) * 180 >= 90


def test_sparse_detections_and_duplicate_boxes_do_not_fake_stability():
    assert camera.stable_region([[(10, 10, 30, 30)]] * 3 + [[]] * 3, 320, 180) == (None, "not_detected")
    assert camera.stable_region([[(10, 10, 30, 30)] * 6] + [[]] * 5, 320, 180) == (None, "not_detected")


def test_native_detector_no_face_in_synthetic_video(video):
    box, status = camera.detect(video, 0, 1.8)
    assert box is None and status == "not_detected"


def test_cancelled_detection_publishes_nothing(video):
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(media.MediaError, match="cancelado"):
        camera.detect(video, 0, 1, cancel=cancel)
