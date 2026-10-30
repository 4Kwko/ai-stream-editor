from pathlib import Path
from array import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import wave

from ai_stream_editor import media
from ai_stream_editor.media import MediaError, _ass, extract_audio, probe_video, render_clip


MEASUREMENTS = []


def fixture_video(path, *, size="320x180", channels=1, duration=1.2, sync=False):
    video = (f"color=black:size={size}:rate=20:duration={duration},"
             "drawbox=color=white:t=fill:enable='between(t,1,1.15)'" if sync else
             f"testsrc2=size={size}:rate=20:duration={duration}")
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-f", "lavfi", "-i", video]
    if channels:
        audio = (f"aevalsrc=exprs='if(between(t,1,1.15),0.5*sin(2*PI*1000*t),0)':s=48000:d={duration}"
                 if sync else f"sine=frequency=440:sample_rate=48000:duration={duration}")
        command += ["-f", "lavfi", "-i", audio]
    command += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-threads", "1", "-pix_fmt", "yuv420p"]
    command += ["-c:a", "aac", "-ac", str(channels), "-shortest"] if channels else ["-an"]
    subprocess.run(command + [str(path)], check=True, capture_output=True, timeout=30)
    return path


def gray_frame(path, seconds, width=180, height=320):
    return subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, seconds):.6f}",
                           "-i", str(path), "-frames:v", "1", "-vf", f"scale={width}:{height}",
                           "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"],
                          check=True, capture_output=True, timeout=30).stdout


def audio_channels(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
                             "-of", "json", str(path)], check=True, capture_output=True, timeout=30)
    streams = json.loads(result.stdout).get("streams", [])
    return streams[0]["channels"] if streams else 0


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe are required")
class MediaTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="media-test-", dir=Path(__file__).parent)
        self.addCleanup(self.scratch.cleanup)
        self.directory = Path(self.scratch.name)
        self.source = self.directory / "origem com espaços.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15:duration=2",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
                        "-c:v", "libx264", "-threads", "1", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-shortest", str(self.source)], check=True, capture_output=True, timeout=30)

    def test_extract_and_render_real_media_preserve_original(self):
        original_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        info = probe_video(self.source)
        self.assertEqual((info["width"], info["height"]), (320, 180))
        self.assertTrue(info["has_audio"])
        audio = extract_audio(self.source, self.directory / "áudio.wav")
        with wave.open(str(audio)) as wav:
            self.assertEqual((wav.getframerate(), wav.getnchannels(), wav.getsampwidth()), (16000, 1, 2))
        updates = []
        output = render_clip(self.source, self.directory / "corte.mp4", 0.25, 1.25,
                             [{"id": "c1", "start_seconds": 0, "end_seconds": 1, "text": "Olá, Brasil!"}],
                             width=180, height=320, progress=updates.append)
        info = probe_video(output)
        self.assertEqual((info["width"], info["height"]), (180, 320))
        self.assertAlmostEqual(info["duration_seconds"], 1, delta=0.15)
        self.assertTrue(info["has_audio"])
        self.assertEqual(updates[-1], 1)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), original_hash)
        self.assertFalse(list(self.directory.glob(".render-*")))

    def test_existing_destination_and_invalid_times_are_not_changed(self):
        destination = self.directory / "existing.mp4"
        destination.write_bytes(b"preserve")
        with self.assertRaises(MediaError):
            render_clip(self.source, destination, 0, 1, [], width=180, height=320)
        self.assertEqual(destination.read_bytes(), b"preserve")
        for start, end in [(-1, 1), (1, 0), (0, 20), (math.nan, 1)]:
            with self.assertRaises(MediaError):
                render_clip(self.source, self.directory / "invalid.mp4", start, end, [])
        self.assertFalse((self.directory / "invalid.mp4").exists())

    def test_cancellation_publishes_nothing(self):
        cancel = threading.Event()
        cancel.set()
        destination = self.directory / "cancel.mp4"
        with self.assertRaisesRegex(MediaError, "cancelado"):
            render_clip(self.source, destination, 0, 1, [], cancel=cancel, width=180, height=320)
        self.assertFalse(destination.exists())
        self.assertFalse(list(self.directory.glob(".render-*")))

    def test_cancel_during_render_cleans_staging(self):
        cancel = threading.Event()
        destination = self.directory / "interrupted.mp4"
        started = time.perf_counter()
        with self.assertRaisesRegex(MediaError, "cancelado"):
            render_clip(self.source, destination, 0, 2, [], cancel=cancel,
                        progress=lambda _: cancel.set())
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 5)
        self.assertFalse(destination.exists())
        self.assertFalse(list(self.directory.glob(".render-*")))
        MEASUREMENTS.append({"case": "cancel_during_render", "seconds_until_cleanup": round(elapsed, 4),
                             "published": False, "staging_remaining": False})

    def test_invalid_and_network_sources_are_rejected(self):
        invalid = self.directory / "not-a-video.mp4"
        invalid.write_text("not media", encoding="utf-8")
        removed = self.directory / "removido.mp4"
        shutil.copyfile(self.source, removed)
        removed.unlink()
        for source in [invalid, removed, self.directory, Path("https://example.com/video.mp4"), Path("//server/video.mp4")]:
            with self.assertRaises(MediaError):
                probe_video(source)


