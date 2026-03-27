#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional

# Forzar CPU y evitar problemas con CUDA en GPUs antiguas
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    OcrAutoOptions,
    EasyOcrOptions,
    RapidOcrOptions,
    TesseractOcrOptions,
    TesseractCliOcrOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from langdetect import DetectorFactory, detect_langs
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

DetectorFactory.seed = 0

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".md",
    ".markdown",
    ".adoc",
    ".asciidoc",
    ".tex",
    ".latex",
    ".html",
    ".xhtml",
    ".csv",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}

SUPPORTED_LANGS = {
    "es": "spa_Latn",
    "en": "eng_Latn",
    "pt": "por_Latn",
    "gl": "glg_Latn",
}

NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"
_TRANSLATION_BACKEND = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ALUDA - extracción y traducción local de documentos/presentaciones"
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Archivo o carpeta de entrada",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output_aluda_docs",
        help="Directorio de salida",
    )
    parser.add_argument(
        "--translate-to",
        type=str,
        default=None,
        help="Idiomas destino separados por comas, por ejemplo: en,pt,gl. "
             "Si no se indica, traduce automáticamente a los otros 3 idiomas soportados.",
    )
    parser.add_argument(
        "--source-lang",
        type=str,
        default=None,
        help="Idioma origen manual, por ejemplo: es, en, pt, gl. "
             "Si no se indica, se detecta automáticamente.",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Activa OCR para PDF escaneado",
    )
    parser.add_argument(
        "--ocr-engine",
        type=str,
        default="auto",
        choices=["auto", "easyocr", "rapidocr", "tesseract", "tesseract-cli"],
        help="Motor OCR a usar para PDF si activas --ocr",
    )
    parser.add_argument(
        "--ocr-lang",
        type=str,
        default="es",
        help="Idiomas OCR separados por comas, por ejemplo: es,en",
    )
    parser.add_argument(
        "--force-full-page-ocr",
        action="store_true",
        help="Fuerza OCR de página completa en PDF",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Si input_path es una carpeta, recorre subcarpetas",
    )
    return parser.parse_args()


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_lang_code(code: str) -> str:
    code = code.lower().strip()
    aliases = {
        "pt-br": "pt",
        "pt-pt": "pt",
        "gl-es": "gl",
    }
    return aliases.get(code, code)


def parse_target_langs(value: Optional[str]) -> Optional[List[str]]:
    if value is None:
        return None

    langs = [normalize_lang_code(x) for x in value.split(",") if x.strip()]
    langs = list(dict.fromkeys(langs))

    invalid = [x for x in langs if x not in SUPPORTED_LANGS]
    if invalid:
        raise ValueError(
            f"Idiomas destino no soportados: {invalid}. "
            f"Soportados: {sorted(SUPPORTED_LANGS.keys())}"
        )

    return langs


