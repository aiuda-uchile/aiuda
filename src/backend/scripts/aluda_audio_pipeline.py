#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Forzar CPU para evitar problemas con CUDA en GPUs antiguas
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from faster_whisper import WhisperModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch


APP_NAME = "ALUDA Audio Pipeline"
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_TRANSLATION_MODEL = "facebook/nllb-200-distilled-600M"

# Whisper suele devolver códigos cortos tipo es, en, pt, gl
# NLLB usa códigos FLORES-200
NLLB_LANG_MAP = {
    "es": "spa_Latn",
    "en": "eng_Latn",
    "pt": "por_Latn",
    "gl": "glg_Latn",
}

ALLOWED_TARGETS = {"es", "en", "pt", "gl"}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ALUDA - transcripción y traducción de audio para backend"
    )
    parser.add_argument("input_file", type=str, help="Archivo de audio de entrada")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=True,
        help="Directorio de salida",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        default="",
        help="ID de tarea del backend",
    )
    parser.add_argument(
        "--source-lang",
        type=str,
        default=None,
        help="Idioma origen manual (es, en, pt, gl). Si no se indica, se detecta automáticamente.",
    )
    parser.add_argument(
        "--translate-to",
        nargs="*",
        default=["es", "en", "pt", "gl"],
        help="Idiomas destino. Ejemplo: --translate-to es en pt gl",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default=DEFAULT_WHISPER_MODEL,
        help="Modelo de faster-whisper. Ejemplos: tiny, base, small, medium",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size para Whisper",
    )
    parser.add_argument(
        "--compute-type",
        type=str,
        default="int8",
        help="Tipo de cómputo de Whisper en CPU. Recomendado: int8",
    )
    parser.add_argument(
        "--max-translation-chars",
        type=int,
        default=800,
        help="Tamaño máximo por bloque de traducción",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sanitize_stem(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name)


def normalize_lang_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    code = code.strip().lower()

    aliases = {
        "es-es": "es",
        "es_419": "es",
        "en-us": "en",
        "en-gb": "en",
        "pt-br": "pt",
        "pt-pt": "pt",
        "gl-es": "gl",
    }
    return aliases.get(code, code)


def format_timestamp_srt(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def format_timestamp_vtt(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_output_filenames(output_dir: Path) -> List[str]:
    return sorted([p.name for p in output_dir.iterdir() if p.is_file()])


def build_logger(output_dir: Path) -> logging.Logger:
    logger = logging.getLogger("aluda_audio")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    fh = logging.FileHandler(output_dir / "job.log", encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


def write_status(
    output_dir: Path,
    task_id: str,
    state: str,
    progress: int,
    stage: str,
    message: str,
    extra: Optional[dict] = None,
) -> None:
    payload = {
        "task_id": task_id,
        "state": state,
        "progress": progress,
        "current_stage": stage,
        "message": message,
        "outputs": collect_output_filenames(output_dir),
    }
    if extra:
        payload.update(extra)
    write_json(output_dir / "status.json", payload)


def split_text_for_translation(text: str, max_chars: int) -> List[str]:
    text = normalize_whitespace(text)
    if not text:
        return []

    parts = re.split(r"(?<=[\.\!\?\:\;])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        parts = [text]

    chunks: List[str] = []
    current = ""

    for part in parts:
        candidate = part if not current else current + " " + part
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(part) <= max_chars:
                current = part
            else:
                # corte de seguridad
                start = 0
                while start < len(part):
                    chunks.append(part[start:start + max_chars])
                    start += max_chars
                current = ""

    if current:
        chunks.append(current)

    return chunks


class NllbTranslator:
    def __init__(self, model_name: str = DEFAULT_TRANSLATION_MODEL) -> None:
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model.to("cpu")
        self.model.eval()

        try:
            torch.set_num_threads(4)
        except Exception:
            pass

    def translate_text(self, text: str, src_code: str, tgt_code: str, max_chars: int = 800) -> str:
        text = normalize_whitespace(text)
        if not text:
            return text
        if src_code == tgt_code:
            return text

        src_nllb = NLLB_LANG_MAP.get(src_code)
        tgt_nllb = NLLB_LANG_MAP.get(tgt_code)

        if not src_nllb:
            raise ValueError(f"Idioma origen no soportado para traducción NLLB: {src_code}")
        if not tgt_nllb:
            raise ValueError(f"Idioma destino no soportado para traducción NLLB: {tgt_code}")

        chunks = split_text_for_translation(text, max_chars=max_chars)
        out_chunks: List[str] = []

        for chunk in chunks:
            self.tokenizer.src_lang = src_nllb
            inputs = self.tokenizer(chunk, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt_nllb),
                    max_length=512,
                )
            translated = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True,
            )[0]
            out_chunks.append(normalize_whitespace(translated))

        return normalize_whitespace("\n\n".join(out_chunks))


def transcribe_audio(
    input_file: Path,
    model_name: str,
    beam_size: int,
    compute_type: str,
    source_lang: Optional[str],
    logger: logging.Logger,
) -> Tuple[List[dict], dict]:
    logger.info("Cargando modelo Whisper en CPU: %s", model_name)

    model = WhisperModel(
        model_name,
        device="cpu",
        compute_type=compute_type,
        cpu_threads=4,
    )

    logger.info("Iniciando transcripción de %s", input_file.name)

    segments_iter, info = model.transcribe(
        str(input_file),
        beam_size=beam_size,
        language=source_lang,
        vad_filter=True,
        word_timestamps=False,
    )

    segments: List[dict] = []
    for seg in segments_iter:
        segments.append(
            {
                "id": len(segments) + 1,
                "start": float(seg.start),
                "end": float(seg.end),
                "text": normalize_whitespace(seg.text),
            }
        )

    info_dict = {
        "language": normalize_lang_code(getattr(info, "language", None)),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "duration_after_vad": getattr(info, "duration_after_vad", None),
    }

    return segments, info_dict


def segments_to_plain_text(segments: List[dict]) -> str:
    return normalize_whitespace("\n".join(seg["text"] for seg in segments if seg["text"].strip()))


def write_srt(path: Path, segments: List[dict]) -> None:
    lines: List[str] = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(
            f"{format_timestamp_srt(seg['start'])} --> {format_timestamp_srt(seg['end'])}"
        )
        lines.append(seg["text"])
        lines.append("")
    write_text(path, "\n".join(lines).strip() + "\n")


def write_vtt(path: Path, segments: List[dict]) -> None:
    lines: List[str] = ["WEBVTT", ""]
    for seg in segments:
        lines.append(
            f"{format_timestamp_vtt(seg['start'])} --> {format_timestamp_vtt(seg['end'])}"
        )
        lines.append(seg["text"])
        lines.append("")
    write_text(path, "\n".join(lines).strip() + "\n")


def translate_segments(
    segments: List[dict],
    translator: NllbTranslator,
    src_lang: str,
    tgt_lang: str,
    max_chars: int,
    logger: logging.Logger,
) -> List[dict]:
    translated_segments: List[dict] = []
    total = len(segments)

    for i, seg in enumerate(segments, start=1):
        text = seg["text"].strip()
        logger.info("Traduciendo segmento %s/%s -> %s", i, total, tgt_lang)

        if not text:
            translated_text = ""
        else:
            translated_text = translator.translate_text(
                text,
                src_code=src_lang,
                tgt_code=tgt_lang,
                max_chars=max_chars,
            )

        translated_segments.append(
            {
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": normalize_whitespace(translated_text),
            }
        )

    return translated_segments


def process_audio(
    input_file: Path,
    output_dir: Path,
    task_id: str,
    source_lang: Optional[str],
    target_langs: List[str],
    whisper_model: str,
    beam_size: int,
    compute_type: str,
    max_translation_chars: int,
) -> int:
    ensure_dir(output_dir)
    logger = build_logger(output_dir)

    stem = sanitize_stem(input_file.stem)

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=5,
        stage="startup",
        message="Inicializando tarea de audio",
        extra={"input_file": str(input_file)},
    )

    logger.info("%s", APP_NAME)
    logger.info("Archivo de entrada: %s", input_file)
    logger.info("Directorio de salida: %s", output_dir)

    manual_source_lang = normalize_lang_code(source_lang)
    if manual_source_lang:
        logger.info("Idioma origen manual: %s", manual_source_lang)
    else:
        logger.info("Idioma origen: detección automática")

    clean_targets = []
    for lang in target_langs:
        lang = normalize_lang_code(lang)
        if lang in ALLOWED_TARGETS and lang not in clean_targets:
            clean_targets.append(lang)

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=15,
        stage="transcription",
        message="Transcribiendo audio",
    )

    segments, info = transcribe_audio(
        input_file=input_file,
        model_name=whisper_model,
        beam_size=beam_size,
        compute_type=compute_type,
        source_lang=manual_source_lang,
        logger=logger,
    )

    detected_lang = normalize_lang_code(info.get("language"))
    used_source_lang = manual_source_lang or detected_lang

    if not used_source_lang:
        logger.warning("No se pudo detectar idioma. Se asumirá 'es' para traducción.")
        used_source_lang = "es"

    logger.info("Idioma detectado/usado: %s", used_source_lang)

    original_txt = segments_to_plain_text(segments)

    transcript_payload = {
        "task_id": task_id,
        "input_file": str(input_file),
        "source_language_requested": manual_source_lang,
        "source_language_detected": detected_lang,
        "source_language_used": used_source_lang,
        "whisper_info": info,
        "segments": segments,
    }

    write_text(output_dir / f"{stem}.original.txt", original_txt)
    write_srt(output_dir / f"{stem}.original.srt", segments)
    write_vtt(output_dir / f"{stem}.original.vtt", segments)
    write_json(output_dir / f"{stem}.original.json", transcript_payload)

    logger.info("Transcripción original generada.")

    translated_outputs: Dict[str, dict] = {}

    if clean_targets:
        write_status(
            output_dir,
            task_id=task_id,
            state="processing",
            progress=55,
            stage="translation",
            message="Traduciendo transcripción",
            extra={"source_language_used": used_source_lang},
        )

        if used_source_lang not in NLLB_LANG_MAP:
            logger.warning(
                "Idioma origen %s no soportado por el traductor NLLB configurado. Se omiten traducciones.",
                used_source_lang,
            )
        else:
            translator = NllbTranslator(model_name=DEFAULT_TRANSLATION_MODEL)

        for idx, tgt_lang in enumerate(clean_targets, start=1):
            logger.info(
                "Generando salida %s/%s: %s -> %s",
                idx,
                len(clean_targets),
                used_source_lang,
                tgt_lang,
            )

            if tgt_lang == used_source_lang:
                translated_segments = [dict(seg) for seg in segments]
            else:
                translated_segments = translate_segments(
                    segments=segments,
                    translator=translator,
                    src_lang=used_source_lang,
                    tgt_lang=tgt_lang,
                    max_chars=max_translation_chars,
                    logger=logger,
                )

            translated_txt = segments_to_plain_text(translated_segments)

            write_text(output_dir / f"{stem}.{tgt_lang}.txt", translated_txt)
            write_srt(output_dir / f"{stem}.{tgt_lang}.srt", translated_segments)
            write_vtt(output_dir / f"{stem}.{tgt_lang}.vtt", translated_segments)
            write_json(
                output_dir / f"{stem}.{tgt_lang}.json",
                {
                    "task_id": task_id,
                    "source_language": used_source_lang,
                    "target_language": tgt_lang,
                    "segments": translated_segments,
                },
            )

            translated_outputs[tgt_lang] = {
                "txt": f"{stem}.{tgt_lang}.txt",
                "srt": f"{stem}.{tgt_lang}.srt",
                "vtt": f"{stem}.{tgt_lang}.vtt",
                "json": f"{stem}.{tgt_lang}.json",
            }

            logger.info("Salida completada: %s", tgt_lang)

    success_message = "Procesamiento completado correctamente."

    result_payload = {
        "ok": True,
        "task_id": task_id,
        "status": "finished",
        "message": success_message,
        "error": None,
        "input_file": str(input_file),
        "source_language_requested": manual_source_lang,
        "source_language_detected": detected_lang,
        "source_language_used": used_source_lang,
        "target_languages_requested": clean_targets,
        "whisper_model": whisper_model,
        "outputs": collect_output_filenames(output_dir),
        "original": {
            "txt": f"{stem}.original.txt",
            "srt": f"{stem}.original.srt",
            "vtt": f"{stem}.original.vtt",
            "json": f"{stem}.original.json",
        },
        "translations": translated_outputs,
    }

    write_json(output_dir / "result.json", result_payload)

    write_status(
        output_dir,
        task_id=task_id,
        state="finished",
        progress=100,
        stage="done",
        message=success_message,
        extra={
            "ok": True,
            "error": None,
            "source_language_used": used_source_lang,
            "result_file": "result.json",
        },
    )

    logger.info("Proceso completado correctamente.")
    return 0


def main() -> int:
    args = parse_args()

    input_file = Path(args.input_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not input_file.exists():
        print(f"[ERROR] No existe el archivo: {input_file}", file=sys.stderr)
        return 1

    if not input_file.is_file():
        print(f"[ERROR] La entrada no es un archivo válido: {input_file}", file=sys.stderr)
        return 1

    try:
        return process_audio(
            input_file=input_file,
            output_dir=output_dir,
            task_id=args.task_id,
            source_lang=args.source_lang,
            target_langs=args.translate_to,
            whisper_model=args.whisper_model,
            beam_size=args.beam_size,
            compute_type=args.compute_type,
            max_translation_chars=args.max_translation_chars,
        )
    except Exception as e:
        ensure_dir(output_dir)

        error_message = f"Error al procesar el audio: {e}"

        write_json(
            output_dir / "result.json",
            {
                "ok": False,
                "task_id": args.task_id,
                "status": "error",
                "message": error_message,
                "error": str(e),
                "outputs": collect_output_filenames(output_dir),
            },
        )

        write_status(
            output_dir,
            task_id=args.task_id,
            state="error",
            progress=100,
            stage="failed",
            message=error_message,
            extra={
                "ok": False,
                "error": str(e),
                "result_file": "result.json",
            },
        )

        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())