class SubtitleTests(unittest.TestCase):
    def test_ass_override_and_newline_handling(self):
        result = _ass([{"start_seconds": 0, "end_seconds": 1,
                        "text": "Olá {\\pos(0,0)}\nsegunda linha"}], 1, 1080, 1920)
        self.assertNotIn(r"{\pos", result)
        self.assertIn(r"\Nsegunda linha", result)
        self.assertIn("Olá", result)

    def test_out_of_bounds_caption_rejected(self):
        with self.assertRaises(MediaError):
            _ass([{"start_seconds": 0, "end_seconds": 2, "text": "bad"}], 1, 1080, 1920)

    def test_short_caption_keeps_positive_ass_interval(self):
        result = _ass([{"start_seconds": 0.011, "end_seconds": 0.014, "text": "curta"}], 1, 1080, 1920)
        self.assertIn("0:00:00.01,0:00:00.02", result)

    def test_long_caption_pages_do_not_overlap_or_drop_words(self):
        original = "Ação, emoção e João descobriram algo incrível no Minecraft com timing e contexto suficientes."
        result = _ass([{"start_seconds": 0.113, "end_seconds": 7.917, "text": original}], 8, 1080, 1920)
        rows = [row.split(",", 9) for row in result.splitlines() if row.startswith("Dialogue:")]
        self.assertGreater(len(rows), 1)
        text = " ".join(row[9].replace(r"\N", " ") for row in rows)
        self.assertEqual(text, original)
        self.assertTrue(all(row[9].count(r"\N") <= 1 for row in rows))
        for earlier, later in zip(rows, rows[1:]):
            self.assertEqual(earlier[2], later[1])

    def test_excessive_caption_density_is_explained(self):
        with self.assertRaisesRegex(MediaError, "densa demais"):
            _ass([{"start_seconds": 0, "end_seconds": 1, "text": "legenda longa " * 50}], 1, 1080, 1920)

    def test_ass_special_characters_are_text_and_crlf_is_preserved(self):
        text = 'João: "AÇÃO", C++, São Paulo e Minecraft.\r\n{\\pos(0,0)} & <teste> | fim'
        result = _ass([{"start_seconds": 0, "end_seconds": 8, "text": text}], 8, 1080, 1920)
        self.assertNotIn(r"{\pos", result)
        self.assertNotIn("\r", result)
        self.assertIn("São Paulo", result)
        self.assertIn("｛＼pos(0,0)｝", result)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe are required")
class MediaMatrixTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="media-matrix-", dir=Path(__file__).parent)
        self.addCleanup(self.scratch.cleanup)
        self.directory = Path(self.scratch.name)

    def test_input_matrix_and_rotation(self):
        cases = [("horizontal-mono", "320x180", 1, 0), ("vertical-estéreo", "180x320", 2, 0),
                 ("quadrado-mono", "200x200", 1, 0), ("sem-áudio", "320x180", 0, 0),
                 ("pequeno-estéreo", "160x90", 2, 0), ("rotação-90", "320x180", 1, 90),
                 ("rotação-270", "320x180", 2, 270)]
        for name, size, channels, rotation in cases:
            with self.subTest(case=name):
                source = fixture_video(self.directory / f"origem {name} ação çã.mp4", size=size, channels=channels)
                if rotation:
                    rotated = self.directory / f"matriz {name}.mp4"
                    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                                    "-display_rotation:v:0", str(rotation), "-i", str(source), "-c", "copy", str(rotated)],
                                   check=True, capture_output=True, timeout=30)
                    source = rotated
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                source_info = probe_video(source)
                w, h = map(int, size.split("x"))
                self.assertEqual((source_info["width"], source_info["height"]), (w, h))
                self.assertEqual(source_info["has_audio"], bool(channels))
                expected_display = (h, w) if rotation else (w, h)
                self.assertEqual((source_info["display_width"], source_info["display_height"]), expected_display)
                if channels:
                    audio = extract_audio(source, self.directory / f"extração {name}.wav")
                    with wave.open(str(audio)) as decoded:
                        self.assertEqual((decoded.getnchannels(), decoded.getframerate()), (1, 16000))
                else:
                    with self.assertRaisesRegex(MediaError, "não contém áudio"):
                        extract_audio(source, self.directory / "no-audio.wav")
                output = self.directory / f"saída {name}.mp4"
                started = time.perf_counter()
                render_clip(source, output, 0.1, 1.0, [], width=180, height=320)
                elapsed = time.perf_counter() - started
                output_info = probe_video(output)
                self.assertEqual((output_info["width"], output_info["height"]), (180, 320))
                self.assertAlmostEqual(output_info["duration_seconds"], 0.9, delta=0.12)
                self.assertEqual(audio_channels(output), channels)
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)
                if rotation:
                    reference, actual = gray_frame(source, 0.4), gray_frame(output, 0.3)
                    mean_error = sum(abs(a - b) for a, b in zip(reference, actual)) / len(reference)
                    self.assertLess(mean_error, 12, "Rendered orientation differs from FFmpeg's autorotated source")
                MEASUREMENTS.append({"case": name, "source_seconds": source_info["duration_seconds"],
                                     "render_seconds": round(elapsed, 4), "rendered_seconds": output_info["duration_seconds"],
                                     "output_bytes": output.stat().st_size, "channels": channels,
                                     "rotation_degrees": source_info["rotation_degrees"]})

    def test_visual_audio_and_caption_synchronization_after_trim(self):
        source = fixture_video(self.directory / "sinal de sincronização.mp4", duration=3, sync=True)
        for start in (0.4, 0.9):
            with self.subTest(start=start):
                expected = 1 - start
                output = self.directory / f"sinal {start}.mp4"
                baseline = self.directory / f"sem legenda {start}.mp4"
                render_clip(source, baseline, start, start + 2, [], width=180, height=320)
                render_clip(source, output, start, start + 2,
                            [{"start_seconds": expected, "end_seconds": expected + 0.3, "text": "sincronização"}],
                            width=180, height=320)
                frames = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(output),
                                         "-vf", "scale=1:1", "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"],
                                        check=True, capture_output=True, timeout=30).stdout
                visual = next(i / 20 for i, pixel in enumerate(frames) if pixel > 200)
                raw = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(output),
                                      "-map", "0:a:0", "-ac", "1", "-ar", "48000", "-f", "s16le", "pipe:1"],
                                     check=True, capture_output=True, timeout=30).stdout
                samples = array("h", raw)
                audio = next(i / 48000 for i in range(0, len(samples), 480)
                             if any(abs(s) > 500 for s in samples[i:i + 480]))
                self.assertAlmostEqual(visual, expected, delta=0.06)
                self.assertAlmostEqual(audio, expected, delta=0.06)
                self.assertAlmostEqual(audio, visual, delta=0.06)
                for instant, active in [(expected - 0.1, False), (expected + 0.05, True), (expected + 0.45, False)]:
                    a, b = gray_frame(baseline, instant), gray_frame(output, instant)
                    changed = sum(abs(x - y) > 48 for x, y in zip(a, b))
                    self.assertGreater(changed, 50) if active else self.assertLess(changed, 20)
                MEASUREMENTS.append({"case": "synchronization", "trim_start": start, "expected_onset": expected,
                                     "visual_onset": visual, "audio_onset": audio,
                                     "absolute_av_difference_seconds": round(abs(audio - visual), 4)})

    def test_anamorphic_shape_matches_square_pixel_reference(self):
        def center_shape(frame):
            row = frame[160 * 180:161 * 180]
            column = frame[90::180]
            spans = []
            for values, center in ((row, 90), (column, 160)):
                first = last = center
                while first > 0 and values[first - 1] > 220:
                    first -= 1
                while last + 1 < len(values) and values[last + 1] > 220:
                    last += 1
                spans.append(last - first + 1)
            return tuple(spans)

        for sar in ("2/1", "16/15"):
            with self.subTest(sar=sar):
                source = self.directory / f"anamórfico {sar.replace('/', '-')}.mp4"
                subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-f", "lavfi", "-i",
                                f"color=black:size=320x180:rate=10:duration=0.6,drawbox=x=120:y=50:w=80:h=80:color=white:t=fill,setsar={sar}",
                                "-c:v", "libx264", "-threads", "1", "-pix_fmt", "yuv420p", str(source)],
                               check=True, capture_output=True, timeout=30)
                before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                reference = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(source),
                                            "-frames:v", "1", "-vf",
                                            "scale=trunc(iw*sar/2)*2:ih,setsar=1,scale=180:320:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=180:320:(ow-iw)/2:(oh-ih)/2:black",
                                            "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1"],
                                           check=True, capture_output=True, timeout=30).stdout
                output = self.directory / f"render {sar.replace('/', '-')}.mp4"
                render_clip(source, output, 0, 0.5, [], width=180, height=320)
                expected, actual = center_shape(reference), center_shape(gray_frame(output, 0.2))
                self.assertGreater(min(expected), 10)
                for observed, correct in zip(actual, expected):
                    self.assertAlmostEqual(observed, correct, delta=2,
                                           msg=f"SAR {sar}: shape {actual}, square-pixel reference {expected}")
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before_hash)
                info = probe_video(output)
                self.assertEqual(info["display_width"], info["width"])
                self.assertEqual(info["display_height"], info["height"])
                MEASUREMENTS.append({"case": "anamorphic", "sar": sar,
                                     "reference_shape_pixels": expected, "rendered_shape_pixels": actual})

    def test_long_caption_is_bounded_on_a_nonuniform_video(self):
        source = fixture_video(self.directory / "contexto visual.mp4", duration=3)
        text = "Ação e emoção: João descobriu algo incrível no Minecraft, com contexto e clareza!"
        output, baseline = self.directory / "legendas.mp4", self.directory / "sem legendas.mp4"
        render_clip(source, baseline, 0, 3, [], width=180, height=320)
        render_clip(source, output, 0, 3, [{"start_seconds": 0, "end_seconds": 3, "text": text}], width=180, height=320)
        for instant in (0.2, 1.2, 2.2):
            before, after = gray_frame(baseline, instant), gray_frame(output, instant)
            white_glyph_rows = [i // 180 for i, (a, b) in enumerate(zip(before, after)) if b > 225 and a < 175]
            self.assertTrue(white_glyph_rows)
            self.assertGreater(min(white_glyph_rows), 210, "Caption covered the main content instead of remaining at the bottom")
            self.assertLess(max(white_glyph_rows), 280, "Caption must leave clearance above the bottom controls area")


class MediaFailureTests(unittest.TestCase):
    def test_probe_timeout_is_normalized(self):
        with patch.object(media.subprocess, "run", side_effect=subprocess.TimeoutExpired("ffprobe", 30)):
            with self.assertRaisesRegex(MediaError, "30 segundos"):
                media._probe(Path("owned-test.mp4"), "v:0", "stream=width", "ffprobe")

    def test_path_permission_errors_are_normalized_without_changing_permissions(self):
        with patch.object(Path, "is_file", side_effect=PermissionError("controlled test")):
            with self.assertRaises(MediaError):
                media._local_source(Path(__file__))
        with patch.object(Path, "is_dir", side_effect=PermissionError("controlled test")):
            with self.assertRaisesRegex(MediaError, "permissão"):
                media._destination(Path(__file__).parent / "not-created.mp4", Path(__file__))

    def test_stall_timeout_stops_the_owned_process(self):
        with tempfile.TemporaryDirectory(prefix="media-stall-", dir=Path(__file__).parent) as directory:
            created = []
            original = subprocess.Popen
            def start(*args, **kwargs):
                process = original(*args, **kwargs)
                created.append(process)
                return process
            began = time.perf_counter()
            with patch.object(media, "_STALL_TIMEOUT_SECONDS", 0.2), patch.object(media.subprocess, "Popen", side_effect=start):
                with self.assertRaisesRegex(MediaError, "andamento"):
                    media._run_ffmpeg([sys.executable, "-c", "import time;time.sleep(30)"], Path(directory), 1, None, None)
            elapsed = time.perf_counter() - began
            self.assertLess(elapsed, 4)
            self.assertIsNotNone(created[0].poll())
            MEASUREMENTS.append({"case": "controlled_stall", "configured_timeout_seconds": 0.2,
                                 "seconds_until_cleanup": round(elapsed, 4), "owned_process_exited": True})

    def test_exclusive_copy_fallback_preserves_a_collision(self):
        with tempfile.TemporaryDirectory(prefix="media-publish-", dir=Path(__file__).parent) as directory:
            source, target = Path(directory) / "owned.bin", Path(directory) / "existing.bin"
            source.write_bytes(b"new")
            target.write_bytes(b"original")
            with patch.object(media.os, "link", side_effect=OSError("controlled unsupported hardlink")):
                with self.assertRaises(FileExistsError):
                    media._publish(source, target, None)
            self.assertEqual(target.read_bytes(), b"original")

    def test_repeated_stalled_progress_does_not_reset_timeout(self):
        with tempfile.TemporaryDirectory(prefix="media-static-progress-", dir=Path(__file__).parent) as directory:
            command = [sys.executable, "-c",
                       "import time\nfor i in range(20):\n print('out_time_us=0', flush=True)\n time.sleep(.05)"]
            with patch.object(media, "_STALL_TIMEOUT_SECONDS", 0.2):
                with self.assertRaisesRegex(MediaError, "andamento"):
                    media._run_ffmpeg(command, Path(directory), 1, None, None)


if __name__ == "__main__":
    unittest.main()
