#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AIUDA - Subtitulado automático local de clases grabadas
-------------------------------------------------------
Script local para:
- Procesar vídeo o audio
- Transcribir con faster-whisper
- Generar:
    * .srt
    * .vtt
    * .txt
    * .json
- Opcionalmente incrustar subtítulos en un MP4 usando ffmpeg

Uso:
    python aiuda_local_subtitles.py input.mp4 -o output
    python aiuda_local_subtitles.py input.mp4 -o output --device cuda --compute-type float16
    python aiuda_local_subtitles.py input.mp4 -o output --device cpu --compute-type int8
    python aiuda_local_subtitles.py input.mp4 -o output --burn-subtitles

Dependencias:
    pip install faster-whisper
    Opcional para quemar subtítulos:
    - ffmpeg instalado en el sistema

Notas:
- faster-whisper usa PyAV para decodificación, así que la transcripción no necesita
  ffmpeg instalado externamente.
- Para incrustar subtítulos en el vídeo final sí se usa ffmpeg si se activa --burn-subtitles.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from faster_whisper import WhisperModel


VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"
}
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma"
}


@dataclass
class SegmentData:
    id: int
    start: float
    end: float
    text: str


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def ensure_input_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {path}")
    if not path.is_file():
        raise ValueError(f"La ruta de entrada no es un archivo: {path}")


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def seconds_to_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def seconds_to_vtt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def write_txt(transcript_text: str, output_path: Path) -> None:
    output_path.write_text(transcript_text.strip() + "\n", encoding="utf-8")


def write_json(data: Dict[str, Any], output_path: Path) -> None:
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def write_srt(segments: List[SegmentData], output_path: Path) -> None:
    lines: List[str] = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(
            f"{seconds_to_srt_time(seg.start)} --> {seconds_to_srt_time(seg.end)}"
        )
        lines.append(seg.text)
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_vtt(segments: List[SegmentData], output_path: Path) -> None:
    lines: List[str] = ["WEBVTT", ""]
    for seg in segments:
        lines.append(
            f"{seconds_to_vtt_time(seg.start)} --> {seconds_to_vtt_time(seg.end)}"
        )
        lines.append(seg.text)
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def burn_subtitles_into_video(
    input_video: Path,
    srt_file: Path,
    output_video: Path,
) -> None:
    if not ffmpeg_available():
        raise EnvironmentError(
            "No se encontró ffmpeg en el sistema. "
            "Instálalo o ejecuta el script sin --burn-subtitles."
        )

    safe_srt = str(srt_file).replace("\\", "\\\\").replace(":", "\\:")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-vf",
        f"subtitles={safe_srt}",
        "-c:a",
        "copy",
        str(output_video),
    ]
    subprocess.run(cmd, check=True)


def transcribe_file(
    input_path: Path,
    model_size: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
    language: Optional[str],
    task: str,
) -> Dict[str, Any]:
    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
    )

    segments_generator, info = model.transcribe(
        str(input_path),
        beam_size=beam_size,
        vad_filter=vad_filter,
        language=language,
        task=task,
    )

    segments: List[SegmentData] = []
    transcript_parts: List[str] = []

    for idx, segment in enumerate(segments_generator):
        text = clean_text(segment.text)
        if not text:
            continue
        seg = SegmentData(
            id=idx,
            start=float(segment.start),
            end=float(segment.end),
            text=text,
        )
        segments.append(seg)
        transcript_parts.append(text)

    transcript_text = " ".join(transcript_parts).strip()

    return {
        "detected_language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "segments": segments,
        "transcript_text": transcript_text,
    }


