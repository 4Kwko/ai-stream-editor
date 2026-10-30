"""Unit tests use synthetic transcripts and a fake recognizer, never private media."""

import tempfile
from pathlib import Path
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

from ai_stream_editor.analysis import AnalysisError, captions_for_window, prepare_model, suggest_clips, transcribe


def segment(start, end, text, words=None):
    return {"start_seconds": start, "end_seconds": end, "text": text, "words": words or []}


def write_silent_audio(path, seconds=1):
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(16000)
        target.writeframes(b"\0\0" * int(16000 * seconds))


class CaptionTests(unittest.TestCase):
    def test_word_timing_is_relative_and_cropped_without_extra_words(self):
        speech = [segment(10, 14, "Antes Olá mundo! Depois", [
            {"start_seconds": 10, "end_seconds": 11, "text": "Antes"},
            {"start_seconds": 11, "end_seconds": 12, "text": "Olá"},
            {"start_seconds": 12, "end_seconds": 13, "text": "mundo!"},
            {"start_seconds": 13, "end_seconds": 14, "text": "Depois"}])]
        result = captions_for_window(speech, 11.5, 12.5)
        self.assertEqual(result[0]["text"], "Olá mundo!")
        self.assertEqual((result[0]["start_seconds"], result[0]["end_seconds"]), (0, 1))
        expanded = captions_for_window(speech, 11, 13)
        self.assertEqual(result[0]["id"], expanded[0]["id"])

    def test_long_text_is_grouped_and_ids_are_stable_after_retiming(self):
        speech = [segment(4, 14, "Uma explicação bastante longa com palavras suficientes para gerar várias legendas legíveis durante a fala completa.")]
        before = captions_for_window(speech, 3, 15)
        after = captions_for_window(speech, 2, 15)
        self.assertGreater(len(before), 1)
        self.assertEqual([c["id"] for c in before], [c["id"] for c in after])
        self.assertAlmostEqual(after[0]["start_seconds"], before[0]["start_seconds"] + 1)
        self.assertTrue(all(len(c["text"]) <= 46 for c in before))

    def test_invalid_numbers_and_windows_are_rejected(self):
        for start, end in [(float("nan"), 2), (0, float("inf")), (-1, 2), (2, 1), (True, 2)]:
            with self.subTest(start=start, end=end), self.assertRaises(AnalysisError):
                captions_for_window([], start, end)
        with self.assertRaises(AnalysisError):
            captions_for_window([segment(0, float("nan"), "texto")], 0, 2)
        with self.assertRaises(AnalysisError):
            captions_for_window([segment(0, 1, "texto", [
                {"start_seconds": 0, "end_seconds": float("inf"), "text": "texto"}])], 0, 2)


class SuggestionsTests(unittest.TestCase):
    def test_short_video_uses_real_bounds(self):
        result = suggest_clips([segment(1, 4, "Olha isso, finalmente consegui!")], 7)
        self.assertEqual(len(result), 1)
        self.assertEqual((result[0]["start_seconds"], result[0]["end_seconds"]), (0, 7))
        self.assertIn("Heurística", result[0]["reason"])
        self.assertLessEqual(result[0]["score"], 1)

    def test_silence_and_blank_transcript_return_no_candidates(self):
        self.assertEqual(suggest_clips([], 90), [])
        self.assertEqual(suggest_clips([segment(1, 2, "   ")], 90), [])

    def test_deterministic_deduplication_and_maximum(self):
        speech = [segment(i, i + 4, "Explicação do assunto.") for i in range(0, 180, 5)]
        speech[16]["text"] = "Não acredito! Finalmente descobri!"
        result = suggest_clips(speech, 180, max_clips=3)
        self.assertEqual(result, suggest_clips(speech, 180, max_clips=3))
        self.assertLessEqual(len(result), 3)
        self.assertTrue(any(c["start_seconds"] <= 80 < c["end_seconds"] for c in result))
        for a in result:
            self.assertGreaterEqual(a["start_seconds"], 0)
            self.assertLessEqual(a["end_seconds"], 180)
            self.assertGreaterEqual(a["end_seconds"] - a["start_seconds"], 30)
            self.assertLessEqual(a["end_seconds"] - a["start_seconds"], 60)
            for b in result:
                if a is b:
                    continue
                overlap = max(0, min(a["end_seconds"], b["end_seconds"]) - max(a["start_seconds"], b["start_seconds"]))
                shorter = min(a["end_seconds"] - a["start_seconds"], b["end_seconds"] - b["start_seconds"])
                self.assertLessEqual(overlap / shorter, 0.5)

    def test_invalid_durations_and_transcript_rejected(self):
        for duration in [0, -2, float("nan"), float("inf"), True]:
            with self.subTest(duration=duration), self.assertRaises(AnalysisError):
                suggest_clips([], duration)
        with self.assertRaises(AnalysisError):
            suggest_clips([], 90, min_duration=60, max_duration=30)
        with self.assertRaises(AnalysisError):
            suggest_clips([], 90, max_clips=0)
        with self.assertRaises(AnalysisError):
            suggest_clips([segment(-1, 4, "texto")], 90)


