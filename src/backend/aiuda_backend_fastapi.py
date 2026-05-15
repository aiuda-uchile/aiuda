#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import json
import mimetypes
import os
import shutil
import smtplib
import subprocess
import threading
import time
import traceback
import uuid
from datetime import datetime
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent.parent
JOBS_DIR = PROJECT_DIR / "jobs"
UPLOADS_DIR = JOBS_DIR / "uploads"
TASKS_DB = JOBS_DIR / "tasks.json"
LOGS_DIR = PROJECT_DIR / "logs"

AUDIO_SCRIPT = BASE_DIR / "scripts" / "aiuda_audio_pipeline.py"
VIDEO_SCRIPT = BASE_DIR / "scripts" / "aiuda_video_pipeline.py"
DOCS_SCRIPT = BASE_DIR / "scripts" / "aiuda_docs_pipeline_compatible.py"

DEFAULT_AUDIO_TARGETS = ["es", "en", "pt", "gl"]
DEFAULT_VIDEO_TARGETS = ["es", "en", "pt", "gl"]
DEFAULT_DOC_TARGETS = ["es", "en", "pt", "gl"]

MAX_WORKERS = 1
PYTHON_BIN = "python"

SMTP_HOST = os.getenv("AIUDA_SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("AIUDA_SMTP_PORT", "587"))
SMTP_USER = os.getenv("AIUDA_SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("AIUDA_SMTP_PASSWORD", "").strip()
SMTP_FROM = os.getenv("AIUDA_SMTP_FROM", SMTP_USER).strip()
SMTP_SECURITY = os.getenv("AIUDA_SMTP_SECURITY", "tls").strip().lower()  # tls | ssl | none
MAX_EMAIL_ATTACH_MB = int(os.getenv("AIUDA_MAX_EMAIL_ATTACH_MB", "20"))

AIUDA_LOGO_PATH = Path(
    os.getenv("AIUDA_LOGO_PATH", str(BASE_DIR / "resources" / "mail" / "aiuda-logo.png"))
)
AIUDA_FOOTER_PATH = Path(
    os.getenv("AIUDA_FOOTER_PATH", str(BASE_DIR / "resources" / "mail" / "aiuda-footer.png"))
)

AIUDA_FOOTER_TEXTS = {
    "es": (
        "Aiuda forma parte del programa Labs UniversitarIA, una iniciativa interuniversitaria "
        "impulsada por la DIPyC-SEGIB junto con la Universidade da Coruña, la Universidad de Chile, "
        "la Universidad Tecnológica del Uruguay, la Universidad de Buenos Aires y la Universidade "
        "Federal do Rio de Janeiro, con el apoyo de AECID."
    ),
    "gl": (
        "Aiuda forma parte do programa Labs UniversitarIA, unha iniciativa interuniversitaria "
        "impulsada pola DIPyC-SEGIB xunto coa Universidade da Coruña, a Universidad de Chile, "
        "a Universidad Tecnológica del Uruguay, a Universidad de Buenos Aires e a Universidade "
        "Federal do Rio de Janeiro, co apoio da AECID."
    ),
    "pt": (
        "O Aiuda faz parte do programa Labs UniversitarIA, uma iniciativa interuniversitária "
        "impulsionada pela DIPyC-SEGIB em conjunto com a Universidade da Coruña, a Universidad de Chile, "
        "a Universidad Tecnológica del Uruguay, a Universidad de Buenos Aires e a Universidade "
        "Federal do Rio de Janeiro, com o apoio da AECID."
    ),
    "en": (
        "Aiuda is part of the Labs UniversitarIA programme, an inter-university initiative "
        "promoted by DIPyC-SEGIB together with Universidade da Coruña, Universidad de Chile, "
        "Universidad Tecnológica del Uruguay, Universidad de Buenos Aires and Universidade "
        "Federal do Rio de Janeiro, with the support of AECID."
    ),
}

MAIL_TRANSLATIONS = {
    "es": {
        "greeting": "Hola,",
        "intro_finished": "Tu solicitud en Aiuda ha finalizado correctamente.",
        "intro_error": "Tu solicitud en Aiuda ha finalizado con error.",
        "intro_other": "Tu solicitud en Aiuda ha cambiado de estado.",
        "status_finished": "completado",
        "status_error": "error",
        "summary_title": "Resumen del procesamiento",
        "field_resource": "Recurso",
        "field_type": "Tipo",
        "field_status": "Estado",
        "field_date": "Fecha de finalizacion",
        "field_source_lang": "Idioma detectado",
        "field_target_langs": "Idiomas de salida",
        "notes_title": "Indicaciones adicionales",
        "results_title": "Resultados generados",
        "results_default": "Los resultados ya estan disponibles para su descarga desde la plataforma.",
        "error_title": "Detalle del error",
        "access_text": "Puedes acceder ahora a los resultados desde la plataforma de Aiuda.",
        "task_id_label": "ID de la tarea:",
        "thanks": "Gracias por utilizar Aiuda.",
        "subject_finished": "Proceso completado",
        "subject_error": "Proceso con error",
        "subject_received": "Tarea recibida",
        "intro_received": "Hemos recibido tu archivo y lo procesaremos a la brevedad.",
        "received_note": "Te notificaremos cuando el procesamiento haya finalizado.",
    },
    "gl": {
        "greeting": "Ola,",
        "intro_finished": "A tua solicitude en Aiuda rematou correctamente.",
        "intro_error": "A tua solicitude en Aiuda rematou con erro.",
        "intro_other": "A tua solicitude en Aiuda cambiou de estado.",
        "status_finished": "completado",
        "status_error": "erro",
        "summary_title": "Resumo do procesamento",
        "field_resource": "Recurso",
        "field_type": "Tipo",
        "field_status": "Estado",
        "field_date": "Data de finalizacion",
        "field_source_lang": "Idioma detectado",
        "field_target_langs": "Idiomas de saida",
        "notes_title": "Indicacions adicionais",
        "results_title": "Resultados xerados",
        "results_default": "Os resultados xa estan dispoñibles para a sua descarga desde a plataforma.",
        "error_title": "Detalle do erro",
        "access_text": "Podes acceder agora aos resultados desde a plataforma de Aiuda.",
        "task_id_label": "ID da tarefa:",
        "thanks": "Grazas por utilizar Aiuda.",
        "subject_finished": "Proceso completado",
        "subject_error": "Proceso con erro",
        "subject_received": "Tarefa recibida",
        "intro_received": "Recibimos o teu ficheiro e procesaremolo en breve.",
        "received_note": "Notificaremoste cando o procesamento remate.",
    },
    "pt": {
        "greeting": "Ola,",
        "intro_finished": "O seu pedido no Aiuda foi concluido com sucesso.",
        "intro_error": "O seu pedido no Aiuda terminou com erro.",
        "intro_other": "O seu pedido no Aiuda mudou de estado.",
        "status_finished": "concluido",
        "status_error": "erro",
        "summary_title": "Resumo do processamento",
        "field_resource": "Recurso",
        "field_type": "Tipo",
        "field_status": "Estado",
        "field_date": "Data de conclusao",
        "field_source_lang": "Idioma detetado",
        "field_target_langs": "Idiomas de saida",
        "notes_title": "Indicacoes adicionais",
        "results_title": "Resultados gerados",
        "results_default": "Os resultados ja estao disponiveis para transferencia a partir da plataforma.",
        "error_title": "Detalhe do erro",
        "access_text": "Pode aceder agora aos resultados a partir da plataforma Aiuda.",
        "task_id_label": "ID da tarefa:",
        "thanks": "Obrigado por utilizar o Aiuda.",
        "subject_finished": "Processo concluido",
        "subject_error": "Processo com erro",
        "subject_received": "Tarefa recebida",
        "intro_received": "Recebemos o seu ficheiro e iremos processá-lo em breve.",
        "received_note": "Notificaremos quando o processamento terminar.",
    },
    "en": {
        "greeting": "Hello,",
        "intro_finished": "Your Aiuda request has completed successfully.",
        "intro_error": "Your Aiuda request has finished with an error.",
        "intro_other": "Your Aiuda request has changed status.",
        "status_finished": "completed",
        "status_error": "error",
        "summary_title": "Processing summary",
        "field_resource": "Resource",
        "field_type": "Type",
        "field_status": "Status",
        "field_date": "Completion date",
        "field_source_lang": "Detected language",
        "field_target_langs": "Output languages",
        "notes_title": "Additional instructions",
        "results_title": "Generated results",
        "results_default": "The results are now available for download from the platform.",
        "error_title": "Error detail",
        "access_text": "You can now access the results from the Aiuda platform.",
        "task_id_label": "Task ID:",
        "thanks": "Thank you for using Aiuda.",
        "subject_finished": "Process completed",
        "subject_error": "Process with error",
        "subject_received": "Task received",
        "intro_received": "We have received your file and will process it shortly.",
        "received_note": "We will notify you when processing is complete.",
    },
}

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "4")


# =========================================================
# APP
# =========================================================

app = FastAPI(title="AIUDA Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STATE
# =========================================================

TASKS_LOCK = threading.Lock()
TASKS: Dict[str, Dict[str, Any]] = {}
TASK_QUEUE: "Queue[str]" = Queue()
WORKER_STARTED = False


# =========================================================
# MODELS
# =========================================================

class TaskListResponse(BaseModel):
    tasks: List[Dict[str, Any]]


# =========================================================
# HELPERS
# =========================================================

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ensure_dirs() -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_DB.exists():
        TASKS_DB.write_text("{}", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_tasks() -> None:
    global TASKS
    data = read_json(TASKS_DB, {})
    if isinstance(data, dict):
        TASKS = data
    else:
        TASKS = {}


def persist_tasks() -> None:
    with TASKS_LOCK:
        write_json(TASKS_DB, TASKS)


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "si", "sí"}


def parse_target_langs(raw: Optional[str], default_langs: List[str]) -> List[str]:
    if raw is None or not str(raw).strip():
        return default_langs

    raw = str(raw).strip()

    if raw.startswith("["):
        try:
            arr = json.loads(raw)
            if isinstance(arr, list):
                return [str(x).strip().lower() for x in arr if str(x).strip()]
        except Exception:
            pass

    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def safe_filename(name: str) -> str:
    keep = []
    for ch in name:
        if ch.isalnum() or ch in {".", "_", "-"}:
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def get_task(task_id: str) -> Dict[str, Any]:
    with TASKS_LOCK:
        task = TASKS.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        return dict(task)


def update_task(task_id: str, **fields: Any) -> Dict[str, Any]:
    with TASKS_LOCK:
        if task_id not in TASKS:
            raise KeyError(f"Tarea no encontrada: {task_id}")
        TASKS[task_id].update(fields)
        task = dict(TASKS[task_id])
    persist_tasks()
    return task


def list_task_outputs(output_dir: Path) -> List[str]:
    if not output_dir.exists():
        return []
    return sorted([p.name for p in output_dir.iterdir() if p.is_file()])


def guess_mime_type(path: Path) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or "/" not in mime_type:
        return "application", "octet-stream"
    maintype, subtype = mime_type.split("/", 1)
    return maintype, subtype


LANGUAGE_LABELS_I18N = {
    "es": {
        "auto": "automático",
        "es": "español",
        "en": "inglés",
        "pt": "portugués",
        "gl": "gallego",
        "fr": "francés",
        "it": "italiano",
        "de": "alemán",
        "ca": "catalán",
        "eu": "euskera",
    },
    "gl": {
        "auto": "automatico",
        "es": "español",
        "en": "inglés",
        "pt": "portugués",
        "gl": "galego",
        "fr": "francés",
        "it": "italiano",
        "de": "alemán",
        "ca": "catalán",
        "eu": "éuscaro",
    },
    "pt": {
        "auto": "automático",
        "es": "espanhol",
        "en": "inglês",
        "pt": "português",
        "gl": "galego",
        "fr": "francês",
        "it": "italiano",
        "de": "alemão",
        "ca": "catalão",
        "eu": "euskera",
    },
    "en": {
        "auto": "automatic",
        "es": "Spanish",
        "en": "English",
        "pt": "Portuguese",
        "gl": "Galician",
        "fr": "French",
        "it": "Italian",
        "de": "German",
        "ca": "Catalan",
        "eu": "Basque",
    },
}

TASK_TYPE_LABELS_I18N = {
    "es": {
        "audio": "audio",
        "video": "vídeo",
        "documents": "documento",
        "pdf": "documento PDF",
        "ppt": "presentación PPT",
        "pptx": "presentación PPT",
    },
    "gl": {
        "audio": "audio",
        "video": "vídeo",
        "documents": "documento",
        "pdf": "documento PDF",
        "ppt": "presentación PPT",
        "pptx": "presentación PPT",
    },
    "pt": {
        "audio": "audio",
        "video": "video",
        "documents": "documento",
        "pdf": "documento PDF",
        "ppt": "apresentação PPT",
        "pptx": "apresentação PPT",
    },
    "en": {
        "audio": "audio",
        "video": "video",
        "documents": "document",
        "pdf": "PDF document",
        "ppt": "PPT presentation",
        "pptx": "PPT presentation",
    },
}

VIDEO_UPLOAD_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def infer_task_type_from_upload(task_type: str, filename: str, content_type: str) -> str:
    task_type = (task_type or "").strip().lower()
    filename = (filename or "").strip().lower()
    content_type = (content_type or "").strip().lower()
    suffix = Path(filename).suffix.lower()

    if task_type == "documents":
        return "documents"

    if content_type.startswith("video/") or suffix in VIDEO_UPLOAD_EXTENSIONS:
        return "video"

    return task_type or "audio"


def friendly_language(code: str, ui_lang: str = "es") -> str:
    if not code:
        return "-"
    labels = LANGUAGE_LABELS_I18N.get(ui_lang, LANGUAGE_LABELS_I18N["es"])
    return labels.get(code.lower(), code)


def friendly_task_type(task_type: str, ui_lang: str = "es") -> str:
    if not task_type:
        return {
            "es": "recurso",
            "gl": "recurso",
            "pt": "recurso",
            "en": "resource",
        }.get(ui_lang, "recurso")
    labels = TASK_TYPE_LABELS_I18N.get(ui_lang, TASK_TYPE_LABELS_I18N["es"])
    return labels.get(task_type.lower(), task_type)


def get_footer_text(ui_lang: str = "es") -> str:
    return AIUDA_FOOTER_TEXTS.get(ui_lang, AIUDA_FOOTER_TEXTS["es"])


def format_finished_at(value: str) -> str:
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return value


def format_languages_list(codes: List[str], ui_lang: str = "es") -> str:
    if not codes:
        return "-"

    names = [friendly_language(code, ui_lang) for code in codes if code]
    if not names:
        return "-"
    if len(names) == 1:
        return names[0]

    join_word = {
        "es": "y",
        "gl": "e",
        "pt": "e",
        "en": "and",
    }.get(ui_lang, "y")

    if len(names) == 2:
        return f"{names[0]} {join_word} {names[1]}"
    return f"{', '.join(names[:-1])} {join_word} {names[-1]}"


def infer_generated_results(task: Dict[str, Any], output_files: List[str]) -> List[str]:
    results: List[str] = []
    task_type = (task.get("task_type") or "").lower()
    ui_lang = task.get("ui_lang", "es")

    labels = {
        "es": {
            "transcription": "Transcripción",
            "subtitles": "Subtítulos",
            "multi_files": "Archivos en varios formatos para descarga",
            "accessibility": "Informe de accesibilidad",
            "ocr": "Procesamiento OCR",
            "download_files": "Archivos de resultado para descarga",
        },
        "gl": {
            "transcription": "Transcrición",
            "subtitles": "Subtítulos",
            "multi_files": "Arquivos en varios formatos para descarga",
            "accessibility": "Informe de accesibilidade",
            "ocr": "Procesamento OCR",
            "download_files": "Arquivos de resultado para descarga",
        },
        "pt": {
            "transcription": "Transcrição",
            "subtitles": "Legendas",
            "multi_files": "Arquivos em vários formatos para transferência",
            "accessibility": "Relatório de acessibilidade",
            "ocr": "Processamento OCR",
            "download_files": "Arquivos de resultado para transferência",
        },
        "en": {
            "transcription": "Transcription",
            "subtitles": "Subtitles",
            "multi_files": "Files in multiple formats available for download",
            "accessibility": "Accessibility report",
            "ocr": "OCR processing",
            "download_files": "Result files available for download",
        },
    }.get(ui_lang, {
        "transcription": "Transcripción",
        "subtitles": "Subtítulos",
        "multi_files": "Archivos en varios formatos para descarga",
        "accessibility": "Informe de accesibilidad",
        "ocr": "Procesamiento OCR",
        "download_files": "Archivos de resultado para descarga",
    })

    has_txt = any(name.endswith(".txt") for name in output_files)
    has_srt = any(name.endswith(".srt") for name in output_files)
    has_vtt = any(name.endswith(".vtt") for name in output_files)
    has_json = any(name.endswith(".json") for name in output_files)

    if task_type in {"audio", "video"}:
        if has_txt:
            results.append(labels["transcription"])
        if has_srt or has_vtt:
            results.append(labels["subtitles"])
        if has_txt or has_srt or has_vtt or has_json:
            results.append(labels["multi_files"])
    elif task_type in {"pdf", "ppt", "pptx", "documents"}:
        if normalize_bool(task.get("accessibility", False)):
            results.append(labels["accessibility"])
        if normalize_bool(task.get("ocr", False)):
            results.append(labels["ocr"])
        if not results and output_files:
            results.append(labels["download_files"])
    elif output_files:
        results.append(labels["download_files"])

    return results


def read_inline_image_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def get_embedded_logo_bytes() -> bytes:
    return read_inline_image_bytes(AIUDA_LOGO_PATH)


def get_footer_image_bytes() -> bytes:
    return read_inline_image_bytes(AIUDA_FOOTER_PATH)


def build_report_html(
    task: Dict[str, Any],
    output_files: List[str],
    logo_cid: Optional[str] = None,
    footer_cid: Optional[str] = None,
) -> str:
    status = task.get("status", "")
    lang = task.get("ui_lang", "es")
    tr = MAIL_TRANSLATIONS.get(lang, MAIL_TRANSLATIONS["es"])

    if status == "finished":
        intro = tr["intro_finished"]
        status_label = tr["status_finished"]
    elif status == "error":
        intro = tr["intro_error"]
        status_label = tr["status_error"]
    else:
        intro = tr["intro_other"]
        status_label = status or "-"

    summary_fields = [
        (tr["field_resource"], str(task.get("input_filename", "-"))),
        (tr["field_type"], friendly_task_type(task.get("task_type", ""), lang)),
        (tr["field_status"], status_label),
        (tr["field_date"], format_finished_at(task.get("finished_at", ""))),
    ]

    if task.get("task_type", "").lower() in {"audio", "video"}:
        summary_fields.append((tr["field_source_lang"], friendly_language(task.get("source_lang", ""), lang)))
        if normalize_bool(task.get("translate", False)):
            summary_fields.append((tr["field_target_langs"], format_languages_list(task.get("target_langs", []) or [], lang)))

    summary_items = "".join(
        f'<tr><td style="padding:8px 0;color:#425466;font-size:14px;vertical-align:top;width:210px;"><strong>{escape(label)}</strong></td><td style="padding:8px 0;color:#12263A;font-size:14px;">{escape(value)}</td></tr>'
        for label, value in summary_fields
    )

    notes = str(task.get("notes", "")).strip()

    notes_block = ""
    if notes:
        notes_block = f"""
        <tr>
        <td style="padding:18px 32px 10px 32px;">
            <div style="font-size:18px;font-weight:700;color:#12263A;margin-bottom:12px;">
            {escape(tr["notes_title"])}
            </div>
            <div style="padding:16px 18px;background:#F8FAFC;border:1px solid #DCE6EE;border-radius:12px;font-size:14px;line-height:1.7;color:#12263A;white-space:pre-wrap;">
            {escape(notes)}
            </div>
        </td>
        </tr>
        """

    generated_results = infer_generated_results(task, output_files)
    if generated_results:
        results_html = "".join(
            f'<li style="margin:0 0 8px 0;">{escape(item)}</li>' for item in generated_results
        )
    else:
        results_html = f'<li style="margin:0 0 8px 0;">{escape(tr["results_default"])}</li>'

    error_block = ""
    if status == "error":
        error_message = escape(str(task.get("message", {"es": "Se produjo un error durante el procesamiento.", "gl": "Produciuse un erro durante o procesamento.", "pt": "Ocorreu um erro durante o processamento.", "en": "An error occurred during processing."}.get(lang, "Se produjo un error durante el procesamiento."))))
        error_block = f"""
        <div style="margin-top:24px;padding:16px 18px;background:#FFF4F2;border:1px solid #FFD5CC;border-radius:12px;">
          <div style="font-size:15px;font-weight:700;color:#9F3A22;margin-bottom:8px;">{escape(tr["error_title"])}</div>
          <div style="font-size:14px;color:#6B2C1A;line-height:1.6;">{error_message}</div>
        </div>
        """

    logo_html = ""
    if logo_cid:
        logo_html = f'<img src="cid:{escape(logo_cid)}" alt="Aiuda" style="display:block;height:52px;width:auto;border:0;">'

    footer_image_html = ""
    if footer_cid:
        footer_image_html = (
            f'<div style="margin-top:12px;text-align:center;">'
            f'<img src="cid:{escape(footer_cid)}" alt="Labs UniversitarIA y entidades colaboradoras" '
            f'style="display:block;max-width:100%;height:auto;margin:0 auto;border:0;">'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="{escape(lang)}">
  <body style="margin:0;padding:0;background:#F4F7FA;font-family:Arial,Helvetica,sans-serif;color:#12263A;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(intro)}</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F7FA;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:720px;background:#FFFFFF;border-radius:18px;overflow:hidden;border:1px solid #DCE6EE;box-shadow:0 4px 18px rgba(18,38,58,0.06);">
            <tr>
              <td style="padding:22px 32px 8px 32px;background:#FFFFFF;">{logo_html}</td>
            </tr>
            <tr>
              <td style="padding:8px 32px 8px 32px;">
                <div style="font-size:15px;line-height:1.7;color:#425466;">{escape(tr["greeting"])}</div>
                <div style="font-size:24px;line-height:1.35;font-weight:700;color:#12263A;margin-top:10px;">{escape(intro)}</div>
              </td>
            </tr>
            <tr>
            <td style="padding:24px 32px 10px 32px;">
                <div style="font-size:18px;font-weight:700;color:#12263A;margin-bottom:12px;">{escape(tr["summary_title"])}</div>
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{summary_items}</table>
            </td>
            </tr>
            {notes_block}
            <tr>
            <td style="padding:18px 32px 10px 32px;">
                <div style="font-size:18px;font-weight:700;color:#12263A;margin-bottom:12px;">{escape(tr["results_title"])}</div>
                <ul style="padding-left:20px;margin:0;font-size:14px;line-height:1.7;color:#12263A;">{results_html}</ul>
                {error_block}
            </td>
            </tr>
            <tr>
              <td style="padding:22px 32px 0 32px;">

                <div style="padding:16px 18px;background:#EEF6F7;border:1px solid #D6EAEC;border-radius:12px;font-size:14px;line-height:1.7;color:#1F4D57;">
                  {escape(tr["access_text"])}
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 32px 0 32px;">
                <div style="font-size:14px;line-height:1.7;color:#425466;"><strong>{escape(tr["task_id_label"])}</strong> {escape(str(task.get("id", "-")))}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 18px 32px;">
                <div style="font-size:14px;line-height:1.7;color:#425466;">{escape(tr["thanks"])}</div>
              </td>
            </tr>
          </table>
          <div style="max-width:720px;padding:16px 12px 0 12px;font-size:12px;line-height:1.7;color:#6B7C93;text-align:center;">
            {escape(get_footer_text(lang))}
            {footer_image_html}
          </div>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

def build_report_text(
    task: Dict[str, Any],
    output_files: List[str],
    skipped_files: Optional[List[str]] = None,
) -> str:
    resource_name = task.get("input_filename", "-")
    task_type = friendly_task_type(task.get("task_type", ""), task.get("ui_lang", "es"))
    status = task.get("status", "")
    finished_at = format_finished_at(task.get("finished_at", ""))
    source_lang = friendly_language(task.get("source_lang", ""), task.get("ui_lang", "es"))
    target_langs = format_languages_list(task.get("target_langs", []) or [], task.get("ui_lang", "es"))
    task_id = task.get("id", "-")
    lang = task.get("ui_lang", "es")
    tr = MAIL_TRANSLATIONS.get(lang, MAIL_TRANSLATIONS["es"])

    if status == "finished":
        status_label = tr["status_finished"]
        intro = tr["intro_finished"]
    elif status == "error":
        status_label = tr["status_error"]
        intro = tr["intro_error"]
    else:
        status_label = status or "-"
        intro = tr["intro_other"]

    generated_results = infer_generated_results(task, output_files)

    lines = [
        tr["greeting"],
        "",
        intro,
        "",
        tr["summary_title"],
        f"- {tr['field_resource']} {resource_name}",
        f"- {tr['field_type']} {task_type}",
        f"- {tr['field_status']} {status_label}",
        f"- {tr['field_date']} {finished_at}",
    ]

    if task.get("task_type", "").lower() in {"audio", "video"}:
        lines.append(f"- {tr['field_source_lang']} {source_lang}")
        if normalize_bool(task.get("translate", False)):
            lines.append(f"- {tr['field_target_langs']} {target_langs}")

    notes = str(task.get("notes", "")).strip()
    if notes:
        lines.extend([
            "",
            tr["notes_title"],
            notes,
        ])

    lines.extend([
        "",
        tr["results_title"],
    ])

    if generated_results:
        for item in generated_results:
            lines.append(f"- {item}")
    else:
        lines.append(f"- {tr['results_default']}")

    lines.extend([
        "",
        tr["access_text"],
        "",
        f"{tr['task_id_label']} {task_id}",
    ])

    if status == "error":
        error_message = str(task.get("message", {"es": "Se produjo un error durante el procesamiento.", "gl": "Produciuse un erro durante o procesamento.", "pt": "Ocorreu um erro durante o processamento.", "en": "An error occurred during processing."}.get(lang, "Se produjo un error durante el procesamiento.")))
        lines.extend([
            "",
            tr["error_title"],
            f"- {error_message}",
        ])

    lines.extend([
        "",
        tr["thanks"],
        "",
        get_footer_text(lang),
    ])

    return "\n".join(lines)

def write_task_report_file(task_id: str) -> Path:
    task = get_task(task_id)
    output_dir = Path(task["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_files = list_task_outputs(output_dir)
    report_path = output_dir / "AIUDA_report.txt"
    report_text = build_report_text(task, output_files)
    report_path.write_text(report_text, encoding="utf-8")
    return report_path



def send_task_received_email(task_id: str) -> None:
    task = get_task(task_id)
    lang = task.get("ui_lang", "es")
    tr = MAIL_TRANSLATIONS.get(lang, MAIL_TRANSLATIONS["es"])
    notify_email = normalize_bool(task.get("notify_email", False))
    recipient = (task.get("email") or "").strip()
    if not notify_email or not recipient:
        return
    if not SMTP_HOST or not SMTP_FROM:
        return

    subject = f"Aiuda | {tr['subject_received']} | {task.get('input_filename', 'recurso')}"

    logo_cid = make_msgid(domain="aiuda.local")
    logo_ref = logo_cid[1:-1]
    footer_cid = make_msgid(domain="aiuda.local")
    footer_ref = footer_cid[1:-1]

    logo_html = f'<img src="cid:{escape(logo_ref)}" alt="Aiuda" style="display:block;height:52px;width:auto;border:0;">'
    footer_image_html = (
        f'<div style="margin-top:12px;text-align:center;">'
        f'<img src="cid:{escape(footer_ref)}" alt="Labs UniversitarIA y entidades colaboradoras" '
        f'style="display:block;max-width:100%;height:auto;margin:0 auto;border:0;">'
        f'</div>'
    )

    body_html = f"""<!DOCTYPE html>
<html lang="{escape(lang)}">
  <body style="margin:0;padding:0;background:#F4F7FA;font-family:Arial,Helvetica,sans-serif;color:#12263A;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(tr["intro_received"])}</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F7FA;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:720px;background:#FFFFFF;border-radius:18px;overflow:hidden;border:1px solid #DCE6EE;box-shadow:0 4px 18px rgba(18,38,58,0.06);">
            <tr>
              <td style="padding:22px 32px 8px 32px;background:#FFFFFF;">{logo_html}</td>
            </tr>
            <tr>
              <td style="padding:8px 32px 8px 32px;">
                <div style="font-size:15px;line-height:1.7;color:#425466;">{escape(tr["greeting"])}</div>
                <div style="font-size:24px;line-height:1.35;font-weight:700;color:#12263A;margin-top:10px;">{escape(tr["intro_received"])}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 10px 32px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding:8px 0;color:#425466;font-size:14px;vertical-align:top;width:210px;"><strong>{escape(tr["field_resource"])}</strong></td>
                    <td style="padding:8px 0;color:#12263A;font-size:14px;">{escape(str(task.get("input_filename", "-")))}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#425466;font-size:14px;vertical-align:top;width:210px;"><strong>{escape(tr["task_id_label"])}</strong></td>
                    <td style="padding:8px 0;color:#12263A;font-size:14px;"><code>{escape(str(task.get("id", "-")))}</code></td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:22px 32px 0 32px;">
                <div style="padding:16px 18px;background:#EEF6F7;border:1px solid #D6EAEC;border-radius:12px;font-size:14px;line-height:1.7;color:#1F4D57;">
                  {escape(tr["received_note"])}
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 18px 32px;">
                <div style="font-size:14px;line-height:1.7;color:#425466;">{escape(tr["thanks"])}</div>
              </td>
            </tr>
          </table>
          <div style="max-width:720px;padding:16px 12px 0 12px;font-size:12px;line-height:1.7;color:#6B7C93;text-align:center;">
            {escape(get_footer_text(lang))}
            {footer_image_html}
          </div>
        </td>
      </tr>
    </table>
  </body>
</html>"""

    body_text = (
        f"{tr['greeting']}\n\n"
        f"{tr['intro_received']}\n\n"
        f"{tr['field_resource']}: {task.get('input_filename', '-')}\n"
        f"{tr['task_id_label']} {task.get('id', '-')}\n\n"
        f"{tr['received_note']}\n\n"
        f"{tr['thanks']}"
    )

    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text)
    msg.add_alternative(body_html, subtype="html")
    try:
        msg.get_payload()[-1].add_related(
            get_embedded_logo_bytes(),
            maintype="image", subtype="png",
            cid=logo_cid, filename=AIUDA_LOGO_PATH.name, disposition="inline",
        )
        msg.get_payload()[-1].add_related(
            get_footer_image_bytes(),
            maintype="image", subtype="png",
            cid=footer_cid, filename=AIUDA_FOOTER_PATH.name, disposition="inline",
        )
    except Exception:
        pass
    try:
        if SMTP_SECURITY == "ssl":
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=60) as server:
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as server:
                server.ehlo()
                if SMTP_SECURITY == "tls":
                    server.starttls()
                    server.ehlo()
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
    except Exception:
        pass
def send_task_email(task_id: str) -> None:
    task = get_task(task_id)
    lang = task.get("ui_lang", "es")
    tr = MAIL_TRANSLATIONS.get(lang, MAIL_TRANSLATIONS["es"])

    notify_email = normalize_bool(task.get("notify_email", False))
    recipient = (task.get("email") or "").strip()

    if not notify_email or not recipient:
        update_task(
            task_id,
            notification_status="disabled",
            notification_error="",
            updated_at=now_iso(),
        )
        return

    if not SMTP_HOST or not SMTP_FROM:
        update_task(
            task_id,
            notification_status="error",
            notification_error="SMTP no configurado. Revisa AIUDA_SMTP_HOST / AIUDA_SMTP_FROM.",
            updated_at=now_iso(),
        )
        return

    output_dir = Path(task["output_dir"])
    report_path = write_task_report_file(task_id)
    output_files = list_task_outputs(output_dir)

    subject_status = (
        tr["subject_finished"]
        if task.get("status") == "finished"
        else tr["subject_error"]
    )
    subject = f"Aiuda | {subject_status} | {task.get('input_filename', 'recurso')}"

    body_text = build_report_text(task, output_files)
    logo_cid = make_msgid(domain="aiuda.local")
    logo_ref = logo_cid[1:-1]
    footer_cid = make_msgid(domain="aiuda.local")
    footer_ref = footer_cid[1:-1]
    body_html = build_report_html(task, output_files, logo_cid=logo_ref, footer_cid=footer_ref)

    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text)
    msg.add_alternative(body_html, subtype="html")

    try:
        msg.get_payload()[-1].add_related(
            get_embedded_logo_bytes(),
            maintype="image",
            subtype="png",
            cid=logo_cid,
            filename=AIUDA_LOGO_PATH.name,
            disposition="inline",
        )
        msg.get_payload()[-1].add_related(
            get_footer_image_bytes(),
            maintype="image",
            subtype="png",
            cid=footer_cid,
            filename=AIUDA_FOOTER_PATH.name,
            disposition="inline",
        )
    except Exception:
        pass

    try:
        if SMTP_SECURITY == "ssl":
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=60) as server:
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as server:
                server.ehlo()
                if SMTP_SECURITY == "tls":
                    server.starttls()
                    server.ehlo()
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

        update_task(
            task_id,
            notification_status="sent",
            notified_at=now_iso(),
            notification_error="",
            updated_at=now_iso(),
        )

    except Exception as e:
        update_task(
            task_id,
            notification_status="error",
            notification_error=str(e),
            updated_at=now_iso(),
        )

        try:
            with open(output_dir / "backend_runner.log", "a", encoding="utf-8") as log_file:
                log_file.write("\n\n===== EMAIL ERROR =====\n")
                log_file.write(traceback.format_exc())
                log_file.write("\n")
        except Exception:
            pass

def refresh_task_from_status(task_id: str) -> None:
    task = get_task(task_id)
    output_dir = Path(task["output_dir"])
    status_path = output_dir / "status.json"

    if not status_path.exists():
        return

    status = read_json(status_path, {})
    if not isinstance(status, dict):
        return

    mapped_state = status.get("state", task.get("status", "queued"))
    if mapped_state == "finished":
        mapped_state = "finished"
    elif mapped_state == "processing":
        mapped_state = "processing"
    elif mapped_state == "error":
        mapped_state = "error"
    elif mapped_state == "queued":
        mapped_state = "queued"

    update_task(
        task_id,
        status=mapped_state,
        progress=int(status.get("progress", task.get("progress", 0))),
        current_stage=status.get("current_stage", task.get("current_stage", "")),
        message=status.get("message", task.get("message", "")),
        outputs=status.get("outputs", list_task_outputs(output_dir)),
        updated_at=now_iso(),
    )


def build_audio_command(task: Dict[str, Any]) -> List[str]:
    if not AUDIO_SCRIPT.exists():
        raise RuntimeError(f"No existe el script de audio: {AUDIO_SCRIPT}")

    input_file = task["input_file"]
    output_dir = task["output_dir"]
    source_lang = task["source_lang"]
    target_langs = task["target_langs"] if task.get("translate", True) else []

    cmd = [
        PYTHON_BIN,
        str(AUDIO_SCRIPT),
        str(input_file),
        "-o",
        str(output_dir),
        "--task-id",
        task["id"],
    ]

    if source_lang and source_lang != "auto":
        cmd.extend(["--source-lang", source_lang])

    if target_langs:
        cmd.append("--translate-to")
        cmd.extend(target_langs)

    return cmd


def build_video_command(task: Dict[str, Any]) -> List[str]:
    if not VIDEO_SCRIPT.exists():
        raise RuntimeError(f"No existe el script de vídeo: {VIDEO_SCRIPT}")

    input_file = task["input_file"]
    output_dir = task["output_dir"]
    source_lang = task["source_lang"]
    target_langs = task["target_langs"] if task.get("translate", True) else []

    cmd = [
        PYTHON_BIN,
        str(VIDEO_SCRIPT),
        str(input_file),
        "-o",
        str(output_dir),
        "--task-id",
        task["id"],
        "--burn-subtitles",
    ]

    if source_lang and source_lang != "auto":
        cmd.extend(["--source-lang", source_lang])

    if target_langs:
        cmd.append("--translate-to")
        cmd.extend(target_langs)

    return cmd


def build_docs_commands(task: Dict[str, Any]) -> List[List[str]]:
    if not DOCS_SCRIPT.exists():
        raise RuntimeError(f"No existe el script de documentos: {DOCS_SCRIPT}")

    input_file = task["input_file"]
    output_dir = task["output_dir"]
    source_lang = task["source_lang"]
    target_langs = task["target_langs"] if task.get("translate", True) else []
    use_ocr = normalize_bool(task.get("ocr", False))

    commands: List[List[str]] = []

    base_cmd = [
        PYTHON_BIN,
        str(DOCS_SCRIPT),
        str(input_file),
        "-o",
        str(output_dir),
    ]

    if use_ocr:
        base_cmd.append("--ocr")

    if source_lang and source_lang != "auto":
        base_cmd.extend(["--source-lang", source_lang])
    if target_langs:
        base_cmd.append("--translate-to")
        base_cmd.extend(target_langs)
    commands.append(base_cmd)

    return commands
    return commands


def build_commands(task: Dict[str, Any]) -> List[List[str]]:
    task_type = task["task_type"]

    if task_type == "audio":
        return [build_audio_command(task)]

    if task_type == "video":
        return [build_video_command(task)]

    if task_type == "documents":
        return build_docs_commands(task)

    raise RuntimeError(f"Tipo de tarea no soportado: {task_type}")


def run_one_command(
    task_id: str,
    cmd: List[str],
    log_path: Path,
    global_log_path: Optional[Path] = None,
) -> int:
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n\n===== {now_iso()} =====\n")
        log_file.write("CMD: " + " ".join(cmd) + "\n\n")
        log_file.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=log_file,
            stderr=log_file,
            text=True,
            env=os.environ,
        )

        while proc.poll() is None:
            try:
                refresh_task_from_status(task_id)
            except Exception:
                pass
            time.sleep(1)

        rc = proc.wait()

    try:
        refresh_task_from_status(task_id)
    except Exception:
        pass

    if global_log_path is not None:
        try:
            global_log_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(log_path, global_log_path)
        except Exception:
            pass

    return rc


