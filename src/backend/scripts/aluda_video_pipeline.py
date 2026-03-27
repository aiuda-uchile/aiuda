#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Forzar CPU para mantener un comportamiento predecible en backend
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from faster_whisper import WhisperModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch


APP_NAME = "ALUDA Video Pipeline"
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_TRANSLATION_MODEL = "facebook/nllb-200-distilled-600M"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}

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
        description="ALUDA - transcripción y traducción de vídeo para backend"
    )
    parser.add_argument("input_file", type=str, help="Archivo de vídeo de entrada")
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
    parser.add_argument(
        "--burn-subtitles",
        action="store_true",
        help="Genera además vídeos MP4 con subtítulos incrustados si ffmpeg está disponible.",
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


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


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
    logger = logging.getLogger("aluda_video")
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
                start = 0
                while start < len(part):
                    chunks.append(part[start:start + max_chars])
                    start += max_chars
                current = ""

    if current:
        chunks.append(current)

    return chunks


def is_repetitive_text(text: str) -> bool:
    t = normalize_whitespace(text).lower()
    if not t:
        return True

    if t.count("@") >= 2:
        return True

    if len(t) > 80 and t.count(" ") <= 1:
        return True

    words = re.findall(r"\w+", t, flags=re.UNICODE)
    if len(words) >= 8:
        freqs: Dict[str, int] = {}
        for word in words:
            freqs[word] = freqs.get(word, 0) + 1
        if max(freqs.values()) >= max(6, int(len(words) * 0.7)):
            return True

    for size in range(3, min(25, len(t) // 4 + 1)):
        pattern = t[:size]
        if pattern and t.startswith(pattern * 6):
            return True

    return False


def clean_segment_text(text: str) -> str:
    text = normalize_whitespace(text)
    if is_repetitive_text(text):
        return ""
    return text


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


def transcribe_video(
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

    logger.info("Iniciando transcripción de vídeo: %s", input_file.name)

    segments_iter, info = model.transcribe(
        str(input_file),
        beam_size=beam_size,
        language=source_lang,
        vad_filter=True,
        word_timestamps=False,
        condition_on_previous_text=False,
    )

    segments: List[dict] = []
    removed_segments = 0

    for seg in segments_iter:
        text = clean_segment_text(seg.text)
        if not text:
            removed_segments += 1
            continue

        segments.append(
            {
                "id": len(segments) + 1,
                "start": float(seg.start),
                "end": float(seg.end),
                "text": text,
            }
        )

    info_dict = {
        "language": normalize_lang_code(getattr(info, "language", None)),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "duration_after_vad": getattr(info, "duration_after_vad", None),
        "removed_segments": removed_segments,
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


def escape_subtitles_path_for_ffmpeg(path: Path) -> str:
    value = str(path.resolve())
    value = value.replace("\\", "\\\\")
    value = value.replace(":", "\\:")
    value = value.replace("'", r"\'")
    value = value.replace(",", r"\,")
    value = value.replace("[", r"\[")
    value = value.replace("]", r"\]")
    return value


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def burn_subtitles_into_video(input_video: Path, srt_file: Path, output_video: Path) -> None:
    if not ffmpeg_available():
        raise EnvironmentError(
            "No se encontró ffmpeg en el sistema. Instálalo o ejecuta el script sin --burn-subtitles."
        )

    safe_srt = escape_subtitles_path_for_ffmpeg(srt_file)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-vf",
        f"subtitles='{safe_srt}'",
        "-c:a",
        "copy",
        str(output_video),
    ]
    subprocess.run(cmd, check=True)


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

        translated_text = clean_segment_text(translated_text) or seg["text"]

        translated_segments.append(
            {
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": normalize_whitespace(translated_text),
            }
        )

    return translated_segments


def write_variant_files(
    output_dir: Path,
    stem: str,
    variant: str,
    input_file: Path,
    source_lang_requested: Optional[str],
    source_lang_detected: Optional[str],
    source_lang_used: str,
    whisper_info: dict,
    segments: List[dict],
    target_language: Optional[str] = None,
) -> Dict[str, str]:
    txt_name = f"{stem}.{variant}.txt"
    srt_name = f"{stem}.{variant}.srt"
    vtt_name = f"{stem}.{variant}.vtt"
    json_name = f"{stem}.{variant}.json"

    plain_text = segments_to_plain_text(segments)
    write_text(output_dir / txt_name, plain_text)
    write_srt(output_dir / srt_name, segments)
    write_vtt(output_dir / vtt_name, segments)
    write_json(
        output_dir / json_name,
        {
            "input_file": str(input_file),
            "source_language_requested": source_lang_requested,
            "source_language_detected": source_lang_detected,
            "source_language_used": source_lang_used,
            "target_language": target_language,
            "whisper_info": whisper_info,
            "segments": segments,
        },
    )

    return {
        "txt": txt_name,
        "srt": srt_name,
        "vtt": vtt_name,
        "json": json_name,
    }


def process_video(
    input_file: Path,
    output_dir: Path,
    task_id: str,
    source_lang: Optional[str],
    target_langs: List[str],
    whisper_model: str,
    beam_size: int,
    compute_type: str,
    max_translation_chars: int,
    burn_subtitles: bool,
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
        message="Inicializando tarea de vídeo",
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

    clean_targets: List[str] = []
    for lang in target_langs:
        normalized = normalize_lang_code(lang)
        if normalized in ALLOWED_TARGETS and normalized not in clean_targets:
            clean_targets.append(normalized)

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=15,
        stage="transcription",
        message="Transcribiendo vídeo",
    )

    segments, info = transcribe_video(
        input_file=input_file,
        model_name=whisper_model,
        beam_size=beam_size,
        compute_type=compute_type,
        source_lang=manual_source_lang,
        logger=logger,
    )

    if not segments:
        raise RuntimeError(
            "No se generaron segmentos útiles. Prueba con un modelo Whisper más grande o forzando el idioma origen."
        )

    detected_lang = normalize_lang_code(info.get("language"))
    used_source_lang = manual_source_lang or detected_lang

    if not used_source_lang:
        logger.warning("No se pudo detectar idioma. Se asumirá 'es' para traducción.")
        used_source_lang = "es"

    logger.info("Idioma detectado/usado: %s", used_source_lang)
    logger.info("Segmentos descartados por limpieza: %s", info.get("removed_segments", 0))

    original_outputs = write_variant_files(
        output_dir=output_dir,
        stem=stem,
        variant="original",
        input_file=input_file,
        source_lang_requested=manual_source_lang,
        source_lang_detected=detected_lang,
        source_lang_used=used_source_lang,
        whisper_info=info,
        segments=segments,
    )

    logger.info("Transcripción original generada.")

    translated_outputs: Dict[str, Dict[str, str]] = {}
    burned_outputs: Dict[str, str] = {}

    translator: Optional[NllbTranslator] = None
    if clean_targets and used_source_lang in NLLB_LANG_MAP:
        write_status(
            output_dir,
            task_id=task_id,
            state="processing",
            progress=55,
            stage="translation",
            message="Traduciendo transcripción de vídeo",
            extra={"source_language_used": used_source_lang},
        )
        translator = NllbTranslator(model_name=DEFAULT_TRANSLATION_MODEL)
    elif clean_targets:
        logger.warning(
            "Idioma origen %s no soportado por el traductor NLLB configurado. Se omiten traducciones.",
            used_source_lang,
        )

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
        elif translator is None:
            logger.warning("No hay traductor disponible. Se omite %s.", tgt_lang)
            continue
        else:
            translated_segments = translate_segments(
                segments=segments,
                translator=translator,
                src_lang=used_source_lang,
                tgt_lang=tgt_lang,
                max_chars=max_translation_chars,
                logger=logger,
            )

        translated_outputs[tgt_lang] = write_variant_files(
            output_dir=output_dir,
            stem=stem,
            variant=tgt_lang,
            input_file=input_file,
            source_lang_requested=manual_source_lang,
            source_lang_detected=detected_lang,
            source_lang_used=used_source_lang,
            whisper_info=info,
            segments=translated_segments,
            target_language=tgt_lang,
        )

        logger.info("Salida completada: %s", tgt_lang)

    if burn_subtitles:
        write_status(
            output_dir,
            task_id=task_id,
            state="processing",
            progress=85,
            stage="subtitle_render",
            message="Generando vídeos subtitulados",
        )

        if not is_video_file(input_file):
            logger.warning("Se solicitó incrustado de subtítulos pero el archivo no parece un vídeo: %s", input_file)
        else:
            variants_to_burn: List[Tuple[str, str]] = [("original", original_outputs["srt"])]
            variants_to_burn.extend((lang, files["srt"]) for lang, files in translated_outputs.items())

            for variant, srt_name in variants_to_burn:
                output_name = f"{stem}.{variant}.subtitled.mp4"
                logger.info("Creando vídeo subtitulado para variante: %s", variant)
                burn_subtitles_into_video(
                    input_video=input_file,
                    srt_file=output_dir / srt_name,
                    output_video=output_dir / output_name,
                )
                burned_outputs[variant] = output_name

    success_message = "Procesamiento de vídeo completado correctamente."

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
        "original": original_outputs,
        "translations": translated_outputs,
        "burned_videos": burned_outputs,
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
        return process_video(
            input_file=input_file,
            output_dir=output_dir,
            task_id=args.task_id,
            source_lang=args.source_lang,
            target_langs=args.translate_to,
            whisper_model=args.whisper_model,
            beam_size=args.beam_size,
            compute_type=args.compute_type,
            max_translation_chars=args.max_translation_chars,
            burn_subtitles=args.burn_subtitles,
        )
    except Exception as e:
        ensure_dir(output_dir)

        error_message = f"Error al procesar el vídeo: {e}"

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