def build_json_payload(
    input_path: Path,
    model_size: str,
    device: str,
    compute_type: str,
    task: str,
    detected_language: Optional[str],
    language_probability: Optional[float],
    duration: Optional[float],
    segments: List[SegmentData],
) -> Dict[str, Any]:
    return {
        "input_file": str(input_path),
        "model": model_size,
        "device": device,
        "compute_type": compute_type,
        "task": task,
        "detected_language": detected_language,
        "language_probability": language_probability,
        "duration_seconds": duration,
        "segments": [asdict(seg) for seg in segments],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Subtitulado automático local para AIUDA usando faster-whisper."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Ruta al archivo de vídeo o audio."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="output_aiuda",
        help="Directorio de salida."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="small",
        help=(
            "Modelo Whisper a usar. Ejemplos: tiny, base, small, medium, "
            "large-v3, distil-large-v3, turbo"
        )
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda", "auto"],
        help="Dispositivo de inferencia."
    )
    parser.add_argument(
        "--compute-type",
        type=str,
        default="int8",
        help="Tipo de cómputo. Ejemplos: int8, int8_float16, float16, float32"
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size para la decodificación."
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Idioma forzado, por ejemplo: es, gl, en, pt. Si no se indica, se autodetecta."
    )
    parser.add_argument(
        "--task",
        type=str,
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Tarea Whisper: transcribe o translate."
    )
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Desactiva filtrado VAD."
    )
    parser.add_argument(
        "--burn-subtitles",
        action="store_true",
        help="Genera además un MP4 con subtítulos incrustados usando ffmpeg."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    ensure_input_exists(input_path)
    ensure_output_dir(output_dir)

    base_name = input_path.stem
    srt_path = output_dir / f"{base_name}.srt"
    vtt_path = output_dir / f"{base_name}.vtt"
    txt_path = output_dir / f"{base_name}.txt"
    json_path = output_dir / f"{base_name}.json"

    try:
        result = transcribe_file(
            input_path=input_path,
            model_size=args.model,
            device=args.device,
            compute_type=args.compute_type,
            beam_size=args.beam_size,
            vad_filter=not args.no_vad,
            language=args.language,
            task=args.task,
        )
    except Exception as e:
        print(f"[ERROR] Falló la transcripción: {e}", file=sys.stderr)
        return 1

    segments: List[SegmentData] = result["segments"]
    transcript_text: str = result["transcript_text"]
    detected_language: Optional[str] = result["detected_language"]
    language_probability: Optional[float] = result["language_probability"]
    duration: Optional[float] = result["duration"]

    if not segments:
        print("[AVISO] No se generaron segmentos de subtítulos.", file=sys.stderr)

    try:
        write_srt(segments, srt_path)
        write_vtt(segments, vtt_path)
        write_txt(transcript_text, txt_path)

        json_payload = build_json_payload(
            input_path=input_path,
            model_size=args.model,
            device=args.device,
            compute_type=args.compute_type,
            task=args.task,
            detected_language=detected_language,
            language_probability=language_probability,
            duration=duration,
            segments=segments,
        )
        write_json(json_payload, json_path)
    except Exception as e:
        print(f"[ERROR] Falló la escritura de salidas: {e}", file=sys.stderr)
        return 1

    print("Proceso completado correctamente.")
    print(f"Idioma detectado: {detected_language}")
    print(f"Probabilidad idioma: {language_probability}")
    print(f"SRT:  {srt_path}")
    print(f"VTT:  {vtt_path}")
    print(f"TXT:  {txt_path}")
    print(f"JSON: {json_path}")

    if args.burn_subtitles:
        if not is_video_file(input_path):
            print(
                "[AVISO] --burn-subtitles solo aplica a archivos de vídeo. "
                "Se omite esta fase."
            )
        else:
            subtitled_video_path = output_dir / f"{base_name}.subtitled.mp4"
            try:
                burn_subtitles_into_video(
                    input_video=input_path,
                    srt_file=srt_path,
                    output_video=subtitled_video_path,
                )
                print(f"MP4 subtitulado: {subtitled_video_path}")
            except Exception as e:
                print(
                    f"[ERROR] No se pudo incrustar subtítulos en el vídeo: {e}",
                    file=sys.stderr
                )
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