def task_worker() -> None:
    while True:
        task_id = TASK_QUEUE.get()

        try:
            task = get_task(task_id)
            output_dir = Path(task["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            log_path = output_dir / "backend_runner.log"
            global_log_path = LOGS_DIR / f"{task_id}.log"

            update_task(
                task_id,
                status="processing",
                progress=5,
                current_stage="queue",
                message="Tarea enviada al engine",
                started_at=now_iso(),
                updated_at=now_iso(),
            )

            commands = build_commands(task)
            total_cmds = len(commands)

            for i, cmd in enumerate(commands, start=1):
                update_task(
                    task_id,
                    status="processing",
                    progress=max(5, int((i - 1) / max(total_cmds, 1) * 100)),
                    current_stage=f"engine_step_{i}",
                    message=f"Ejecutando paso {i}/{total_cmds}",
                    updated_at=now_iso(),
                )

                rc = run_one_command(task_id, cmd, log_path, global_log_path)
                if rc != 0:
                    raise RuntimeError(f"El proceso devolvió código {rc}")

            output_files = list_task_outputs(output_dir)

            task = get_task(task_id)

            update_task(
                task_id,
                status="finished",
                progress=100,
                current_stage="done",
                message=task.get("message", "Tarea finalizada correctamente"),
                outputs=output_files,
                finished_at=now_iso(),
                updated_at=now_iso(),
            )

            write_task_report_file(task_id)
            update_task(
                task_id,
                outputs=list_task_outputs(output_dir),
                updated_at=now_iso(),
            )

            try:
                send_task_email(task_id)
            except Exception:
                pass

        except Exception as e:
            try:
                task = get_task(task_id)
                output_dir = Path(task["output_dir"])
                output_files = list_task_outputs(output_dir)
            except Exception:
                output_files = []

            task = get_task(task_id)

            update_task(
                task_id,
                status="error",
                progress=100,
                current_stage="failed",
                message=task.get("message") or f"Error en el procesamiento: {e}",
                outputs=output_files,
                finished_at=now_iso(),
                updated_at=now_iso(),
            )

            try:
                write_task_report_file(task_id)
                task = get_task(task_id)
                output_dir = Path(task["output_dir"])
                update_task(
                    task_id,
                    outputs=list_task_outputs(output_dir),
                    updated_at=now_iso(),
                )
            except Exception:
                pass

            try:
                send_task_email(task_id)
            except Exception:
                pass

        finally:
            TASK_QUEUE.task_done()


def requeue_pending_tasks() -> None:
    with TASKS_LOCK:
        pending_ids = [
            task_id
            for task_id, task in TASKS.items()
            if task.get("status") in {"queued", "processing"}
        ]

    for task_id in pending_ids:
        update_task(
            task_id,
            status="queued",
            progress=0,
            current_stage="queue",
            message="Tarea reencolada al arrancar el backend",
            updated_at=now_iso(),
        )
        TASK_QUEUE.put(task_id)


def start_worker_once() -> None:
    global WORKER_STARTED
    if WORKER_STARTED:
        return

    for _ in range(MAX_WORKERS):
        t = threading.Thread(target=task_worker, daemon=True)
        t.start()

    WORKER_STARTED = True


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def on_startup() -> None:
    ensure_dirs()
    load_tasks()
    start_worker_once()
    requeue_pending_tasks()


# =========================================================
# API
# =========================================================

@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "aiuda-backend", "time": now_iso()}


@app.get("/api/tasks", response_model=TaskListResponse)
def list_tasks() -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []

    with TASKS_LOCK:
        for _, task in TASKS.items():
            items.append(dict(task))

    for item in items:
        try:
            refresh_task_from_status(item["id"])
        except Exception:
            pass

    with TASKS_LOCK:
        items = [dict(v) for v in TASKS.values()]

    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"tasks": items}