class TranscriptionTests(unittest.TestCase):
    def test_untrusted_model_name_is_rejected_before_runtime_or_network(self):
        with self.assertRaisesRegex(AnalysisError, "multilíngue"):
            prepare_model(Path("models"), "arbitrary-owner/repository")

    def test_prepare_uses_known_model_without_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def fake_download(name, **kwargs):
                destination = Path(kwargs["output_dir"])
                (destination / "model.bin").write_bytes(b"fake fixture model")
                return str(destination)
            with patch("faster_whisper.utils.download_model", side_effect=fake_download) as download:
                result = prepare_model(root, "tiny")
            self.assertEqual(result, root / "tiny")
            self.assertEqual(download.call_args.args, ("tiny",))
            self.assertIs(download.call_args.kwargs["use_auth_token"], False)

    def test_missing_model_does_not_start_a_download(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "synthetic.wav"
            write_silent_audio(audio)
            with patch("ai_stream_editor.analysis._load_model") as loader:
                with self.assertRaisesRegex(AnalysisError, "não preparado"):
                    transcribe(audio, root)
                loader.assert_not_called()

    def test_fake_recognizer_maps_timestamps_and_uses_portuguese(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base").mkdir()
            (root / "base/model.bin").write_bytes(b"fake model")
            audio = root / "synthetic.wav"
            write_silent_audio(audio)
            word = SimpleNamespace(start=0.1, end=0.7, word=" Olá!")
            detected = SimpleNamespace(start=0, end=1, text=" Olá! ", words=[word])
            model = unittest.mock.Mock()
            model.transcribe.return_value = (iter([detected]), SimpleNamespace(duration=1))
            progress = []
            with patch("ai_stream_editor.analysis._load_model", return_value=model):
                result = transcribe(audio, root, progress=progress.append)
            self.assertEqual(result[0]["text"], "Olá!")
            self.assertEqual(result[0]["words"][0]["start_seconds"], 0.1)
            self.assertEqual(model.transcribe.call_args.kwargs["language"], "pt")
            self.assertTrue(model.transcribe.call_args.kwargs["word_timestamps"])
            self.assertEqual(progress[-1], 1)

    def test_canceled_job_does_not_load_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base").mkdir()
            (root / "base/model.bin").write_bytes(b"fake model")
            audio = root / "synthetic.wav"
            write_silent_audio(audio)
            cancel = Event()
            cancel.set()
            with patch("ai_stream_editor.analysis._load_model") as loader:
                with self.assertRaisesRegex(AnalysisError, "cancelado"):
                    transcribe(audio, root, cancel=cancel)
                loader.assert_not_called()

    def test_long_audio_is_chunked_and_timestamps_are_global(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base").mkdir()
            (root / "base/model.bin").write_bytes(b"fake model")
            audio = root / "synthetic.wav"
            write_silent_audio(audio, seconds=2.5)
            model = unittest.mock.Mock()
            detected = SimpleNamespace(start=0, end=0.4, text=" teste ", words=[])
            model.transcribe.side_effect = [(iter([detected]), SimpleNamespace(duration=1)) for _ in range(3)]
            progress = []
            with patch("ai_stream_editor.analysis._load_model", return_value=model), patch("ai_stream_editor.analysis._CHUNK_SECONDS", 1):
                result = transcribe(audio, root, progress=progress.append)
            self.assertEqual([s["start_seconds"] for s in result], [0, 1, 2])
            self.assertEqual([s["end_seconds"] for s in result], [0.4, 1.4, 2.4])
            self.assertEqual(model.transcribe.call_count, 3)
            self.assertEqual([len(call.args[0]) for call in model.transcribe.call_args_list], [16000, 16000, 8000])
            self.assertTrue(all(call.args[0].dtype.name == "float32" for call in model.transcribe.call_args_list))
            self.assertEqual(progress[-1], 1)

    def test_clamped_segment_end_does_not_report_progress_past_its_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base").mkdir()
            (root / "base/model.bin").write_bytes(b"fake model")
            audio = root / "synthetic.wav"
            write_silent_audio(audio, seconds=2)
            model = unittest.mock.Mock()
            overrun = SimpleNamespace(start=0, end=5, text="primeira parte", words=[])
            normal = SimpleNamespace(start=0, end=.5, text="segunda parte", words=[])
            model.transcribe.side_effect = [(iter([overrun]), None), (iter([normal]), None)]
            progress = []
            with patch("ai_stream_editor.analysis._load_model", return_value=model), patch("ai_stream_editor.analysis._CHUNK_SECONDS", 1):
                transcribe(audio, root, progress=progress.append)
            self.assertEqual(progress, sorted(progress))
            self.assertEqual(progress[0], .5)

    def test_cancel_between_chunks_stops_before_another_native_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base").mkdir()
            (root / "base/model.bin").write_bytes(b"fake model")
            audio = root / "synthetic.wav"
            write_silent_audio(audio, seconds=2)
            cancel = Event()
            model = unittest.mock.Mock()
            model.transcribe.return_value = (iter([]), None)
            with patch("ai_stream_editor.analysis._load_model", return_value=model), patch("ai_stream_editor.analysis._CHUNK_SECONDS", 1):
                with self.assertRaisesRegex(AnalysisError, "cancelado"):
                    transcribe(audio, root, cancel=cancel, progress=lambda _: cancel.set())
            self.assertEqual(model.transcribe.call_count, 1)

    def test_truncated_audio_reports_an_error_before_native_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base").mkdir()
            (root / "base/model.bin").write_bytes(b"fake model")
            audio = root / "synthetic.wav"
            write_silent_audio(audio)
            audio.write_bytes(audio.read_bytes()[:-20])
            model = unittest.mock.Mock()
            with patch("ai_stream_editor.analysis._load_model", return_value=model):
                with self.assertRaisesRegex(AnalysisError, "truncado"):
                    transcribe(audio, root)
            model.transcribe.assert_not_called()


class EditorialBaselineTests(unittest.TestCase):
    """Deterministic transcript cases, not evidence of editorial quality on a real VOD."""

    def test_ordinary_conversation_does_not_fill_a_quota(self):
        speech = [segment(i, i + 5, "Hoje estamos conversando sobre o tempo e a rotina da semana.")
                  for i in range(0, 150, 6)]
        self.assertEqual(suggest_clips(speech, 180), [])

    def test_repetition_alone_is_not_a_sequence_of_highlights(self):
        speech = [segment(i, i + 4, "Não acredito! Finalmente consegui!") for i in range(0, 180, 5)]
        self.assertEqual(suggest_clips(speech, 180), [])

    def test_keyword_is_a_word_not_a_substring(self):
        speech = [segment(10, 17, "A família falou calmamente sobre o bezerro que estava no sítio.")]
        self.assertEqual(suggest_clips(speech, 180), [])

    def test_one_brief_word_is_not_enough_evidence(self):
        self.assertEqual(suggest_clips([segment(40, 40.4, "Incrível!")], 180), [])

    def test_sparse_reaction_does_not_drag_a_minute_of_silence(self):
        speech = [segment(90, 96, "Olha isso! Finalmente descobri uma maneira de resolver o problema!")]
        result = suggest_clips(speech, 240)
        self.assertEqual(len(result), 1)
        self.assertLess(result[0]["end_seconds"] - result[0]["start_seconds"], 20)
        self.assertLessEqual(result[0]["start_seconds"], 90)
        self.assertGreaterEqual(result[0]["end_seconds"], 96)

    def test_explanation_preserves_opening_and_conclusion(self):
        speech = [
            segment(10, 18, "Primeiro, vou explicar uma maneira simples de organizar os arquivos deste projeto."),
            segment(18, 27, "O problema aparece quando os nomes se repetem e ninguém encontra o documento correto."),
            segment(27, 35, "Separamos cada assunto em uma pasta, mantendo datas e títulos fáceis de reconhecer."),
            segment(35, 43, "Por fim, o resultado é uma organização que permite recuperar o trabalho sem confusão."),
        ]
        result = suggest_clips(speech, 180)
        self.assertTrue(result)
        self.assertLessEqual(result[0]["start_seconds"], 10)
        self.assertGreaterEqual(result[0]["end_seconds"], 43)

    def test_distinct_moments_and_both_media_edges_can_survive(self):
        speech = [
            segment(.2, 5, "Não acredito! Finalmente consegui terminar a pintura que estava preparando."),
            segment(90, 96, "Descobri uma surpresa: a receita fica muito melhor usando limão e gengibre!"),
            segment(175, 179, "Olha isso! O experimento terminou com um resultado incrível para nossa equipe!"),
        ]
        result = suggest_clips(speech, 180)
        self.assertEqual(len(result), 3)
        for event in speech:
            self.assertTrue(any(c["start_seconds"] <= event["start_seconds"]
                                and c["end_seconds"] >= event["end_seconds"] for c in result))
        self.assertTrue(all(0 <= c["start_seconds"] < c["end_seconds"] <= 180 for c in result))

    def test_context_can_cross_recognition_chunk_boundary(self):
        speech = [
            segment(292, 299, "Primeiro, precisamos entender por que a água estava escapando do recipiente."),
            segment(299, 304, "Agora descobri o erro! A borracha estava instalada do lado contrário."),
            segment(304, 312, "Por fim, corrigimos a posição e o resultado apareceu: não existe mais vazamento."),
        ]
        result = suggest_clips(speech, 630)
        self.assertTrue(result)
        self.assertTrue(any(c["start_seconds"] <= 292 and c["end_seconds"] >= 312 for c in result))
        self.assertTrue(any(cap["start_seconds"] + c["start_seconds"] >= 299
                            for c in result for cap in c["captions"]))

    def test_disjoint_identical_moments_are_deduplicated_by_text(self):
        phrase = "Olha isso! Finalmente consegui completar uma descoberta incrível para todo mundo!"
        result = suggest_clips([segment(10, 16, phrase), segment(200, 206, phrase)], 300)
        self.assertEqual(len(result), 1)

    def test_native_segment_spanning_silence_uses_word_bounds(self):
        words = []
        for offset in (10, 100):
            for index, text in enumerate("Olha isso! Finalmente consegui resolver o problema.".split()):
                words.append({"start_seconds": offset + index * .6,
                              "end_seconds": offset + (index + 1) * .6, "text": text})
        speech = [segment(10, 105, " ".join(w["text"] for w in words), words)]
        result = suggest_clips(speech, 240)
        self.assertEqual(len(result), 1)
        self.assertLess(result[0]["end_seconds"] - result[0]["start_seconds"], 20)

    def test_repeated_partial_utterance_is_not_another_distinct_moment(self):
        first = "Olha isso! Finalmente consegui resolver o problema. O resultado ficou incrível para nossa equipe!"
        repeated_tail = "O resultado ficou incrível para nossa equipe!"
        result = suggest_clips([segment(10, 18, first), segment(200, 205, repeated_tail)], 300)
        self.assertEqual(len(result), 1)

    def test_short_speech_run_keeps_intro_before_the_reaction(self):
        speech = [segment(94, 97, "Este é um teste local de vídeo."),
                  segment(98, 101, "Hoje vamos descobrir um momento interessante."),
                  segment(102, 106, "Olha isso! Finalmente consegui resolver o problema."),
                  segment(107, 110, "O resultado ficou incrível para nossa equipe.")]
        result = suggest_clips(speech, 630)
        self.assertEqual(len(result), 1)
        self.assertLessEqual(result[0]["start_seconds"], 94)
        self.assertGreaterEqual(result[0]["end_seconds"], 110)
        self.assertLess(result[0]["end_seconds"] - result[0]["start_seconds"], 30)

    def test_justification_only_names_signals_actually_used(self):
        result = suggest_clips([segment(10, 17, "Não acredito! Finalmente descobri uma solução simples para esta questão!")], 120)
        self.assertTrue(result)
        reason = result[0]["reason"].lower()
        self.assertIn("heurística", reason)
        self.assertIn("não é uma probabilidade", reason)
        self.assertFalse(any(term in reason for term in ["câmera", "imagem", "clutch", "viralização garantida"]))


if __name__ == "__main__":
    unittest.main()