def looks_degenerate(text: str) -> bool:
    t = normalize_whitespace(text).lower()
    if not t:
        return False

    if "@@" in t:
        return True

    if "tajik" in t:
        return True

    if len(t) > 120 and t.count(" ") <= 2:
        return True

    words = re.findall(r"\w+", t, flags=re.UNICODE)
    if len(words) >= 12:
        unique_words = set(words)
        if len(unique_words) <= 3:
            return True

        counts = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1

        most_common = max(counts.values())
        if most_common >= max(5, int(len(words) * 0.45)):
            return True

    for size in range(3, min(30, len(t) // 8 + 1)):
        prefix = t[:size]
        if prefix and t.startswith(prefix * 10):
            return True

    if "mainstream" in t and t.count("mainstream") >= 5:
        return True

    return False


def split_sentences(text: str) -> List[str]:
    text = normalize_whitespace(text)
    if not text:
        return []

    parts = re.split(r"(?<=[\.\!\?\:\;])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else [text]


def split_by_words(text: str, max_words: int = 80) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= max_words:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


def iter_input_files(input_path: Path, recursive: bool) -> Iterable[Path]:
    if input_path.is_file():
        yield input_path
        return

    if not input_path.is_dir():
        raise FileNotFoundError(f"No existe el archivo o carpeta: {input_path}")

    pattern = "**/*" if recursive else "*"
    for p in sorted(input_path.glob(pattern)):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield p


def get_ocr_options(engine: str, langs: List[str]):
    if engine == "auto":
        opts = OcrAutoOptions()
    elif engine == "easyocr":
        opts = EasyOcrOptions()
    elif engine == "rapidocr":
        opts = RapidOcrOptions()
    elif engine == "tesseract":
        opts = TesseractOcrOptions()
    elif engine == "tesseract-cli":
        opts = TesseractCliOcrOptions()
    else:
        raise ValueError(f"Motor OCR no soportado: {engine}")

    if hasattr(opts, "lang"):
        opts.lang = langs

    return opts


def build_converter_for_file(
    file_path: Path,
    use_ocr: bool,
    ocr_engine: str,
    ocr_langs: List[str],
    force_full_page_ocr: bool,
) -> DocumentConverter:
    if file_path.suffix.lower() == ".pdf":
        pipeline_options = PdfPipelineOptions()

        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=4,
            device=AcceleratorDevice.CPU,
        )

        if use_ocr:
            pipeline_options.do_ocr = True

            if hasattr(pipeline_options, "force_full_page_ocr"):
                pipeline_options.force_full_page_ocr = force_full_page_ocr

            pipeline_options.ocr_options = get_ocr_options(ocr_engine, ocr_langs)

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )

    return DocumentConverter()


def get_translation_backend():
    global _TRANSLATION_BACKEND

    if _TRANSLATION_BACKEND is None:
        print(f"[INFO] Cargando modelo NLLB: {NLLB_MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL_NAME)
        model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_NAME)
        model.to("cpu")
        model.eval()
        _TRANSLATION_BACKEND = (tokenizer, model)

    return _TRANSLATION_BACKEND


def ensure_translation_available(from_code: str, to_code: str):
    if from_code == to_code:
        return

    if from_code not in SUPPORTED_LANGS:
        raise RuntimeError(f"Idioma origen no soportado: {from_code}")
    if to_code not in SUPPORTED_LANGS:
        raise RuntimeError(f"Idioma destino no soportado: {to_code}")

    get_translation_backend()


def translate_text(text: str, from_code: str, to_code: str) -> str:
    text = normalize_whitespace(text)
    if not text or from_code == to_code:
        return text

    ensure_translation_available(from_code, to_code)

    tokenizer, model = get_translation_backend()
    src_lang = SUPPORTED_LANGS[from_code]
    tgt_lang = SUPPORTED_LANGS[to_code]

    tokenizer.src_lang = src_lang
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    with torch.no_grad():
        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
            max_length=512,
            num_beams=4,
        )

    return tokenizer.batch_decode(
        translated_tokens,
        skip_special_tokens=True
    )[0]


def safe_translate_unit(text: str, from_code: str, to_code: str) -> str:
    text = normalize_whitespace(text)
    if not text or from_code == to_code:
        return text

    try:
        translated = translate_text(text, from_code, to_code)
        translated = normalize_whitespace(translated)

        if not translated:
            print(f"[TRAD][WARN] Traducción vacía. Se conserva original: {text[:120]!r}")
            return text

        if looks_degenerate(translated):
            print(f"[TRAD][WARN] Traducción degenerada. Se conserva original: {text[:120]!r}")
            return text

        return translated

    except Exception as e:
        print(f"[TRAD][ERROR] Falló la traducción de: {text[:120]!r}")
        print(f"[TRAD][ERROR] Motivo: {e}")
        return text