@app.get("/api/tasks/{task_id}")
def get_task_detail(task_id: str) -> Dict[str, Any]:
    refresh_task_from_status(task_id)
    return get_task(task_id)


@app.get("/api/tasks/{task_id}/log", response_class=PlainTextResponse)
def get_task_log(task_id: str) -> str:
    task = get_task(task_id)
    log_path = Path(task["output_dir"]) / "backend_runner.log"

    if not log_path.exists():
        return ""

    return log_path.read_text(encoding="utf-8", errors="replace")


@app.post("/api/tasks")
async def create_task(
    file: UploadFile = File(...),
    task_type: str = Form(...),
    email: str = Form(""),
    notes: str = Form(""),
    notify_email: str = Form("false"),
    translate: str = Form("true"),
    accessibility: str = Form("false"),
    ocr: str = Form("false"),
    source_lang: str = Form("auto"),
    target_langs: str = Form(""),
    ui_lang: str = Form("es"),
) -> Dict[str, Any]:
    task_type = infer_task_type_from_upload(
        task_type=task_type,
        filename=file.filename or "",
        content_type=getattr(file, "content_type", "") or "",
    )
    if task_type not in {"audio", "video", "documents"}:
        raise HTTPException(status_code=400, detail="task_type debe ser audio, video o documents")

    task_id = uuid.uuid4().hex[:12]
    task_dir = JOBS_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    original_name = file.filename or "input.bin"
    safe_name = safe_filename(original_name)
    input_path = task_dir / safe_name

    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if task_type == "audio":
        targets = parse_target_langs(target_langs, DEFAULT_AUDIO_TARGETS)
    elif task_type == "video":
        targets = parse_target_langs(target_langs, DEFAULT_VIDEO_TARGETS)
    else:
        targets = parse_target_langs(target_langs, DEFAULT_DOC_TARGETS)

    task_data = {
        "id": task_id,
        "status": "queued",
        "progress": 0,
        "current_stage": "queue",
        "message": "Tarea en cola",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "task_type": task_type,
        "email": email.strip(),
        "notes": notes.strip(),
        "notify_email": normalize_bool(notify_email),
        "translate": normalize_bool(translate),
        "accessibility": normalize_bool(accessibility),
        "ocr": normalize_bool(ocr),
        "source_lang": (source_lang or "auto").strip().lower(),
        "target_langs": targets,
        "ui_lang": ui_lang if ui_lang in ("es", "gl", "pt", "en") else "es",
        "input_filename": safe_name,
        "input_file": str(input_path),
        "output_dir": str(task_dir),
        "outputs": [],
        "notification_status": "pending"
        if normalize_bool(notify_email) and email.strip()
        else "disabled",
        "notification_error": "",
        "notified_at": None,
    }

    with TASKS_LOCK:
        TASKS[task_id] = task_data
    persist_tasks()

    TASK_QUEUE.put(task_id)
    threading.Thread(target=send_task_received_email, args=(task_id,), daemon=True).start()

    return {
        "ok": True,
        "task": task_data,
    }


