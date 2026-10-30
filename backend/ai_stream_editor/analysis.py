"""Offline speech recognition and an explicitly heuristic first-pass clip ranking."""

from __future__ import annotations

from bisect import bisect_left
from functools import lru_cache
import math
import os
from pathlib import Path
import re
from threading import Event, RLock
from typing import Callable
import unicodedata
import wave


class AnalysisError(RuntimeError):
    pass


_MODEL_NAMES = {"tiny", "base", "small"}
_MODEL_LOCK = RLock()
_CHUNK_SECONDS = 300
_CUES = ("nao acredito", "incrivel", "consegui", "caramba", "atencao", "finalmente",
         "descobri", "surpresa", "olha isso", "que aconteceu", "erro", "vitoria")
_OPENINGS = ("primeiro", "vou explicar", "o problema", "a ideia")
_CONCLUSIONS = ("por fim", "em resumo", "a conclusao", "por isso", "o resultado", "resolvido")


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AnalysisError(f"{name} precisa ser um número finito.")
    result = float(value)
    if not math.isfinite(result):
        raise AnalysisError(f"{name} precisa ser um número finito.")
    return result


def _check_cancel(cancel: Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise AnalysisError("Processamento cancelado.")


def _model_path(model_dir: Path, model_name: str) -> Path:
    if model_name not in _MODEL_NAMES:
        raise AnalysisError("Escolha um modelo multilíngue local: tiny, base ou small.")
    return Path(model_dir).expanduser().resolve() / model_name


def prepare_model(model_dir: Path, model_name: str = "base") -> Path:
    """Download only the known Systran model assets, never media or remote code."""
    destination = _model_path(model_dir, model_name)
    try:
        from faster_whisper.utils import download_model
    except ImportError as exc:
        raise AnalysisError("Instale as dependências locais do backend para preparar o modelo.") from exc
    with _MODEL_LOCK:
        try:
            destination.mkdir(parents=True, exist_ok=True)
            download_model(model_name, output_dir=str(destination),
                           cache_dir=str(destination.parent / ".hub-cache"),
                           use_auth_token=False)
        except Exception as exc:
            raise AnalysisError("Não foi possível baixar os pesos oficiais do modelo local.") from exc
        if not (destination / "model.bin").is_file():
            raise AnalysisError("O download não produziu os pesos do modelo local.")
        _load_model.cache_clear()
    return destination


@lru_cache(maxsize=1)
def _load_model(path: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise AnalysisError("Transcrição indisponível: instale as dependências locais do backend.") from exc
    try:
        return WhisperModel(path, device="cpu", compute_type="int8",
                            cpu_threads=min(4, os.cpu_count() or 1), num_workers=1,
                            local_files_only=True)
    except Exception as exc:
        raise AnalysisError("Não foi possível carregar o modelo local em CPU/int8.") from exc


def _audio_parts(audio: Path):
    # Bound faster-whisper's decoded waveform, which otherwise grows with VOD length.
    try:
        import numpy as np
    except ImportError as exc:
        raise AnalysisError("Instale as dependências locais para ler o áudio de transcrição.") from exc
    try:
        with wave.open(str(audio), "rb") as source:
            rate = source.getframerate()
            total_frames = source.getnframes()
            if (source.getcomptype() != "NONE" or rate != 16000 or total_frames <= 0
                    or source.getnchannels() != 1 or source.getsampwidth() != 2):
                raise AnalysisError("O áudio precisa ser WAV PCM 16-bit mono a 16 kHz, extraído pelo backend.")
            total = total_frames / rate
            chunk_frames = rate * _CHUNK_SECONDS
            for first in range(0, total_frames, chunk_frames):
                count = min(chunk_frames, total_frames - first)
                frames = source.readframes(count)
                if len(frames) != count * 2:
                    raise AnalysisError("O arquivo de áudio está truncado.")
                samples = np.frombuffer(frames, dtype="<i2").astype(np.float32)
                samples *= 1 / 32768.0
                yield samples, first / rate, count / rate, total
    except (wave.Error, EOFError, OSError) as exc:
        raise AnalysisError("Não foi possível ler o WAV PCM extraído do vídeo.") from exc


def transcribe(audio: Path, model_dir: Path, *, model_name: str = "base",
               cancel: Event | None = None,
               progress: Callable[[float], None] | None = None) -> list[dict]:
    audio = Path(audio).expanduser().resolve()
    if not audio.is_file():
        raise AnalysisError("O áudio local para transcrição não foi encontrado.")
    destination = _model_path(model_dir, model_name)
    if not (destination / "model.bin").is_file():
        raise AnalysisError(f"Modelo {model_name} não preparado. Execute a preparação local do modelo.")
    _check_cancel(cancel)
    with _MODEL_LOCK:
        model = _load_model(str(destination))
        _check_cancel(cancel)
        iterator = None
        try:
            output = []
            for part, offset, part_duration, total in _audio_parts(audio):
                _check_cancel(cancel)
                iterator, _ = model.transcribe(part, language="pt", beam_size=5,
                                               word_timestamps=True, vad_filter=True,
                                               condition_on_previous_text=False)
                for segment in iterator:
                    _check_cancel(cancel)
                    text = segment.text.strip()
                    start = min(part_duration, max(0.0, _number(segment.start, "Início transcrito")))
                    end = min(part_duration, max(0.0, _number(segment.end, "Fim transcrito")))
                    if text and end > start:
                        words = [{"start_seconds": offset + min(part_duration, max(0.0, _number(w.start, "Início da palavra"))),
                                  "end_seconds": offset + min(part_duration, max(0.0, _number(w.end, "Fim da palavra"))),
                                  "text": w.word.strip()}
                                 for w in (segment.words or []) if w.word.strip()]
                        output.append({"start_seconds": offset + start,
                                       "end_seconds": offset + end,
                                       "text": text, "words": words})
                    if progress:
                        progress(min(0.99, max(0.0, (offset + end) / total)))
                if progress:
                    progress(min(0.99, (offset + part_duration) / total))
            _check_cancel(cancel)
            _segments(output)
            if progress:
                progress(1.0)
            return output
        except AnalysisError:
            raise
        except Exception as exc:
            raise AnalysisError("Falha na transcrição local. Confira o áudio e o modelo preparado.") from exc
        finally:
            if iterator is not None and hasattr(iterator, "close"):
                iterator.close()


def _segments(items: list[dict]) -> list[dict]:
    if not isinstance(items, list):
        raise AnalysisError("A transcrição precisa ser uma lista de segmentos.")
    result = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise AnalysisError("Segmento de transcrição inválido.")
        start = _number(item.get("start_seconds"), "Início do segmento")
        end = _number(item.get("end_seconds"), "Fim do segmento")
        if start < 0 or end <= start:
            raise AnalysisError("Os segmentos precisam ter início não negativo e fim posterior.")
        text = item.get("text", "")
        if not isinstance(text, str):
            raise AnalysisError("O texto do segmento precisa ser uma string.")
        words = item.get("words") or []
        if not isinstance(words, list):
            raise AnalysisError("Palavras do segmento inválidas.")
        clean_words = []
        for word in words:
            if not isinstance(word, dict) or not isinstance(word.get("text"), str):
                raise AnalysisError("Palavra de transcrição inválida.")
            a = _number(word.get("start_seconds"), "Início da palavra")
            b = _number(word.get("end_seconds"), "Fim da palavra")
            if a < 0 or b < a:
                raise AnalysisError("Tempos de palavra inválidos.")
            if word["text"].strip() and b > a:
                clean_words.append({"start_seconds": a, "end_seconds": b,
                                    "text": word["text"].strip()})
        if text.strip():
            result.append({"index": index, "start_seconds": start, "end_seconds": end,
                           "text": text.strip(), "words": sorted(clean_words, key=lambda w: w["start_seconds"])})
    return sorted(result, key=lambda s: s["start_seconds"])


def _caption_groups(segment: dict):
    units = segment["words"]
    if not units:
        tokens = segment["text"].split()
        step = (segment["end_seconds"] - segment["start_seconds"]) / len(tokens)
        units = [{"text": token, "start_seconds": segment["start_seconds"] + i * step,
                  "end_seconds": segment["start_seconds"] + (i + 1) * step}
                 for i, token in enumerate(tokens)]
    group = []
    first = 0
    for index, word in enumerate(units):
        too_long = group and (sum(len(w["text"]) + 1 for w in group) + len(word["text"]) > 46
                              or word["end_seconds"] - group[0]["start_seconds"] > 3.5)
        if too_long:
            yield first, group
            group = []
        if not group:
            first = index
        group.append(word)
        if re.search(r"[.!?…]$", word["text"]):
            yield first, group
            group = []
    if group:
        yield first, group


def captions_for_window(segments: list[dict], start: float, end: float) -> list[dict]:
    start = _number(start, "Início do corte")
    end = _number(end, "Fim do corte")
    if start < 0 or end <= start:
        raise AnalysisError("O corte precisa ter início não negativo e fim posterior.")
    captions = []
    for segment in _segments(segments):
        if segment["end_seconds"] <= start or segment["start_seconds"] >= end:
            continue
        for first, group in _caption_groups(segment):
            visible = [w for w in group if w["end_seconds"] > start and w["start_seconds"] < end]
            if visible:
                captions.append({"id": f"segment-{segment['index']}-word-{first}",
                                 "start_seconds": round(max(start, visible[0]["start_seconds"]) - start, 6),
                                 "end_seconds": round(min(end, visible[-1]["end_seconds"]) - start, 6),
                                 "text": " ".join(w["text"] for w in visible)})
    return captions


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def _has_phrase(text: str, phrase: str) -> bool:
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def _speech_units(segments: list[dict]) -> list[dict]:
    # Native segments can span long VAD gaps. Rank actual sentences, not that silence.
    units = []
    for segment in segments:
        if not segment["words"]:
            units.append(segment)
            continue
        group = []
        for word in segment["words"]:
            if group and word["start_seconds"] - group[-1]["end_seconds"] > 2:
                units.append({"start_seconds": group[0]["start_seconds"],
                              "end_seconds": group[-1]["end_seconds"],
                              "text": " ".join(w["text"] for w in group), "words": group})
                group = []
            group.append(word)
            if re.search(r"[.!?…]$", word["text"]):
                units.append({"start_seconds": group[0]["start_seconds"],
                              "end_seconds": group[-1]["end_seconds"],
                              "text": " ".join(w["text"] for w in group), "words": group})
                group = []
        if group:
            units.append({"start_seconds": group[0]["start_seconds"],
                          "end_seconds": group[-1]["end_seconds"],
                          "text": " ".join(w["text"] for w in group), "words": group})
    return sorted(units, key=lambda s: s["start_seconds"])


def _window_evidence(nearby: list[dict], start: float, end: float):
    texts = []
    for segment in nearby:
        if segment["words"]:
            texts.append(" ".join(w["text"] for w in segment["words"]
                                  if start <= w["start_seconds"] < w["end_seconds"] <= end))
        elif start <= segment["start_seconds"] and segment["end_seconds"] <= end:
            texts.append(segment["text"])
    text = " ".join(t for t in texts if t)
    folded = _fold(text)
    tokens = re.findall(r"\b\w+\b", folded)
    coverage = min(1.0, sum(max(0.0, min(end, s["end_seconds"]) - max(start, s["start_seconds"]))
                           for s in nearby) / (end - start))
    voiced = coverage * (end - start)
    phrases = [" ".join(re.findall(r"\b\w+\b", _fold(t))) for t in texts if t]
    if (len(tokens) < 4 or len(set(tokens)) < 4 or voiced < 2
            or (len(phrases) >= 2 and len(set(phrases)) == 1)
            or (len(tokens) >= 12 and len(set(tokens)) / len(tokens) < .15)):
        return None
    cue_count = sum(_has_phrase(folded, cue) for cue in _CUES)
    explanation = (len(tokens) >= 18 and len(set(phrases)) >= 2
                   and any(_has_phrase(folded, marker) for marker in _OPENINGS)
                   and any(_has_phrase(folded, marker) for marker in _CONCLUSIONS))
    if not cue_count and not explanation:
        return None
    emphasis = min(4, text.count("!") + text.count("?"))
    score = round(min(.95, .2 + .12 * min(cue_count, 3) + .04 * emphasis
                      + .2 * coverage + (.22 if explanation else 0)), 3)
    signals = []
    if cue_count:
        signals.append("expressões de reação ou descoberta")
    if explanation:
        signals.append("marcadores textuais de explicação e conclusão")
    if emphasis:
        signals.append("pontuação de pergunta ou ênfase")
    signals.append("limites temporais e margem de contexto")
    fingerprint = set(zip(tokens, tokens[1:], tokens[2:]))
    return text, score, signals, fingerprint


def suggest_clips(segments: list[dict], duration_seconds: float, *, min_duration: float = 30,
                  max_duration: float = 60, max_clips: int = 12) -> list[dict]:
    duration = _number(duration_seconds, "Duração do vídeo")
    minimum = _number(min_duration, "Duração mínima")
    maximum = _number(max_duration, "Duração máxima")
    if duration <= 0 or minimum <= 0 or maximum < minimum:
        raise AnalysisError("Durações inválidas para sugerir cortes.")
    if isinstance(max_clips, bool) or not isinstance(max_clips, int) or not 1 <= max_clips <= 100:
        raise AnalysisError("A quantidade de cortes precisa estar entre 1 e 100.")
    speech = [s for s in _speech_units(_segments(segments)) if s["start_seconds"] < duration]
    if not speech:
        return []
    starts = [s["start_seconds"] for s in speech]
    context_first = []
    first = 0
    for index, segment in enumerate(speech):
        if index and segment["start_seconds"] - speech[index - 1]["end_seconds"] > 5:
            first = index
        context_first.append(first)
    target = minimum / 2 + maximum / 2
    candidates = []
    seen = set()
    for index, segment in enumerate(speech):
        context = min(index, max(context_first[index], bisect_left(starts, segment["end_seconds"] - maximum + 2)))
        start = max(0.0, speech[context]["start_seconds"] - 2.0)
        if duration - start < minimum:
            start = max(0.0, duration - min(minimum, duration))
        limit = min(duration, start + maximum)
        right = bisect_left(starts, limit)
        left = max(0, bisect_left(starts, start) - 1)
        nearby = [s for s in speech[left:right] if s["end_seconds"] > start]
        ends = [min(duration, s["end_seconds"]) for s in nearby
                if max(start + min(minimum, duration), segment["end_seconds"]) <= s["end_seconds"] <= limit]
        end = min(ends, key=lambda v: abs(v - (start + target))) if ends else limit
        if duration <= minimum:
            start, end = 0.0, duration
        nearby = [s for s in nearby if s["start_seconds"] < end]
        if nearby and duration > minimum:
            first_speech = max(start, min(s["start_seconds"] for s in nearby))
            last_speech = min(end, max(s["end_seconds"] for s in nearby))
            if first_speech - start > 5:
                start = max(start, first_speech - 2)
            if end - last_speech > max(4, (end - start) * .25):
                end = min(end, last_speech + 2)
        key = (round(start, 3), round(end, 3))
        if key in seen:
            continue
        seen.add(key)
        evidence = _window_evidence(nearby, start, end)
        if evidence is None:
            continue
        text, score, signals, fingerprint = evidence
        candidates.append({"start_seconds": round(start, 6), "end_seconds": round(end, 6),
                           "title": " ".join(text.split()[:10])[:100],
                           "reason": "Heurística local: " + ", ".join(signals) + ". Revise o contexto; a pontuação não é uma probabilidade.",
                           "score": score, "_fingerprint": fingerprint})
    selected = []
    for candidate in sorted(candidates, key=lambda c: (-c["score"], c["start_seconds"])):
        a, b = candidate["start_seconds"], candidate["end_seconds"]
        duplicate = any(max(0.0, min(b, old["end_seconds"]) - max(a, old["start_seconds"]))
                        / min(b - a, old["end_seconds"] - old["start_seconds"]) > 0.5
                        for old in selected)
        duplicate = duplicate or any(len(candidate["_fingerprint"] & old["_fingerprint"])
                                     / max(1, min(len(candidate["_fingerprint"]), len(old["_fingerprint"]))) >= .9
                                     for old in selected)
        if not duplicate:
            candidate["captions"] = captions_for_window(segments, a, b)
            selected.append(candidate)
        if len(selected) >= max_clips:
            break
    for candidate in selected:
        candidate.pop("_fingerprint")
    return selected