def safe_translate_paragraph(text: str, from_code: str, to_code: str) -> str:
    text = normalize_whitespace(text)
    if not text:
        return text

    if len(text) > 600:
        sentences = split_sentences(text)
        if not sentences:
            sentences = [text]

        translated_parts = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) > 600:
                pieces = split_by_words(sentence, max_words=80)
                translated_pieces = [
                    safe_translate_unit(piece, from_code, to_code) for piece in pieces
                ]
                translated_parts.append(" ".join(translated_pieces))
            else:
                translated_parts.append(safe_translate_unit(sentence, from_code, to_code))

        merged = normalize_whitespace(" ".join(translated_parts))

        if looks_degenerate(merged):
            print("[TRAD][WARN] Párrafo traducido degenerado. Se conserva original.")
            return text

        return merged

    translated = safe_translate_unit(text, from_code, to_code)

    if looks_degenerate(translated):
        print("[TRAD][WARN] Traducción degenerada en párrafo corto. Se conserva original.")
        return text

    return translated


def safe_translate_document(text: str, from_code: str, to_code: str) -> str:
    paragraphs = re.split(r"\n\s*\n", text)
    out = []

    total = len(paragraphs)
    for i, p in enumerate(paragraphs, start=1):
        p = p.strip()
        if not p:
            continue

        print(f"[TRAD] {from_code}->{to_code} | Párrafo {i}/{total} ({len(p)} chars)...")

        if looks_degenerate(p):
            print(f"[TRAD] Párrafo {i} ignorado por parecer degenerado.")
            out.append(p)
            continue

        out.append(safe_translate_paragraph(p, from_code, to_code))

    return "\n\n".join(out)


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and all(ch in "|:- " for ch in stripped)


def translate_markdown(md_text: str, from_code: str, to_code: str) -> str:
    lines = md_text.splitlines()
    out_lines: List[str] = []
    in_code_block = False

    patterns = [
        r"^(\s{0,3}#{1,6}\s+)(.*)$",
        r"^(\s*[-*+]\s+)(.*)$",
        r"^(\s*\d+[.)]\s+)(.*)$",
        r"^(\s*>\s+)(.*)$",
    ]

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            out_lines.append(line)
            continue

        if in_code_block or not line.strip():
            out_lines.append(line)
            continue

        if is_table_separator(line):
            out_lines.append(line)
            continue

        translated = None
        for pat in patterns:
            m = re.match(pat, line)
            if m:
                prefix, content = m.groups()
                content = content.strip()
                if content:
                    translated = prefix + safe_translate_paragraph(content, from_code, to_code)
                else:
                    translated = line
                break

        if translated is None:
            translated = safe_translate_paragraph(line, from_code, to_code)

        out_lines.append(translated)

    return "\n".join(out_lines)


def detect_source_language(text: str) -> str:
    sample = normalize_whitespace(text)
    if len(sample) < 20:
        raise RuntimeError("Texto demasiado corto para detectar idioma con fiabilidad.")

    sample = sample[:5000]

    try:
        candidates = detect_langs(sample)
    except Exception as e:
        raise RuntimeError(f"No se pudo detectar el idioma: {e}") from e

    for cand in candidates:
        code = normalize_lang_code(cand.lang)
        if code in SUPPORTED_LANGS:
            print(f"[INFO] Idioma detectado: {code} (score={cand.prob:.3f})")
            return code

    raise RuntimeError(
        f"No se pudo mapear el idioma detectado a uno soportado. "
        f"Soportados: {sorted(SUPPORTED_LANGS.keys())}"
    )


def resolve_source_language(
    source_lang_arg: Optional[str],
    original_txt: str,
    original_md: str,
) -> Optional[str]:
    if source_lang_arg:
        code = normalize_lang_code(source_lang_arg)
        if code not in SUPPORTED_LANGS:
            raise ValueError(
                f"Idioma origen no soportado: {code}. "
                f"Soportados: {sorted(SUPPORTED_LANGS.keys())}"
            )
        print(f"[INFO] Idioma origen fijado manualmente: {code}")
        return code

    detection_text = original_txt if len(original_txt) >= 50 else original_md
    if not detection_text.strip():
        return None

    return detect_source_language(detection_text)