@app.get("/api/tasks/{task_id}/download/{filename}")
def download_task_file(task_id: str, filename: str):
    task = get_task(task_id)
    output_dir = Path(task["output_dir"]).resolve()
    file_path = (output_dir / filename).resolve()

    if not str(file_path).startswith(str(output_dir)):
        raise HTTPException(status_code=400, detail="Ruta no válida")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    mime_type, _ = mimetypes.guess_type(str(file_path))

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=mime_type or "application/octet-stream",
        content_disposition_type="inline",
    )


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str) -> Dict[str, Any]:
    task = get_task(task_id)
    output_dir = Path(task["output_dir"])

    with TASKS_LOCK:
        TASKS.pop(task_id, None)
    persist_tasks()

    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)

    return {"ok": True, "deleted": task_id}

@app.get("/api/debug/smtp")
def debug_smtp():
    return {
        "smtp_host": os.getenv("AIUDA_SMTP_HOST", ""),
        "smtp_port": os.getenv("AIUDA_SMTP_PORT", ""),
        "smtp_user": os.getenv("AIUDA_SMTP_USER", ""),
        "smtp_from": os.getenv("AIUDA_SMTP_FROM", ""),
        "smtp_security": os.getenv("AIUDA_SMTP_SECURITY", ""),
        "smtp_password_loaded": bool(os.getenv("AIUDA_SMTP_PASSWORD", "")),
        "smtp_password_len": len(os.getenv("AIUDA_SMTP_PASSWORD", "")),
    }