#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
aluda_model_manager.py
----------------------
Carga Whisper y NLLB una sola vez al arrancar el backend y los mantiene
en memoria para todos los jobs siguientes.

Uso desde el backend:
    from aluda_model_manager import model_manager
    model_manager.load()                     # llamar en on_startup()
    whisper = model_manager.whisper_model    # instancia WhisperModel
    nllb    = model_manager.nllb_translator  # instancia NllbTranslator
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import threading
from typing import Optional

logger = logging.getLogger("aluda.models")

# ---------------------------------------------------------------------------
# Detección de dispositivo (misma lógica que en los pipelines)
# ---------------------------------------------------------------------------
_CPU_CORES = multiprocessing.cpu_count()
os.environ.setdefault("OMP_NUM_THREADS", str(_CPU_CORES))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _detect_device() -> tuple[str, str, int]:
    """Devuelve (device, compute_type, cpu_threads)."""
    import torch
    if torch.cuda.is_available():
        logger.info("GPU detectada: %s", torch.cuda.get_device_name(0))
        return "cuda", "float16", 0
    logger.info("Sin GPU — usando CPU con %d cores", _CPU_CORES)
    return "cpu", "int8", _CPU_CORES


# ---------------------------------------------------------------------------
# Constantes (mismas que en los pipelines)
# ---------------------------------------------------------------------------
DEFAULT_WHISPER_MODEL    = "small"
DEFAULT_TRANSLATION_MODEL = "facebook/nllb-200-distilled-600M"


# ---------------------------------------------------------------------------
# ModelManager
# ---------------------------------------------------------------------------
class ModelManager:
    """Singleton con ciclo de vida: load() una vez, luego usar los atributos."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded = False

        self.device: str = "cpu"
        self.compute_type: str = "int8"
        self.cpu_threads: int = _CPU_CORES

        self.whisper_model = None      # faster_whisper.WhisperModel
        self.nllb_translator = None    # scripts.NllbTranslator

    # ------------------------------------------------------------------
    def load(
        self,
        whisper_model_name: str = DEFAULT_WHISPER_MODEL,
        nllb_model_name: str = DEFAULT_TRANSLATION_MODEL,
    ) -> None:
        """Carga ambos modelos. Idempotente: segunda llamada es no-op."""
        with self._lock:
            if self._loaded:
                return
            self._load_internal(whisper_model_name, nllb_model_name)
            self._loaded = True

    def _load_internal(self, whisper_model_name: str, nllb_model_name: str) -> None:
        import torch
        from faster_whisper import WhisperModel
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.device, self.compute_type, self.cpu_threads = _detect_device()

        # ---- Whisper -------------------------------------------------------
        logger.info(
            "Cargando Whisper '%s' en %s (compute=%s, threads=%s)…",
            whisper_model_name, self.device.upper(), self.compute_type,
            self.cpu_threads or "n/a",
        )
        self.whisper_model = WhisperModel(
            whisper_model_name,
            device=self.device,
            compute_type=self.compute_type,
            cpu_threads=self.cpu_threads if self.device == "cpu" else 0,
        )
        logger.info("Whisper listo.")

        # ---- NLLB ----------------------------------------------------------
        logger.info("Cargando NLLB '%s' en %s…", nllb_model_name, self.device.upper())
        tokenizer = AutoTokenizer.from_pretrained(nllb_model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(nllb_model_name)
        model.to(self.device)
        model.eval()

        if self.device == "cpu":
            try:
                torch.set_num_threads(self.cpu_threads)
            except Exception:
                pass

        # Construimos un NllbTranslator "ligero" que reutiliza los objetos ya cargados
        self.nllb_translator = _PreloadedNllbTranslator(
            tokenizer=tokenizer,
            model=model,
            device=self.device,
        )
        logger.info("NLLB listo.")

    @property
    def loaded(self) -> bool:
        return self._loaded


# ---------------------------------------------------------------------------
# NllbTranslator que usa modelos ya cargados (no los carga de nuevo)
# ---------------------------------------------------------------------------
class _PreloadedNllbTranslator:
    """
    Misma interfaz que NllbTranslator en los pipelines, pero recibe los
    objetos tokenizer/model ya instanciados.
    """

    NLLB_LANG_MAP = {
        "es": "spa_Latn",
        "en": "eng_Latn",
        "pt": "por_Latn",
        "gl": "glg_Latn",
    }

    def __init__(self, tokenizer, model, device: str) -> None:
        import torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self._torch = torch

    def translate_text(self, text: str, src_code: str, tgt_code: str, max_chars: int = 800) -> str:
        import re

        def normalize(t: str) -> str:
            return re.sub(r"[ \t]+", " ", t).strip()

        text = normalize(text)
        if not text or src_code == tgt_code:
            return text

        src_nllb = self.NLLB_LANG_MAP.get(src_code)
        tgt_nllb = self.NLLB_LANG_MAP.get(tgt_code)

        if not src_nllb:
            raise ValueError(f"Idioma origen no soportado: {src_code}")
        if not tgt_nllb:
            raise ValueError(f"Idioma destino no soportado: {tgt_code}")

        # Dividir en chunks si el texto es largo
        chunks = self._split(text, max_chars)
        out_chunks: list[str] = []

        for chunk in chunks:
            self.tokenizer.src_lang = src_nllb
            inputs = self.tokenizer(chunk, return_tensors="pt", truncation=True, padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with self._torch.no_grad():
                generated = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt_nllb),
                    max_length=512,
                )
            translated = self.tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
            out_chunks.append(normalize(translated))

        return normalize("\n\n".join(out_chunks))

    @staticmethod
    def _split(text: str, max_chars: int) -> list[str]:
        if len(text) <= max_chars:
            return [text]
        import re
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: list[str] = []
        current = ""
        for sent in sentences:
            if current and len(current) + len(sent) + 1 > max_chars:
                chunks.append(current.strip())
                current = sent
            else:
                current = (current + " " + sent).strip() if current else sent
        if current:
            chunks.append(current.strip())
        return chunks or [text]


# ---------------------------------------------------------------------------
# Instancia global
# ---------------------------------------------------------------------------
model_manager = ModelManager()