def resolve_target_languages(
    source_lang: str,
    target_langs_arg: Optional[List[str]],
) -> List[str]:
    if target_langs_arg:
        targets = [x for x in target_langs_arg if x != source_lang]
    else:
        targets = [x for x in SUPPORTED_LANGS.keys() if x != source_lang]

    if not targets:
        raise RuntimeError("No quedan idiomas destino tras excluir el idioma origen.")

    return targets


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def process_one_file(
    file_path: Path,
    output_dir: Path,
    use_ocr: bool,
    ocr_engine: str,
    ocr_langs: List[str],
    force_full_page_ocr: bool,
    source_lang_arg: Optional[str],
    target_langs_arg: Optional[List[str]],
) -> None:
    converter = build_converter_for_file(
        file_path=file_path,
        use_ocr=use_ocr,
        ocr_engine=ocr_engine,
        ocr_langs=ocr_langs,
        force_full_page_ocr=force_full_page_ocr,
    )

    result = converter.convert(file_path)
    doc = result.document

    stem = file_path.stem
    safe_stem = re.sub(r"[^\w.\-]+", "_", stem)

    original_md = normalize_whitespace(doc.export_to_markdown())
    original_txt = normalize_whitespace(doc.export_to_text())
    original_json = doc.export_to_dict()

    write_text(output_dir / f"{safe_stem}.original.md", original_md)
    write_text(output_dir / f"{safe_stem}.original.txt", original_txt)
    write_json(output_dir / f"{safe_stem}.original.json", original_json)

    print(f"[OK] Extraído: {file_path.name}")

    source_lang = resolve_source_language(source_lang_arg, original_txt, original_md)
    if source_lang is None:
        print(f"[WARN] No se pudo detectar idioma en {file_path.name}. Se omite traducción.")
        return

    target_langs = resolve_target_languages(source_lang, target_langs_arg)

    for target_lang in target_langs:
        ensure_translation_available(source_lang, target_lang)

        translated_txt = normalize_whitespace(
            safe_translate_document(original_txt, source_lang, target_lang)
        )
        translated_md = translate_markdown(original_md, source_lang, target_lang)

        translated_payload = {
            "input_file": str(file_path),
            "source_language": source_lang,
            "target_language": target_lang,
            "translated_markdown": translated_md,
            "translated_text": translated_txt,
        }

        write_text(output_dir / f"{safe_stem}.{target_lang}.md", translated_md)
        write_text(output_dir / f"{safe_stem}.{target_lang}.txt", translated_txt)
        write_json(output_dir / f"{safe_stem}.{target_lang}.json", translated_payload)

        print(f"[OK] Traducido: {file_path.name} -> {target_lang}")


def main() -> int:
    args = parse_args()

    input_path = Path(args.input_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    ensure_output_dir(output_dir)

    if not input_path.exists():
        print(f"[ERROR] No existe la ruta: {input_path}", file=sys.stderr)
        return 1

    ocr_langs = [x.strip() for x in args.ocr_lang.split(",") if x.strip()]
    if not ocr_langs:
        ocr_langs = ["es"]

    try:
        target_langs_arg = parse_target_langs(args.translate_to)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    try:
        files = list(iter_input_files(input_path, recursive=args.recursive))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    if not files:
        print("[ERROR] No se encontraron archivos soportados.", file=sys.stderr)
        return 1

    errors = 0
    for file_path in files:
        try:
            process_one_file(
                file_path=file_path,
                output_dir=output_dir,
                use_ocr=args.ocr,
                ocr_engine=args.ocr_engine,
                ocr_langs=ocr_langs,
                force_full_page_ocr=args.force_full_page_ocr,
                source_lang_arg=args.source_lang,
                target_langs_arg=target_langs_arg,
            )
        except Exception as e:
            errors += 1
            print(f"[ERROR] {file_path.name}: {e}", file=sys.stderr)

    if errors:
        print(f"\nFinalizado con {errors} error(es).", file=sys.stderr)
        return 1

    print("\nProceso completado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())