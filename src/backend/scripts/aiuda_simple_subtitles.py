#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from faster_whisper import WhisperModel


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def es_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def tiempo_srt(segundos: float) -> str:
    total_ms = int(round(segundos * 1000))
    horas = total_ms // 3600000
    total_ms %= 3600000
    minutos = total_ms // 60000
    total_ms %= 60000
    segundos = total_ms // 1000
    ms = total_ms % 1000
    return f"{horas:02d}:{minutos:02d}:{segundos:02d},{ms:03d}"


def escribir_srt(segmentos, ruta_srt: Path) -> None:
    with open(ruta_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segmentos, start=1):
            texto = seg.text.strip()
            if not texto:
                continue
            f.write(f"{i}\n")
            f.write(f"{tiempo_srt(seg.start)} --> {tiempo_srt(seg.end)}\n")
            f.write(f"{texto}\n\n")


def escribir_txt(segmentos, ruta_txt: Path) -> None:
    with open(ruta_txt, "w", encoding="utf-8") as f:
        for seg in segmentos:
            texto = seg.text.strip()
            if texto:
                f.write(texto + " ")


def ffmpeg_disponible() -> bool:
    return shutil.which("ffmpeg") is not None


def incrustar_subtitulos(video_entrada: Path, srt: Path, video_salida: Path) -> None:
    if not ffmpeg_disponible():
        raise RuntimeError("ffmpeg no está instalado o no está en el PATH")

    # Escapado básico para rutas
    srt_str = str(srt).replace("\\", "\\\\").replace(":", "\\:")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_entrada),
        "-vf",
        f"subtitles={srt_str}",
        "-c:a",
        "copy",
        str(video_salida),
    ]

    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Vídeo o audio de entrada")
    parser.add_argument("-o", "--output-dir", default="output_aiuda", help="Output directory")
    parser.add_argument("--model", default="small", help="Modelo: tiny, base, small, medium, large-v3, turbo...")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    parser.add_argument("--compute-type", default="int8", help="Ej: int8, float16, float32")
    parser.add_argument("--language", default=None, help="Ej: es, gl, en, pt")
    parser.add_argument("--burn-subtitles", action="store_true", help="Incrusta subtítulos en el vídeo")
    args = parser.parse_args()

    input_file = Path(args.input_file).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        print(f"Error: no existe {input_file}", file=sys.stderr)
        sys.exit(1)

    nombre = input_file.stem
    ruta_srt = output_dir / f"{nombre}.srt"
    ruta_txt = output_dir / f"{nombre}.txt"
    ruta_video_final = output_dir / f"{nombre}_subtitulado.mp4"

    print("Cargando modelo...")
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
    )

    print("Transcribiendo...")
    segmentos_generador, info = model.transcribe(
        str(input_file),
        language=args.language,
        vad_filter=True,
        task="transcribe",
    )

    segmentos = list(segmentos_generador)

    print(f"Idioma detectado: {info.language}")
    escribir_srt(segmentos, ruta_srt)
    escribir_txt(segmentos, ruta_txt)

    print(f"SRT guardado en: {ruta_srt}")
    print(f"TXT guardado en: {ruta_txt}")

    if args.burn_subtitles:
        if not es_video(input_file):
            print("El archivo de entrada no es un vídeo. No se puede incrustar subtítulos.", file=sys.stderr)
            sys.exit(1)

        print("Incrustando subtítulos en el vídeo...")
        incrustar_subtitulos(input_file, ruta_srt, ruta_video_final)
        print(f"Vídeo subtitulado guardado en: {ruta_video_final}")


if __name__ == "__main__":
    main()
