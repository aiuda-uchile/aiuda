#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import html
import io
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from statistics import median
import csv
from datetime import datetime

from collections import Counter

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

APP_NAME = "AIUDA Docs Pipeline"
ALLOWED_TARGETS = {"es", "en", "pt", "gl"}



MASTER_REPORT_TEXTS = {
    "es": {
        "report_title": "Informe de accesibilidad",
        "estimated_reading_time": "Tiempo estimado de lectura del material:",
        "intro": "En el análisis del documento identificamos oportunidades de mejora para ayudarte a crear materiales más claros y accesibles, considerando:",
        "intro_no_issues": "En el análisis del documento no fueron encontradas incidencias. El análisis de la presentación consideró:",

        "summary_blocks": [
            {
                "title": "Comprensión visual",
                "text": "Tamaño de letra, interlineado, tipografía, cantidad de texto, color y contraste.",
            },
            {
                "title": "Organización del contenido",
                "text": "Jerarquía visual y cantidad de elementos por diapositiva.",
            },
            {
                "title": "Uso de imágenes",
                "text": "Presencia de descripciones alternativas de accesibilidad (ALT).",
            },
        ],

        "sections": {
            "by_dimension_title": "Recomendaciones por dimensión",
            "by_dimension_intro": "Abajo se detallan las recomendaciones organizadas por dimensión, indicando junto con las diapositivas o páginas en que se sugiere verificar cada aspecto.",
            "by_slide_title": "Resumen por diapositivas",
            "by_slide_intro": "Abajo se presenta, para cada diapositiva, el conjunto de recomendaciones aplicables identificadas en el análisis.",
            "criteria_title": "Criterios y referencias utilizados",
            "criteria_intro": "Las recomendaciones de este informe se basan en estándares internacionales de accesibilidad y en modelos de análisis reconocidos.",
            "limitations_title": "Limitaciones de la estimación",
            "references_title": "Referencias",
        },

        "dimensions": {
            "visual": {
                "title": "Dimensión Comprensión visual",
                "summary": "Tamaño de letra, interlineado, tipografía y cantidad de texto.",
            },
            "organization": {
                "title": "Dimensión Organización del contenido",
                "summary": "Jerarquía visual, bloques de contenido y cantidad de elementos por diapositiva.",
            },
            "images": {
                "title": "Dimensión uso de imágenes",
                "summary": "Presencia de descripciones alternativas de accesibilidad.",
            },
        },

        "metrics": {
            "font_size": {
                "label": "Tamaño de letra",
                "recommendation": "Aumentar el tamaño de la letra manteniendo, como referencia, un tamaño mínimo de {min_font:.0f} pts.",
            },
            "typography": {
                "label": "Tipografía",
                "recommendation": "Priorizar tipografías sans serif consistentes, especialmente en títulos, cuerpo y etiquetas.",
            },
            "line_spacing": {
                "label": "Interlineado",
                "recommendation": "Aumentar el espacio entre líneas manteniendo, como referencia, un interlineado mínimo de {min_spacing:.2f} pt.",
            },
            "text_amount": {
                "label": "Cantidad de texto",
                "recommendation": "Reducir la cantidad de texto por diapositiva o página cuando supere la referencia de {max_words} palabras.",
            },
            "color": {
                "label": "Color",
                "recommendation": "Revisar el uso de colores en las diapositivas para asegurar que la información sea distinguible para personas con diferentes tipos de visión del color. Evitar combinaciones que puedan generar confusión (por ejemplo, rojo/verde) y reforzar la información con otros recursos como texto, íconos o subrayados.",
            },
            "contrast": {
                "label": "Contraste",
                "recommendation": "Mejorar el contraste entre el texto y el fondo para facilitar la lectura. En algunos casos, puede ser necesario ajustar los colores o reorganizar el contenido de la diapositiva.",
            },
            "visual_hierarchy": {
                "label": "Jerarquia visual",
                "recommendation": "Segmentar el contenido organizando cada diapositiva en, al menos, {min_blocks} bloques, cuando sea posible.",
            },
            "elements": {
                "label": "Cantidad de elementos",
                "recommendation": "Reducir la cantidad total de elementos por diapositiva manteniendo un máximo de {max_elements} elementos visibles.",
            },
            "alt_text": {
                "label": "Texto alternativo (ALT)",
                "recommendation": "Añadir texto alternativo a las imágenes relevantes para que puedan interpretarse con tecnologías de apoyo.",
            },
        },

        "common": {
            "recommendation": "Recomendación:",
            "slides_for_review": "Diapositivas para revisión",
            "pages_for_review": "Páginas para revisión",
            "no_slides_review": "No se detectaron diapositivas para revisión.",
            "slide": "Diapositiva",
            "page": "Página",
        },

        "criteria": {
            "visual_title": "Accesibilidad visual y contraste",
            "wcag_143_title": "W3C WCAG 2.1 — Criterio 1.4.3 (Contraste mínimo)",
            "wcag_143_detail": "Referencia: relación de contraste 4.5:1 para texto normal y 3:1 para texto grande.",
            "wcag_1411_title": "W3C WCAG 2.1 — Criterio 1.4.11 (Contraste no textual)",
            "wcag_1411_detail": "Referencia: relación mínima de 3:1 para elementos visuales relevantes.",
            "documents_title": "Aplicación a documentos",
            "wcag2ict_title": "WCAG2ICT — Aplicación de WCAG a documentos y software no web",
            "wcag2ict_detail": "Base para el análisis en presentaciones (PDF, PPT, PPTX).",
            "color_title": "Percepción del color",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Modelo de simulación de visión del color (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Modelo para simulación de deficiencias en la percepción del color.",
        },
    },

    "en": {
        "report_title": "Accessibility report",
        "estimated_reading_time": "Estimated reading time:",
        "intro": "The document analysis identified improvement opportunities to help create clearer and more accessible materials, considering:",
        "intro_no_issues": "No issues were found in the document analysis. The presentation analysis considered:",
        "summary_blocks": [
            {"title": "Visual comprehension", "text": "Font size, line spacing, typography, amount of text, color, and contrast."},
            {"title": "Content organization", "text": "Visual hierarchy and number of elements per slide."},
            {"title": "Use of images", "text": "Presence of alternative accessibility descriptions (ALT)."},
        ],
        "sections": {
            "by_dimension_title": "Recommendations by dimension",
            "by_dimension_intro": "Below are the recommendations organized by dimension, indicating the slides or pages where each aspect should be reviewed.",
            "by_slide_title": "Summary by slide",
            "by_slide_intro": "Below is the set of applicable recommendations identified for each slide.",
            "criteria_title": "Criteria and references used",
            "criteria_intro": "The recommendations in this report are based on international accessibility standards and recognized analysis models.",
            "limitations_title": "Estimation limitations",
            "references_title": "References",
        },
        "dimensions": {
            "visual": {"title": "Visual Comprehension Dimension", "summary": "Font size, line spacing, typography, and amount of text."},
            "organization": {"title": "Content Organization Dimension", "summary": "Visual hierarchy, content blocks, and number of elements per slide."},
            "images": {"title": "Images Dimension", "summary": "Presence of alternative accessibility descriptions."},
        },
        "metrics": {
            "font_size": {"label": "Font size", "recommendation": "Increase font size while keeping, as a reference, a minimum size of {min_font:.0f} pt."},
            "typography": {"label": "Typography", "recommendation": "Prioritize consistent sans serif typefaces, especially in titles, body text, and labels."},
            "line_spacing": {"label": "Line spacing", "recommendation": "Increase line spacing while keeping, as a reference, a minimum line spacing of {min_spacing:.2f} pt."},
            "text_amount": {"label": "Amount of text", "recommendation": "Reduce the amount of text per slide or page when it exceeds the reference of {max_words} words."},
            "color": {"label": "Color", "recommendation": "Review the use of colors in the slides to ensure the information is distinguishable for people with different types of color vision. Avoid combinations that may cause confusion, for example red and green, and reinforce the information with text, icons, or underlining."},
            "contrast": {"label": "Contrast", "recommendation": "Improve the contrast between text and background to facilitate reading. In some cases, it may be necessary to adjust the colors or reorganize the content of the slide."},
            "visual_hierarchy": {"label": "Visual hierarchy", "recommendation": "Segment the content by organizing each slide into at least {min_blocks} blocks whenever possible."},
            "elements": {"label": "Number of elements", "recommendation": "Reduce the total number of elements per slide while keeping a maximum of {max_elements} visible elements."},
            "alt_text": {"label": "Alternative text (ALT)", "recommendation": "Add alternative text to relevant images so they can be interpreted with assistive technologies."},
        },
        "common": {
            "recommendation": "Recommendation:",
            "slides_for_review": "Slides for review",
            "pages_for_review": "Pages for review",
            "no_slides_review": "No slides were identified for review.",
            "slide": "Slide",
            "page": "Page",
        },
        "criteria": {
            "visual_title": "Visual accessibility and contrast",
            "wcag_143_title": "W3C WCAG 2.1 — Criterion 1.4.3 (Minimum contrast)",
            "wcag_143_detail": "Reference: contrast ratio 4.5:1 for normal text and 3:1 for large text.",
            "wcag_1411_title": "W3C WCAG 2.1 — Criterion 1.4.11 (Non text contrast)",
            "wcag_1411_detail": "Reference: minimum 3:1 ratio for relevant visual elements.",
            "documents_title": "Application to documents",
            "wcag2ict_title": "WCAG2ICT — Applying WCAG to non web documents and software",
            "wcag2ict_detail": "Basis for analysis in presentations (PDF, PPT, PPTX).",
            "color_title": "Color perception",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Color vision simulation model (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Model for simulation of color vision deficiencies.",
        },
    },

    "pt": {
        "report_title": "Relatório de acessibilidade",
        "estimated_reading_time": "Tempo estimado de leitura do material:",
        "intro": "A análise do documento identificou oportunidades de melhoria para ajudar a criar materiais mais claros e acessíveis, considerando:",
"intro_no_issues": "Na análise do documento não foram encontradas incidências. A análise da apresentação considerou:",
        "summary_blocks": [
            {"title": "Compreensão visual", "text": "Tamanho da letra, espaçamento entre linhas, tipografia, quantidade de texto, cor e contraste."},
            {"title": "Organização do conteúdo", "text": "Hierarquia visual e quantidade de elementos por slide."},
            {"title": "Uso de imagens", "text": "Presença de descrições alternativas de acessibilidade (ALT)."},
        ],
        "sections": {
            "by_dimension_title": "Recomendações por dimensão",
            "by_dimension_intro": "Abaixo estão as recomendações organizadas por dimensão, indicando os slides ou páginas em que se sugere verificar cada aspecto.",
            "by_slide_title": "Resumo por slide",
            "by_slide_intro": "Abaixo apresenta-se, para cada slide, o conjunto de recomendações aplicáveis identificadas na análise.",
            "criteria_title": "Critérios e referências utilizados",
            "criteria_intro": "As recomendações deste relatório baseiam-se em normas internacionais de acessibilidade e em modelos de análise reconhecidos.",
            "limitations_title": "Limitações da estimativa",
            "references_title": "Referências",
        },
        "dimensions": {
            "visual": {"title": "Dimensão Compreensão visual", "summary": "Tamanho da letra, espaçamento entre linhas, tipografia e quantidade de texto."},
            "organization": {"title": "Dimensão Organização do conteúdo", "summary": "Hierarquia visual, blocos de conteúdo e quantidade de elementos por slide."},
            "images": {"title": "Dimensão uso de imagens", "summary": "Presença de descrições alternativas de acessibilidade."},
        },
        "metrics": {
            "font_size": {"label": "Tamanho da letra", "recommendation": "Aumentar o tamanho da letra mantendo, como referência, um tamanho mínimo de {min_font:.0f} pts."},
            "typography": {"label": "Tipografia", "recommendation": "Priorizar tipografias sans serif consistentes, especialmente em títulos, corpo e rótulos."},
            "line_spacing": {"label": "Espaçamento entre linhas", "recommendation": "Aumentar o espaço entre linhas mantendo, como referência, um espaçamento mínimo de {min_spacing:.2f} pt."},
            "text_amount": {"label": "Quantidade de texto", "recommendation": "Reduzir a quantidade de texto por slide ou página quando superar a referência de {max_words} palavras."},
            "color": {"label": "Cor", "recommendation": "Revisar o uso de cores nos slides para garantir que a informação seja distinguível para pessoas com diferentes tipos de visão de cores. Evitar combinações que possam gerar confusão, por exemplo vermelho e verde, e reforçar a informação com texto, ícones ou sublinhado."},
            "contrast": {"label": "Contraste", "recommendation": "Melhorar o contraste entre o texto e o fundo para facilitar a leitura. Em alguns casos, pode ser necessário ajustar as cores ou reorganizar o conteúdo do slide."},
            "visual_hierarchy": {"label": "Hierarquia visual", "recommendation": "Segmentar o conteúdo organizando cada slide em, pelo menos, {min_blocks} blocos, quando possível."},
            "elements": {"label": "Quantidade de elementos", "recommendation": "Reduzir a quantidade total de elementos por slide mantendo um máximo de {max_elements} elementos visíveis."},
            "alt_text": {"label": "Texto alternativo (ALT)", "recommendation": "Adicionar texto alternativo às imagens relevantes para que possam ser interpretadas com tecnologias assistivas."},
        },
        "common": {
            "recommendation": "Recomendação:",
            "slides_for_review": "Slides para revisão",
            "pages_for_review": "Páginas para revisão",
            "no_slides_review": "Nenhum slide foi identificado para revisão.",
            "slide": "Slide",
            "page": "Página",
        },
        "criteria": {
            "visual_title": "Acessibilidade visual e contraste",
            "wcag_143_title": "W3C WCAG 2.1 — Critério 1.4.3 (Contraste mínimo)",
            "wcag_143_detail": "Referência: relação de contraste 4.5:1 para texto normal e 3:1 para texto grande.",
            "wcag_1411_title": "W3C WCAG 2.1 — Critério 1.4.11 (Contraste não textual)",
            "wcag_1411_detail": "Referência: relação mínima de 3:1 para elementos visuais relevantes.",
            "documents_title": "Aplicação a documentos",
            "wcag2ict_title": "WCAG2ICT — Aplicação das WCAG a documentos e software não web",
            "wcag2ict_detail": "Base para a análise em apresentações (PDF, PPT, PPTX).",
            "color_title": "Percepção da cor",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Modelo de simulação da visão das cores (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Modelo para simulação de deficiências na visão de cores.",
        },
    },

    "gl": {
        "report_title": "Informe de accesibilidade",
        "estimated_reading_time": "Tempo estimado de lectura do material:",
        "intro": "Na análise do documento identificáronse oportunidades de mellora para crear materiais máis claros e accesibles, considerando:",
        "intro_no_issues": "Na análise do documento non foron encontradas incidencias. A análise da presentación considerou:",
        "summary_blocks": [
            {"title": "Comprensión visual", "text": "Tamaño da letra, interliñado, tipografía, cantidade de texto, cor e contraste."},
            {"title": "Organización do contido", "text": "Xerarquía visual e cantidade de elementos por diapositiva."},
            {"title": "Uso de imaxes", "text": "Presenza de descricións alternativas de accesibilidade (ALT)."},
        ],
        "sections": {
            "by_dimension_title": "Recomendacións por dimensión",
            "by_dimension_intro": "A continuación detállanse as recomendacións organizadas por dimensión, indicando as diapositivas ou páxinas nas que se suxire revisar cada aspecto.",
            "by_slide_title": "Resumo por diapositiva",
            "by_slide_intro": "A continuación preséntase, para cada diapositiva, o conxunto de recomendacións aplicables identificadas na análise.",
            "criteria_title": "Criterios e referencias utilizadas",
            "criteria_intro": "As recomendacións deste informe baséanse en estándares internacionais de accesibilidade e en modelos de análise recoñecidos.",
            "limitations_title": "Limitacións da estimación",
            "references_title": "Referencias",
        },
        "dimensions": {
            "visual": {"title": "Dimensión Comprensión visual", "summary": "Tamaño da letra, interliñado, tipografía e cantidade de texto."},
            "organization": {"title": "Dimensión Organización do contido", "summary": "Xerarquía visual, bloques de contido e cantidade de elementos por diapositiva."},
            "images": {"title": "Dimensión uso de imaxes", "summary": "Presenza de descricións alternativas de accesibilidade."},
        },
        "metrics": {
            "font_size": {"label": "Tamaño da letra", "recommendation": "Aumentar o tamaño da letra mantendo, como referencia, un tamaño mínimo de {min_font:.0f} pts."},
            "typography": {"label": "Tipografía", "recommendation": "Priorizar tipografías sans serif consistentes, especialmente en títulos, corpo e etiquetas."},
            "line_spacing": {"label": "Interliñado", "recommendation": "Aumentar o espazo entre liñas mantendo, como referencia, un interliñado mínimo de {min_spacing:.2f} pt."},
            "text_amount": {"label": "Cantidade de texto", "recommendation": "Reducir a cantidade de texto por diapositiva ou páxina cando supere a referencia de {max_words} palabras."},
            "color": {"label": "Cor", "recommendation": "Revisar o uso de cores nas diapositivas para asegurar que a información sexa distinguible para persoas con diferentes tipos de visión da cor. Evitar combinacións que poidan xerar confusión, por exemplo vermello e verde, e reforzar a información con texto, iconas ou subliñado."},
            "contrast": {"label": "Contraste", "recommendation": "Mellorar o contraste entre o texto e o fondo para facilitar a lectura. Nalgúns casos, pode ser necesario axustar as cores ou reorganizar o contido da diapositiva."},
            "visual_hierarchy": {"label": "Xerarquía visual", "recommendation": "Segmentar o contido organizando cada diapositiva en, polo menos, {min_blocks} bloques, cando sexa posible."},
            "elements": {"label": "Cantidade de elementos", "recommendation": "Reducir a cantidade total de elementos por diapositiva mantendo un máximo de {max_elements} elementos visibles."},
            "alt_text": {"label": "Texto alternativo (ALT)", "recommendation": "Engadir texto alternativo ás imaxes relevantes para que poidan interpretarse con tecnoloxías de apoio."},
        },
        "common": {
            "recommendation": "Recomendación:",
            "slides_for_review": "Diapositivas para revisión",
            "pages_for_review": "Páxinas para revisión",
            "no_slides_review": "Non se detectaron diapositivas para revisión.",
            "slide": "Diapositiva",
            "page": "Páxina",
        },
        "criteria": {
            "visual_title": "Accesibilidade visual e contraste",
            "wcag_143_title": "W3C WCAG 2.1 — Criterio 1.4.3 (Contraste mínimo)",
            "wcag_143_detail": "Referencia: relación de contraste 4.5:1 para texto normal e 3:1 para texto grande.",
            "wcag_1411_title": "W3C WCAG 2.1 — Criterio 1.4.11 (Contraste non textual)",
            "wcag_1411_detail": "Referencia: relación mínima de 3:1 para elementos visuais relevantes.",
            "documents_title": "Aplicación a documentos",
            "wcag2ict_title": "WCAG2ICT — Aplicación das WCAG a documentos e software non web",
            "wcag2ict_detail": "Base para a análise en presentacións (PDF, PPT, PPTX).",
            "color_title": "Percepción da cor",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Modelo de simulación da visión da cor (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Modelo para simulación de deficiencias na visión da cor.",
        },
    },
}


def _master(lang: str) -> dict:
    return MASTER_REPORT_TEXTS.get(lang, MASTER_REPORT_TEXTS["es"])


def _master_fmt(lang: str, section: str, key: str, **kwargs) -> str:
    text = MASTER_REPORT_TEXTS.get(lang, MASTER_REPORT_TEXTS["es"])[section][key]
    return text.format(**kwargs)

UI_TEXTS = {
    "es": {
        "default_title": "Informe de accesibilidad",
        "estimated_reading_time": "Tiempo estimado de lectura del material:",
        "intro_with_issues": "En el análisis del documento identificamos oportunidades de mejora para ayudarte a crear materiales más claros y accesibles, considerando:",
        "intro_no_issues": "El análisis de la presentación consideró:",
        "executive_summary": "Resumen ejecutivo",
        "teacher_report": "Informe de accesibilidad para profesorado",
        "recommendations_by_dimension": "Recomendaciones por dimensión",
        "recommendations_by_dimension_intro": "Abajo se detallan las recomendaciones organizadas por dimensión, indicando junto con las diapositivas o páginas en que se sugiere verificar cada aspecto.",
        "slide_summary": "Resumen por diapositivas",
        "slide_summary_intro": "Abajo se presenta, para cada diapositiva, el conjunto de recomendaciones aplicables identificadas en el análisis.",
        "criteria_and_references": "Criterios y referencias utilizados",
        "criteria_intro": "Las recomendaciones de este informe se basan en estándares internacionales de accesibilidad y en modelos de análisis reconocidos.",
        "limitations": "Limitaciones de la estimación",
        "references": "Referencias",
        "no_slides_review": "No se detectaron diapositivas para revisión.",
        "slides_for_review": "Diapositivas para revisión",
        "pages_for_review": "Páginas para revisión",
        "slide": "Diapositiva",
        "page": "Página",
        "recommendation": "Recomendación:",
        "dimension_legibility": "Dimensión Legibilidad",
        "dimension_contrast": "Dimensión Contraste",
        "dimension_organization": "Dimensión Organización",
        "dimension_images": "Dimensión Imágenes",
        "metric_font_size": "Tamaño de Fuente",
        "metric_typography": "Tipografía",
        "metric_line_spacing": "Interlineado",
        "metric_text_excess": "Exceso de Texto",
        "metric_contrast_level": "Nivel de Contraste",
        "metric_text_blocks": "Número de párrafos / bloques de texto",
        "metric_elements": "Número de elementos",
        "metric_alt_text": "Texto Alternativo",
    },
    "en": {
        "default_title": "Accessibility report",
        "estimated_reading_time": "Estimated reading time:",
        "intro_with_issues": "The document analysis identified improvement opportunities to help create clearer and more accessible materials, considering:",
        "intro_no_issues": "The presentation analysis considered:",
        "executive_summary": "Executive summary",
        "teacher_report": "Accessibility report for teaching staff",
        "recommendations_by_dimension": "Recommendations by dimension",
        "recommendations_by_dimension_intro": "Below are the recommendations organized by dimension, indicating the slides or pages where each aspect should be reviewed.",
        "slide_summary": "Summary by slide",
        "slide_summary_intro": "Below is the set of applicable recommendations identified for each slide.",
        "criteria_and_references": "Criteria and references used",
        "criteria_intro": "The recommendations in this report are based on international accessibility standards and recognized analysis models.",
        "limitations": "Estimation limitations",
        "references": "References",
        "no_slides_review": "No slides were identified for review.",
        "slides_for_review": "Slides for review",
        "pages_for_review": "Pages for review",
        "slide": "Slide",
        "page": "Page",
        "recommendation": "Recommendation:",
        "dimension_legibility": "Legibility Dimension",
        "dimension_contrast": "Contrast Dimension",
        "dimension_organization": "Organization Dimension",
        "dimension_images": "Images Dimension",
        "metric_font_size": "Font Size",
        "metric_typography": "Typography",
        "metric_line_spacing": "Line Spacing",
        "metric_text_excess": "Text Overload",
        "metric_contrast_level": "Contrast Level",
        "metric_text_blocks": "Number of paragraphs / text blocks",
        "metric_elements": "Number of elements",
        "metric_alt_text": "Alternative Text",
    },
    "pt": {
        "default_title": "Relatório de acessibilidade",
        "estimated_reading_time": "Tempo estimado de leitura do material:",
        "intro_with_issues": "A análise do documento identificou oportunidades de melhoria para ajudar a criar materiais mais claros e acessíveis, considerando:",
        "intro_no_issues": "A análise da apresentação considerou:",
        "executive_summary": "Resumo executivo",
        "teacher_report": "Relatório de acessibilidade para docentes",
        "recommendations_by_dimension": "Recomendações por dimensão",
        "recommendations_by_dimension_intro": "Abaixo estão as recomendações organizadas por dimensão, indicando os slides ou páginas em que se sugere verificar cada aspecto.",
        "slide_summary": "Resumo por slide",
        "slide_summary_intro": "Abaixo apresenta-se, para cada slide, o conjunto de recomendações aplicáveis identificadas na análise.",
        "criteria_and_references": "Critérios e referências utilizados",
        "criteria_intro": "As recomendações deste relatório baseiam-se em normas internacionais de acessibilidade e em modelos de análise reconhecidos.",
        "limitations": "Limitações da estimativa",
        "references": "Referências",
        "no_slides_review": "Nenhum slide foi identificado para revisão.",
        "slides_for_review": "Slides para revisão",
        "pages_for_review": "Páginas para revisão",
        "slide": "Slide",
        "page": "Página",
        "recommendation": "Recomendação:",
        "dimension_legibility": "Dimensão Legibilidade",
        "dimension_contrast": "Dimensão Contraste",
        "dimension_organization": "Dimensão Organização",
        "dimension_images": "Dimensão Imagens",
        "metric_font_size": "Tamanho da Fonte",
        "metric_typography": "Tipografia",
        "metric_line_spacing": "Espaçamento entre linhas",
        "metric_text_excess": "Excesso de Texto",
        "metric_contrast_level": "Nível de Contraste",
        "metric_text_blocks": "Número de parágrafos / blocos de texto",
        "metric_elements": "Número de elementos",
        "metric_alt_text": "Texto Alternativo",
    },
    "gl": {
        "default_title": "Informe de accesibilidade",
        "estimated_reading_time": "Tempo estimado de lectura do material:",
        "intro_with_issues": "Na análise do documento identificáronse oportunidades de mellora para crear materiais máis claros e accesibles, considerando:",
        "intro_no_issues": "A análise da presentación considerou:",
        "executive_summary": "Resumo executivo",
        "teacher_report": "Informe de accesibilidade para profesorado",
        "recommendations_by_dimension": "Recomendacións por dimensión",
        "recommendations_by_dimension_intro": "A continuación detállanse as recomendacións organizadas por dimensión, indicando as diapositivas ou páxinas nas que se suxire revisar cada aspecto.",
        "slide_summary": "Resumo por diapositiva",
        "slide_summary_intro": "A continuación preséntase, para cada diapositiva, o conxunto de recomendacións aplicables identificadas na análise.",
        "criteria_and_references": "Criterios e referencias utilizadas",
        "criteria_intro": "As recomendacións deste informe baséanse en estándares internacionais de accesibilidade e en modelos de análise recoñecidos.",
        "limitations": "Limitacións da estimación",
        "references": "Referencias",
        "no_slides_review": "Non se detectaron diapositivas para revisión.",
        "slides_for_review": "Diapositivas para revisión",
        "pages_for_review": "Páxinas para revisión",
        "slide": "Diapositiva",
        "page": "Páxina",
        "recommendation": "Recomendación:",
        "dimension_legibility": "Dimensión Lexibilidade",
        "dimension_contrast": "Dimensión Contraste",
        "dimension_organization": "Dimensión Organización",
        "dimension_images": "Dimensión Imaxes",
        "metric_font_size": "Tamaño da Fonte",
        "metric_typography": "Tipografía",
        "metric_line_spacing": "Interliñado",
        "metric_text_excess": "Exceso de Texto",
        "metric_contrast_level": "Nivel de Contraste",
        "metric_text_blocks": "Número de parágrafos / bloques de texto",
        "metric_elements": "Número de elementos",
        "metric_alt_text": "Texto Alternativo",
    },
}

def build_units_links_pdf_markup_master(payload: dict, unit_indexes: List[int], lang: str) -> str:
    m = _master(lang)

    if not unit_indexes:
        return html.escape(m["common"]["no_slides_review"])

    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    label = m["common"]["pages_for_review"] if document_type == "pdf" else m["common"]["slides_for_review"]

    links = []
    for unit_index in unit_indexes:
        try:
            unit_num = int(unit_index)
        except Exception:
            continue
        anchor = f"slide-summary-{unit_num}"
        links.append(f'<a href="#{anchor}" color="blue">{unit_num}</a>')

    if not links:
        return html.escape(m["common"]["no_slides_review"])

    return f"{html.escape(label)}: " + ", ".join(links)

def build_units_links_html_master(payload: dict, unit_indexes: List[int], lang: str) -> str:
    m = _master(lang)
    if not unit_indexes:
        return html.escape(m["common"]["no_slides_review"])

    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    label = m["common"]["pages_for_review"] if document_type == "pdf" else m["common"]["slides_for_review"]

    links = []
    for unit_index in unit_indexes:
        anchor = f"slide-summary-{int(unit_index)}"
        links.append(f'<a href="#{anchor}" class="slide-jump-link">{int(unit_index)}</a>')

    return f"{html.escape(label)}: " + ", ".join(links)

REPORT_I18N = {
    "es": {
        "title": "Informe de accesibilidad",
        "intro_with_issues": "En el análisis del documento identificamos oportunidades de mejora para ayudarte a crear materiales más claros y accesibles, considerando:",
        "intro_no_issues": "El análisis de la presentación consideró:",
        "dimension_summaries": {
            "legibility": "Tamaño de letra, interlineado, tipografía y cantidad de texto.",
            "contrast": "Color, contraste y posibles dificultades de percepción cromática.",
            "organization": "Jerarquía visual, bloques de contenido y cantidad de elementos por diapositiva.",
            "images": "Presencia de descripciones alternativas de accesibilidad.",
        },
        "recommendations": {
            "font_size": "Aumenta el tamaño de la letra y procura mantener, como referencia, un tamaño mínimo de {min_font:.0f}.",
            "typography": "Prioriza tipografías sans serif consistentes, especialmente en títulos, cuerpo y etiquetas.",
            "line_spacing": "Aumenta el espacio entre líneas y procura mantener, como referencia, un interlineado mínimo de {min_spacing:.2f}.",
            "text_excess": "Reduce la cantidad de texto por diapositiva o página cuando supere la referencia de {max_words} palabras.",
            "color": "Revisa el uso de colores en las diapositivas para asegurar que la información sea distinguible para personas con diferentes tipos de visión del color. Evita combinaciones que puedan generar confusión, por ejemplo rojo y verde, y refuerza la información con texto, iconos o subrayados.",
            "contrast": "Aumenta la diferencia entre color de texto y fondo, o reestructura el bloque visual para cumplir mejor con WCAG/WCAG2ICT.",
            "text_blocks": "Segmenta mejor el contenido y procura organizar cada unidad en al menos {min_blocks} bloques cuando sea posible.",
            "elements": "Reduce la cantidad total de elementos por diapositiva y procura mantener un máximo de {max_elements} elementos visibles.",
            "alt_text": "Añade texto alternativo a las imágenes relevantes para que puedan interpretarse con tecnologías de apoyo.",
        },
        "fixed_criteria": {
            "section_title": "Criterios y referencias utilizados",
            "intro": "Las recomendaciones de este informe se basan en estándares internacionales de accesibilidad y en modelos de análisis reconocidos.",
            "visual_contrast_title": "Accesibilidad visual y contraste",
            "wcag_143_title": "W3C WCAG 2.1 — Criterio 1.4.3 (Contraste mínimo)",
            "wcag_143_detail": "Referencia: relación de contraste 4.5:1 para texto normal y 3:1 para texto grande.",
            "wcag_1411_title": "W3C WCAG 2.1 — Criterio 1.4.11 (Contraste no textual)",
            "wcag_1411_detail": "Referencia: relación mínima de 3:1 para elementos visuales relevantes.",
            "documents_title": "Aplicación a documentos",
            "wcag2ict_title": "WCAG2ICT — Aplicación de WCAG a documentos y software no web",
            "wcag2ict_detail": "Base para el análisis en presentaciones (PDF, PPT, PPTX).",
            "color_title": "Percepción del color",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Modelo de simulación de visión del color (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Modelo para simulación de deficiencias en la percepción del color.",
        },
    },
    "en": {
        "title": "Accessibility report",
        "intro_with_issues": "The document analysis identified improvement opportunities to help create clearer and more accessible materials, considering:",
        "intro_no_issues": "The presentation analysis considered:",
        "dimension_summaries": {
            "legibility": "Font size, line spacing, typography, and amount of text.",
            "contrast": "Color, contrast, and possible color perception difficulties.",
            "organization": "Visual hierarchy, content blocks, and number of elements per slide.",
            "images": "Presence of alternative accessibility descriptions.",
        },
        "recommendations": {
            "font_size": "Increase font size and aim to keep, as a reference, a minimum size of {min_font:.0f}.",
            "typography": "Prioritize consistent sans serif typefaces, especially in titles, body text, and labels.",
            "line_spacing": "Increase line spacing and aim to keep, as a reference, a minimum line spacing of {min_spacing:.2f}.",
            "text_excess": "Reduce the amount of text per slide or page when it exceeds the reference of {max_words} words.",
            "color": "Review the use of colors in the slides to ensure the information is distinguishable for people with different types of color vision. Avoid combinations that may cause confusion, for example red and green, and reinforce the information with text, icons, or underlining.",
            "contrast": "Increase the difference between text and background colors, or restructure the visual block to better comply with WCAG/WCAG2ICT.",
            "text_blocks": "Segment the content more clearly and aim to organize each unit into at least {min_blocks} blocks whenever possible.",
            "elements": "Reduce the total number of elements per slide and aim to keep a maximum of {max_elements} visible elements.",
            "alt_text": "Add alternative text to relevant images so they can be interpreted with assistive technologies.",
        },
        "fixed_criteria": {
            "section_title": "Criteria and references used",
            "intro": "The recommendations in this report are based on international accessibility standards and recognized analysis models.",
            "visual_contrast_title": "Visual accessibility and contrast",
            "wcag_143_title": "W3C WCAG 2.1 — Criterion 1.4.3 (Minimum contrast)",
            "wcag_143_detail": "Reference: contrast ratio 4.5:1 for normal text and 3:1 for large text.",
            "wcag_1411_title": "W3C WCAG 2.1 — Criterion 1.4.11 (Non text contrast)",
            "wcag_1411_detail": "Reference: minimum 3:1 ratio for relevant visual elements.",
            "documents_title": "Application to documents",
            "wcag2ict_title": "WCAG2ICT — Applying WCAG to non web documents and software",
            "wcag2ict_detail": "Basis for analysis in presentations (PDF, PPT, PPTX).",
            "color_title": "Color perception",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Color vision simulation model (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Model for simulation of color vision deficiencies.",
        },
    },
    "pt": {
        "title": "Relatório de acessibilidade",
        "intro_with_issues": "A análise do documento identificou oportunidades de melhoria para ajudar a criar materiais mais claros e acessíveis, considerando:",
        "intro_no_issues": "A análise da apresentação considerou:",
        "dimension_summaries": {
            "legibility": "Tamanho da letra, espaçamento entre linhas, tipografia e quantidade de texto.",
            "contrast": "Cor, contraste e possíveis dificuldades de percepção cromática.",
            "organization": "Hierarquia visual, blocos de conteúdo e quantidade de elementos por slide.",
            "images": "Presença de descrições alternativas de acessibilidade.",
        },
        "recommendations": {
            "font_size": "Aumente o tamanho da letra e procure manter, como referência, um tamanho mínimo de {min_font:.0f}.",
            "typography": "Priorize tipografias sans serif consistentes, especialmente em títulos, corpo do texto e rótulos.",
            "line_spacing": "Aumente o espaçamento entre linhas e procure manter, como referência, um interlineado mínimo de {min_spacing:.2f}.",
            "text_excess": "Reduza a quantidade de texto por slide ou página quando ultrapassar a referência de {max_words} palavras.",
            "color": "Revise o uso de cores nos slides para garantir que a informação seja distinguível para pessoas com diferentes tipos de visão de cores. Evite combinações que possam gerar confusão, por exemplo vermelho e verde, e reforce a informação com texto, ícones ou sublinhado.",
            "contrast": "Aumente a diferença entre a cor do texto e do fundo, ou reestruture o bloco visual para cumprir melhor com WCAG/WCAG2ICT.",
            "text_blocks": "Segmente melhor o conteúdo e procure organizar cada unidade em pelo menos {min_blocks} blocos sempre que possível.",
            "elements": "Reduza a quantidade total de elementos por slide e procure manter no máximo {max_elements} elementos visíveis.",
            "alt_text": "Adicione texto alternativo às imagens relevantes para que possam ser interpretadas com tecnologias assistivas.",
        },
        "fixed_criteria": {
            "section_title": "Critérios e referências utilizados",
            "intro": "As recomendações deste relatório baseiam-se em normas internacionais de acessibilidade e em modelos de análise reconhecidos.",
            "visual_contrast_title": "Acessibilidade visual e contraste",
            "wcag_143_title": "W3C WCAG 2.1 — Critério 1.4.3 (Contraste mínimo)",
            "wcag_143_detail": "Referência: relação de contraste 4.5:1 para texto normal e 3:1 para texto grande.",
            "wcag_1411_title": "W3C WCAG 2.1 — Critério 1.4.11 (Contraste não textual)",
            "wcag_1411_detail": "Referência: relação mínima de 3:1 para elementos visuais relevantes.",
            "documents_title": "Aplicação a documentos",
            "wcag2ict_title": "WCAG2ICT — Aplicação das WCAG a documentos e software não web",
            "wcag2ict_detail": "Base para a análise em apresentações (PDF, PPT, PPTX).",
            "color_title": "Percepção da cor",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Modelo de simulação da visão das cores (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Modelo para simulação de deficiências na visão de cores.",
        },
    },
    "gl": {
        "title": "Informe de accesibilidade",
        "intro_with_issues": "Na análise do documento identificáronse oportunidades de mellora para crear materiais máis claros e accesibles, considerando:",
        "intro_no_issues": "A análise da presentación considerou:",
        "dimension_summaries": {
            "legibility": "Tamaño da letra, interliñado, tipografía e cantidade de texto.",
            "contrast": "Cor, contraste e posibles dificultades de percepción cromática.",
            "organization": "Xerarquía visual, bloques de contido e cantidade de elementos por diapositiva.",
            "images": "Presenza de descricións alternativas de accesibilidade.",
        },
        "recommendations": {
            "font_size": "Aumenta o tamaño da letra e procura manter, como referencia, un tamaño mínimo de {min_font:.0f}.",
            "typography": "Prioriza tipografías sans serif consistentes, especialmente en títulos, corpo do texto e etiquetas.",
            "line_spacing": "Aumenta o espazo entre liñas e procura manter, como referencia, un interliñado mínimo de {min_spacing:.2f}.",
            "text_excess": "Reduce a cantidade de texto por diapositiva ou páxina cando supere a referencia de {max_words} palabras.",
            "color": "Revisa o uso de cores nas diapositivas para asegurar que a información sexa distinguible para persoas con diferentes tipos de visión da cor. Evita combinacións que poidan xerar confusión, por exemplo vermello e verde, e reforza a información con texto, iconas ou subliñado.",
            "contrast": "Aumenta a diferenza entre a cor do texto e do fondo, ou reestrutura o bloque visual para cumprir mellor con WCAG/WCAG2ICT.",
            "text_blocks": "Segmenta mellor o contido e procura organizar cada unidade en polo menos {min_blocks} bloques cando sexa posible.",
            "elements": "Reduce a cantidade total de elementos por diapositiva e procura manter un máximo de {max_elements} elementos visibles.",
            "alt_text": "Engade texto alternativo ás imaxes relevantes para que poidan interpretarse con tecnoloxías de apoio.",
        },
        "fixed_criteria": {
            "section_title": "Criterios e referencias utilizadas",
            "intro": "As recomendacións deste informe baséanse en estándares internacionais de accesibilidade e en modelos de análise recoñecidos.",
            "visual_contrast_title": "Accesibilidade visual e contraste",
            "wcag_143_title": "W3C WCAG 2.1 — Criterio 1.4.3 (Contraste mínimo)",
            "wcag_143_detail": "Referencia: relación de contraste 4.5:1 para texto normal e 3:1 para texto grande.",
            "wcag_1411_title": "W3C WCAG 2.1 — Criterio 1.4.11 (Contraste non textual)",
            "wcag_1411_detail": "Referencia: relación mínima de 3:1 para elementos visuais relevantes.",
            "documents_title": "Aplicación a documentos",
            "wcag2ict_title": "WCAG2ICT — Aplicación das WCAG a documentos e software non web",
            "wcag2ict_detail": "Base para a análise en presentacións (PDF, PPT, PPTX).",
            "color_title": "Percepción da cor",
            "brettel_title": "Brettel et al. (1997)",
            "brettel_detail": "Modelo de simulación da visión da cor (protanopia, deuteranopia, tritanopia).",
            "machado_title": "Machado et al. (2009)",
            "machado_detail": "Modelo para simulación de deficiencias na visión da cor.",
        },
    },
}

def _ui(lang: str, key: str) -> str:
    return UI_TEXTS.get(lang, UI_TEXTS["es"]).get(key, UI_TEXTS["es"].get(key, key))

def _ri(lang: str, section: str, key: Optional[str] = None):
    base = REPORT_I18N.get(lang, REPORT_I18N["es"])
    value = base.get(section, {})
    if key is None:
        return value
    if isinstance(value, dict):
        return value.get(key, REPORT_I18N["es"].get(section, {}).get(key, key))
    return value

WCAG_NORMAL_TEXT_RATIO = 4.5
WCAG_LARGE_TEXT_RATIO = 3.0
WCAG_NON_TEXT_RATIO = 3.0
TEXT_DENSITY_WORD_THRESHOLD = 60
PARAGRAPH_DENSITY_WORD_THRESHOLD = 60
SMALL_FONT_THRESHOLD_PT = 22.0
MAX_RENDER_SIDE = 1400

# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# ---------------------------------------------------------

MIN_LINE_SPACING = 1.15
MAX_WORDS_PER_UNIT = 60
MIN_TEXT_BLOCKS = 2
MAX_ELEMENTS = 7

READING_WORDS_PER_MINUTE = 140.0
SECONDS_PER_IMAGE = 5.0
ELEMENTS_BASELINE = 3
WORDS_BASELINE = 60

PPTX_NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

FONT_SANS_COMPLIANCE_RATIO = 0.80
FONT_SERIF_NONCOMPLIANCE_RATIO = 0.20
FONT_MIN_KNOWN_WORD_RATIO = 0.60
MAX_FONT_EXAMPLES = 5

PDF_HEADER_LOGO_NAME = "../resources/mail/aiuda-logo.png"
PDF_FOOTER_IMAGE_NAME = "../resources/mail/aiuda-footer.png"

PDF_LOGO_WIDTH_MM = 30
PDF_LOGO_HEIGHT_MM = 14
PDF_HEADER_TOP_OFFSET_MM = 6
PDF_HEADER_LEFT_OFFSET_MM = 16

PDF_FOOTER_HEIGHT_MM = 22
PDF_FOOTER_BOTTOM_OFFSET_MM = 0

PDF_PAGE_MARGIN_TOP_MM = 46
PDF_PAGE_MARGIN_BOTTOM_MM = 34

FONT_SERIF_ALIASES = {
    "times",
    "timesnewroman",
    "timesroman",
    "timesnr",
    "georgia",
    "garamond",
    "cambria",
    "baskerville",
    "palatino",
    "palatinolinotype",
    "bookantiqua",
    "constantia",
    "bodoni",
    "didot",
    "nimbusroman",
    "liberationserif",
    "dejavuserif",
    "serif",
}

FONT_SANS_ALIASES = {
    "arial",
    "arialmt",
    "arialunicode",
    "calibri",
    "calibrilight",
    "aptos",
    "verdana",
    "tahoma",
    "helvetica",
    "helveticaneue",
    "segoe",
    "segoeui",
    "opensans",
    "sourcesans",
    "sourcesanspro",
    "montserrat",
    "roboto",
    "lato",
    "inter",
    "ubuntu",
    "futura",
    "avenir",
    "nimbussans",
    "liberationsans",
    "dejavusans",
    "sans",
    "sansserif",
}
BULLET_RE = re.compile(
    r"^\s*(?:[\-\u2022\u25E6\u25AA\u2023\u25CF\u25CB\u25A0\u25A1\u2013\u2014]|\(?\d+[\.\)]|[A-Za-z][\.\)])\s+"
)

# ------------------------------------


METHODOLOGY_REFERENCES = [
    {
        "reference_code": "WCAG-1.4.3",
        "title": "W3C WCAG 2.1 - Success Criterion 1.4.3 Contrast (Minimum)",
        "metric_type": "Umbral normativo de referencia",
        "details": "Se usa como referencia 4.5:1 para texto normal y 3:1 para texto grande.",
    },
    {
        "reference_code": "WCAG-1.4.11",
        "title": "W3C WCAG 2.1 - Success Criterion 1.4.11 Non-text Contrast",
        "metric_type": "Umbral normativo de referencia",
        "details": "Se usa como referencia 3:1 para componentes visuales y gráficos relevantes.",
    },
    {
        "reference_code": "WCAG2ICT",
        "title": "W3C WCAG2ICT - Applying WCAG to Non-Web Documents and Software",
        "metric_type": "Umbral normativo de referencia",
        "details": "Sirve de base para aplicar estos criterios a PDF, PPT y PPTX, aunque su naturaleza es orientativa.",
    },
    {
        "reference_code": "BRETTEL-1997",
        "title": "Brettel et al., 1997 - Computerized simulation of color appearance for dichromats",
        "metric_type": "Métrica heurística del sistema",
        "details": "Referencia metodológica para simulación/estimación de protanopia, deuteranopia y tritanopia.",
    },
    {
        "reference_code": "MACHADO-2009",
        "title": "Machado et al., 2009 - A Physiologically-based Model for Simulation of Color Vision Deficiency",
        "metric_type": "Métrica heurística del sistema",
        "details": "Referencia metodológica para simulación de deficiencia visual cromática y análisis comparativo orientativo.",
    },
]

CVD_MATRICES = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}


# ---------------------------------------------------------
# ARGUMENTS
# ---------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ALUDA - análisis documental y generación de informes multilingües"
    )
    parser.add_argument("input_file", type=str, help="Archivo PDF/PPT/PPTX de entrada")
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
        help="Idioma del documento (es, en, pt, gl). Si no se indica, se intentará detectar.",
    )
    parser.add_argument(
        "--translate-to",
        nargs="*",
        default=["es", "en", "pt", "gl"],
        help="Idiomas destino para el informe. Ejemplo: --translate-to es en pt gl",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Intenta OCR cuando un PDF no contiene texto extraíble (solo se usa si hay soporte disponible).",
    )
    parser.add_argument(
        "--max-translation-chars",
        type=int,
        default=800,
        help="Tamaño máximo por bloque de traducción",
    )
    return parser.parse_args()


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def build_units_links_html_master(payload: dict, unit_indexes: List[int], lang: str) -> str:
    m = _master(lang)

    if not unit_indexes:
        return html.escape(m["common"]["no_slides_review"])

    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    label = m["common"]["pages_for_review"] if document_type == "pdf" else m["common"]["slides_for_review"]

    links = []
    for unit_index in unit_indexes:
        try:
            unit_num = int(unit_index)
        except Exception:
            continue
        anchor = f"slide-summary-{unit_num}"
        links.append(f'<a href="#{anchor}" class="slide-jump-link">{unit_num}</a>')

    if not links:
        return html.escape(m["common"]["no_slides_review"])

    return f"{html.escape(label)}: " + ", ".join(links)


def _format_units_for_review_master(payload: dict, unit_indexes: List[int], lang: str) -> str:
    m = _master(lang)
    if not unit_indexes:
        return m["common"]["no_slides_review"]
    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    label = m["common"]["pages_for_review"] if document_type == "pdf" else m["common"]["slides_for_review"]
    return f"{label}: " + ", ".join(str(x) for x in unit_indexes)


def build_dimension_recommendations_master(payload: dict, lang: str) -> List[dict]:
    m = _master(lang)
    mm = m["metrics"]
    dd = m["dimensions"]

    sections = [
        {
            "dimension": dd["visual"]["title"],
            "summary": dd["visual"]["summary"],
            "items": [
                {
                    "metric": mm["font_size"]["label"],
                    "recommendation": mm["font_size"]["recommendation"].format(min_font=SMALL_FONT_THRESHOLD_PT),
                    "units": _collect_unit_indexes_for_categories(payload, ["small_fonts"]),
                },
                {
                    "metric": mm["typography"]["label"],
                    "recommendation": mm["typography"]["recommendation"],
                    "units": _collect_unit_indexes_for_categories(payload, ["font_family"]),
                },
                {
                    "metric": mm["line_spacing"]["label"],
                    "recommendation": mm["line_spacing"]["recommendation"].format(min_spacing=MIN_LINE_SPACING),
                    "units": _collect_unit_indexes_for_categories(payload, ["line_spacing"]),
                },
                {
                    "metric": mm["text_amount"]["label"],
                    "recommendation": mm["text_amount"]["recommendation"].format(max_words=MAX_WORDS_PER_UNIT),
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_words", "dense_text"]),
                },
                {
                    "metric": mm["color"]["label"],
                    "recommendation": mm["color"]["recommendation"],
                    "units": _collect_unit_indexes_for_categories(payload, ["cvd_risk"]),
                },
                {
                    "metric": mm["contrast"]["label"],
                    "recommendation": mm["contrast"]["recommendation"],
                    "units": _collect_unit_indexes_for_categories(payload, ["text_contrast", "figure_contrast"]),
                },
            ],
        },
        {
            "dimension": dd["organization"]["title"],
            "summary": dd["organization"]["summary"],
            "items": [
                {
                    "metric": mm["visual_hierarchy"]["label"],
                    "recommendation": mm["visual_hierarchy"]["recommendation"].format(min_blocks=MIN_TEXT_BLOCKS),
                    "units": _collect_unit_indexes_for_categories(payload, ["insufficient_text_blocks"]),
                },
                {
                    "metric": mm["elements"]["label"],
                    "recommendation": mm["elements"]["recommendation"].format(max_elements=MAX_ELEMENTS),
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_elements"]),
                },
            ],
        },
        {
            "dimension": dd["images"]["title"],
            "summary": dd["images"]["summary"],
            "items": [
                {
                    "metric": mm["alt_text"]["label"],
                    "recommendation": mm["alt_text"]["recommendation"],
                    "units": _collect_unit_indexes_for_categories(payload, ["missing_alt_text"]),
                },
            ],
        },
    ]

    filtered_sections: List[dict] = []

    for section in sections:
        filtered_items = []
        for item in section["items"]:
            units = _normalize_recommendation_units_master(item.get("units"))
            if units:
                new_item = dict(item)
                new_item["units"] = units
                filtered_items.append(new_item)

        if filtered_items:
            new_section = dict(section)
            new_section["items"] = filtered_items
            filtered_sections.append(new_section)

    return filtered_sections

def _normalize_recommendation_units_master(units: Any) -> List[int]:
    if isinstance(units, list):
        out = []
        for value in units:
            try:
                out.append(int(value))
            except Exception:
                continue
        return sorted(set(out))
    return []


def build_slide_recommendations_summary_master(payload: dict, lang: str) -> List[dict]:
    m = _master(lang)
    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    unit_label = m["common"]["page"] if document_type == "pdf" else m["common"]["slide"]

    sections = build_dimension_recommendations_master(payload, lang)
    per_unit: Dict[int, List[dict]] = {}

    for section in sections:
        for item in section["items"]:
            for unit_index in _normalize_recommendation_units_master(item["units"]):
                per_unit.setdefault(unit_index, []).append(
                    {
                        "dimension": section["dimension"],
                        "metric": item["metric"],
                        "recommendation": item["recommendation"],
                    }
                )

    result = []
    for unit_index in sorted(per_unit.keys()):
        result.append(
            {
                "unit_index": unit_index,
                "label": f"{unit_label} {unit_index}",
                "items": per_unit[unit_index],
            }
        )
    return result

def build_dimension_recommendations_html_master(payload: dict, lang: str) -> str:
    m = _master(lang)
    sections = build_dimension_recommendations_master(payload, lang)
    blocks = []

    for section in sections:
        items_html = []
        for item in section["items"]:
            units_html = build_units_links_html_master(payload, item["units"], lang)

            items_html.append(
                f"""
                <article class="card issue-card">
                  <div class="issue-location">{html.escape(str(item['metric']))}</div>
                  <div class="issue-recommendation">
                    <strong>{html.escape(m['common']['recommendation'])}</strong>
                    {html.escape(str(item['recommendation']))}
                  </div>
                  <div class="issue-meta">{units_html}</div>
                </article>
                """
            )

        blocks.append(
            f"""
            <section class="section">
              <h2>{html.escape(str(section['dimension']))}</h2>
              <p class="dimension-summary">{html.escape(str(section['summary']))}</p>
              {''.join(items_html)}
            </section>
            """
        )

    return "".join(blocks)

def build_slide_recommendations_html_master(payload: dict, lang: str) -> str:
    m = _master(lang)
    slides = build_slide_recommendations_summary_master(payload, lang)

    if not slides:
        return f"""
        <section class="section">
          <div class="card">
            <p>{html.escape(m['common']['no_slides_review'])}</p>
          </div>
        </section>
        """

    blocks = []
    for slide in slides:
        item_html = []
        for item in slide["items"]:
            item_html.append(
                f"""
                <article class="slide-rec-item">
                  <div class="slide-rec-metric">{html.escape(str(item["metric"]))}</div>
                  <div class="slide-rec-dimension">{html.escape(str(item["dimension"]))}</div>
                  <div class="slide-rec-text">
                    <strong>{html.escape(m['common']['recommendation'])}</strong>
                    {html.escape(str(item["recommendation"]))}
                  </div>
                </article>
                """
            )

        slide_anchor = f"slide-summary-{int(slide['unit_index'])}"

        blocks.append(
            f"""
            <section class="section" id="{slide_anchor}">
              <div class="slide-summary-card">
                <h2>{html.escape(str(slide["label"]))}</h2>
                {''.join(item_html)}
              </div>
            </section>
            """
        )

    return "".join(blocks)

def build_fixed_criteria_section_html_master(lang: str) -> str:
    m = _master(lang)
    c = m["criteria"]
    s = m["sections"]

    return f"""
    <section class="section">
    <hr class="section-divider">
      <h2>{html.escape(s['criteria_title'])}</h2>
      <div class="card">
        <p>{html.escape(s['criteria_intro'])}</p>

        <h3>{html.escape(c['visual_title'])}</h3>
        <p><strong>{html.escape(c['wcag_143_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['wcag_143_detail'])}</p>

        <p><strong>{html.escape(c['wcag_1411_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['wcag_1411_detail'])}</p>

        <h3>{html.escape(c['documents_title'])}</h3>
        <p><strong>{html.escape(c['wcag2ict_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['wcag2ict_detail'])}</p>

        <h3>{html.escape(c['color_title'])}</h3>
        <p><strong>{html.escape(c['brettel_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['brettel_detail'])}</p>

        <p><strong>{html.escape(c['machado_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['machado_detail'])}</p>
      </div>
    </section>
    """

def render_report_html_master(payload: dict, title: str, lang: str) -> str:
    summary = payload.get("summary", {}) or {}
    visual_metrics = payload.get("visual_metrics", {}) or {}
    m = _master(lang)

    totals = summary.get("totals", {}) or {}
    reportable_issue_count = int(totals.get("reportable_issue_count", totals.get("issue_count", 0)) or 0)
    has_issues = reportable_issue_count > 0

    branding_assets = get_pdf_branding_assets()
    logo_uri = branding_assets["logo"].as_uri() if branding_assets["logo"] else ""
    bottom_uri = branding_assets["bottom"].as_uri() if branding_assets["bottom"] else ""

    estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")

    intro_text = m["intro"] if has_issues else m["intro_no_issues"]

    summary_cards_html = "".join(
        f"""
        <div class="metric-card teacher-card">
          <div class="metric-label">{html.escape(str(card['title']))}</div>
          <div class="teacher-detail">{html.escape(str(card['text']))}</div>
        </div>
        """
        for card in m["summary_blocks"]
    )

    styles = """
    :root {
      --bg: #f4f7fa;
      --panel: #ffffff;
      --line: #dde6ee;
      --line-strong: #c9d6e1;
      --text: #12263a;
      --muted: #536474;
      --soft: #f8fafc;
      --teacher-soft: #f4f8fb;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 24px; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; }
    .pdf-header-logo, .pdf-footer-image { display: none; }
    .page { max-width: 980px; margin: 0 auto; background: var(--panel); border: 1px solid var(--line); border-radius: 22px; overflow: hidden; box-shadow: 0 6px 24px rgba(18, 38, 58, 0.08); }
    .hero { padding: 30px 32px 18px 32px; border-bottom: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%); }
    .hero h1 { margin: 0; font-size: 30px; line-height: 1.2; }
    .hero p { margin: 10px 0 0 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .hero-overview { white-space: pre-line; }
    .section { padding: 24px 32px 0 32px; }
    .section:last-child { padding-bottom: 32px; }
    h2 { margin: 0 0 14px 0; font-size: 21px; line-height: 1.3; }
    h3 { margin: 0 0 12px 0; font-size: 17px; line-height: 1.3; }
    .metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .metric-card { border: 1px solid var(--line); border-radius: 16px; background: var(--soft); padding: 14px 16px; min-height: 90px; }
    .teacher-card { background: var(--teacher-soft); }
    .metric-label { color: var(--text); font-size: 15px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; }
    .teacher-detail { color: var(--muted); font-size: 14px; line-height: 1.7; }
    .card { border: 1px solid var(--line); border-radius: 16px; background: #fff; padding: 16px 18px; margin-bottom: 14px; }
    .decision-card { background: linear-gradient(180deg, #ffffff 0%, #f8fcff 100%); }
    .dimension-summary { color: var(--muted); font-size: 14px; line-height: 1.7; margin: 0 0 14px 0; }
    .slide-summary-card { border: 1px solid var(--line); border-radius: 18px; background: #fff; padding: 18px 20px; }
    .slide-rec-item { border: 1px solid var(--line); border-radius: 14px; background: var(--soft); padding: 14px 16px; margin-bottom: 12px; }
    .slide-rec-metric { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
    .slide-rec-dimension { color: var(--muted); font-size: 13px; line-height: 1.6; margin-bottom: 8px; }
    .slide-rec-text, .reference-detail, li { font-size: 14px; line-height: 1.7; }
    .section-divider {
      border: 0;
      border-top: 1px solid #d9dde3;
      margin: 18px 0 0 0;
    }
    @media print {
      @page {
        size: A4;
        margin-top: 46mm;
        margin-right: 14mm;
        margin-bottom: 34mm;
        margin-left: 14mm;
        @top-left { content: element(headerLogo); }
        @bottom-center { content: element(footerImage); }
      }
      body { padding: 0; background: #fff; }
      .page { max-width: none; border: 0; box-shadow: none; border-radius: 0; }
      .card, .metric-card, .slide-summary-card, .slide-rec-item { break-inside: avoid; page-break-inside: avoid; }
      .pdf-header-logo {
        display: block;
        position: running(headerLogo);
        width: 30mm;
        height: 14mm;
        object-fit: contain;
        margin-top: 6mm;
        margin-left: 2mm;
      }
      .pdf-footer-image {
        display: block;
        position: running(footerImage);
        width: 210mm;
        height: 22mm;
        object-fit: cover;
        margin: 0;
      }
      .section { padding-left: 0; padding-right: 0; }
    }
    """

    recommendations_html = ""
    slides_html = ""

    if has_issues:
        recommendations_html = f"""
        <section class="section">
          <hr class="section-divider">
          <h2>{html.escape(m['sections']['by_dimension_title'])}</h2>
          <div class="card">
            <p>{html.escape(m['sections']['by_dimension_intro'])}</p>
          </div>
        </section>

        {build_dimension_recommendations_html_master(payload, lang)}

        <section class="section">
          <hr class="section-divider">
          <h2>{html.escape(m['sections']['by_slide_title'])}</h2>
          <div class="card">
            <p>{html.escape(m['sections']['by_slide_intro'])}</p>
          </div>
        </section>

        {build_slide_recommendations_html_master(payload, lang)}
        """

    return f"""<!DOCTYPE html>
<html lang="{html.escape(lang)}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(m['report_title'])}</title>
    <style>{styles}</style>
  </head>
  <body>
    {f'<img class="pdf-header-logo" src="{logo_uri}" alt="Logo">' if logo_uri else ''}
    {f'<img class="pdf-footer-image" src="{bottom_uri}" alt="Bottom">' if bottom_uri else ''}
    <main class="page">
      <header class="hero">
        <h1>{html.escape(m['report_title'])}</h1>
        <p class="hero-overview">{html.escape(str(summary.get('overview', '')))}</p>
        <p><strong>{html.escape(m['estimated_reading_time'])}</strong> {html.escape(str(estimated_read_time_human))}</p>
      </header>

      <section class="section">
        <hr class="section-divider">
        <div class="card decision-card">
          <p>{html.escape(intro_text)}</p>
          <div class="metric-grid">{summary_cards_html}</div>
        </div>
      </section>

      {recommendations_html}

      {build_fixed_criteria_section_html_master(lang)}

    </main>
  </body>
</html>
"""

def render_html_to_pdf_master(html_content: str, pdf_path: Path, payload: Optional[dict] = None, lang: str = "es") -> None:
    try:
        from weasyprint import HTML  # type: ignore
        HTML(string=html_content, base_url=str(pdf_path.parent)).write_pdf(str(pdf_path))
        return
    except Exception:
        pass

    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.enums import TA_LEFT  # type: ignore
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, HRFlowable  # type: ignore

        payload = payload or {}
        summary = payload.get("summary", {}) or {}
        visual_metrics = payload.get("visual_metrics", {}) or {}
        m = _master(lang)

        totals = summary.get("totals", {}) or {}
        reportable_issue_count = int(totals.get("reportable_issue_count", totals.get("issue_count", 0)) or 0)
        has_issues = reportable_issue_count > 0

        estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")
        intro_text = m["intro"] if has_issues else m["intro_no_issues"]

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=PDF_PAGE_MARGIN_TOP_MM * mm,
            bottomMargin=PDF_PAGE_MARGIN_BOTTOM_MM * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "AltTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=10,
            alignment=TA_LEFT,
        )
        heading_style = ParagraphStyle(
            "AltHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=8,
            spaceBefore=12,
        )
        body_style = ParagraphStyle(
            "AltBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=4,
        )
        muted_style = ParagraphStyle(
            "AltMuted",
            parent=body_style,
            textColor=colors.HexColor("#536474"),
        )

        def _divider():
            return HRFlowable(
                width="100%",
                thickness=0.8,
                color=colors.HexColor("#d9dde3"),
                spaceBefore=8,
                spaceAfter=12,
                lineCap="round",
            )

        story: List[Any] = []
        overview_pdf = html.escape(str(summary.get("overview", ""))).replace("\n", "<br/>")

        story.append(Paragraph(html.escape(m["report_title"]), title_style))
        story.append(Paragraph(overview_pdf, muted_style))
        story.append(
            Paragraph(
                f"<b>{html.escape(m['estimated_reading_time'])}</b> {html.escape(str(estimated_read_time_human))}",
                body_style,
            )
        )
        story.append(Spacer(1, 4))
        story.append(_divider())

        story.append(Paragraph(html.escape(intro_text), body_style))
        story.append(Spacer(1, 4))

        for card in m["summary_blocks"]:
            story.append(Paragraph(f"<b>{html.escape(card['title'])}</b>", body_style))
            story.append(Paragraph(html.escape(card["text"]), muted_style))

        if has_issues:
            story.append(_divider())
            story.append(Paragraph(m["sections"]["by_dimension_title"], heading_style))
            story.append(Paragraph(m["sections"]["by_dimension_intro"], body_style))

            for section in build_dimension_recommendations_master(payload, lang):
                story.append(Paragraph(section["dimension"], heading_style))
                story.append(Paragraph(html.escape(section["summary"]), muted_style))

                for item in section["items"]:
                    story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                    story.append(
                        Paragraph(
                            f"<b>{html.escape(m['common']['recommendation'])}</b> {html.escape(str(item['recommendation']))}",
                            body_style,
                        )
                    )

                    units_markup = build_units_links_pdf_markup_master(payload, item["units"], lang)
                    story.append(Paragraph(units_markup, muted_style))
                    story.append(Spacer(1, 4))

            story.append(_divider())
            story.append(Paragraph(m["sections"]["by_slide_title"], heading_style))
            story.append(Paragraph(m["sections"]["by_slide_intro"], body_style))

            for slide in build_slide_recommendations_summary_master(payload, lang):
                slide_anchor = f"slide-summary-{int(slide['unit_index'])}"
                story.append(
                    Paragraph(
                        f'<a name="{slide_anchor}"/>{html.escape(str(slide["label"]))}',
                        heading_style,
                    )
                )

                for item in slide["items"]:
                    story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                    story.append(Paragraph(html.escape(str(item["dimension"])), muted_style))
                    story.append(
                        Paragraph(
                            f"<b>{html.escape(m['common']['recommendation'])}</b> {html.escape(str(item['recommendation']))}",
                            body_style,
                        )
                    )
                    story.append(Spacer(1, 4))

        story.append(_divider())
        c = m["criteria"]
        story.append(Paragraph(m["sections"]["criteria_title"], heading_style))
        story.append(Paragraph(m["sections"]["criteria_intro"], body_style))
        story.append(Paragraph(c["visual_title"], heading_style))
        story.append(Paragraph(f"<b>{html.escape(c['wcag_143_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["wcag_143_detail"]), muted_style))
        story.append(Paragraph(f"<b>{html.escape(c['wcag_1411_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["wcag_1411_detail"]), muted_style))
        story.append(Paragraph(c["documents_title"], heading_style))
        story.append(Paragraph(f"<b>{html.escape(c['wcag2ict_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["wcag2ict_detail"]), muted_style))
        story.append(Paragraph(c["color_title"], heading_style))
        story.append(Paragraph(f"<b>{html.escape(c['brettel_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["brettel_detail"]), muted_style))
        story.append(Paragraph(f"<b>{html.escape(c['machado_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["machado_detail"]), muted_style))

        doc.build(story, onFirstPage=_draw_pdf_branding, onLaterPages=_draw_pdf_branding)
        return

    except Exception as exc:
        raise RuntimeError(f"No se pudo generar el PDF del informe: {exc}")


def render_report_text_master(payload: dict, lang: str) -> str:
    """Renderiza una versión TXT liviana y localizada del informe.

    Esta salida conserva la compatibilidad con el contrato del código base,
    que generaba TXT/JSON/HTML/PDF para cada variante.
    """
    m = _master(lang)
    summary = payload.get("summary", {}) or {}
    visual_metrics = payload.get("visual_metrics", {}) or {}
    totals = summary.get("totals", {}) or {}
    reportable_issue_count = int(totals.get("reportable_issue_count", totals.get("issue_count", 0)) or 0)
    has_issues = reportable_issue_count > 0

    lines: List[str] = [
        m["report_title"],
        "",
        str(summary.get("overview", "")),
        "",
        f"{m['estimated_reading_time']} {visual_metrics.get('estimated_read_time_human', 'unavailable')}",
        "",
        m["intro"] if has_issues else m["intro_no_issues"],
        "",
    ]

    for card in m.get("summary_blocks", []):
        lines.append(str(card.get("title", "")))
        lines.append(str(card.get("text", "")))
        lines.append("")

    if has_issues:
        lines.extend([
            m["sections"]["by_dimension_title"],
            m["sections"]["by_dimension_intro"],
            "",
        ])
        for section in build_dimension_recommendations_master(payload, lang):
            lines.append(str(section.get("dimension", "")))
            if section.get("summary"):
                lines.append(str(section.get("summary")))
            for item in section.get("items", []):
                units = _format_units_for_review_master(payload, item.get("units", []), lang)
                lines.append(f"- {item.get('metric', '-')}")
                lines.append(f"  {m['common']['recommendation']} {item.get('recommendation', '-')}")
                lines.append(f"  {units}")
            lines.append("")

        lines.extend([
            m["sections"]["by_slide_title"],
            m["sections"]["by_slide_intro"],
            "",
        ])
        for slide in build_slide_recommendations_summary_master(payload, lang):
            lines.append(str(slide.get("label", "")))
            for item in slide.get("items", []):
                lines.append(f"- {item.get('metric', '-')}")
                lines.append(f"  {item.get('dimension', '-')}")
                lines.append(f"  {m['common']['recommendation']} {item.get('recommendation', '-')}")
            lines.append("")

    c = m["criteria"]
    lines.extend([
        m["sections"]["criteria_title"],
        m["sections"]["criteria_intro"],
        "",
        c["visual_title"],
        f"- {c['wcag_143_title']}: {c['wcag_143_detail']}",
        f"- {c['wcag_1411_title']}: {c['wcag_1411_detail']}",
        "",
        c["documents_title"],
        f"- {c['wcag2ict_title']}: {c['wcag2ict_detail']}",
        "",
        c["color_title"],
        f"- {c['brettel_title']}: {c['brettel_detail']}",
        f"- {c['machado_title']}: {c['machado_detail']}",
    ])

    return "\n".join(lines).strip() + "\n"


def save_report_variants_master(
    payload: dict,
    stem: str,
    output_dir: Path,
    variant: str,
    lang: str,
) -> Dict[str, str]:
    txt_name = f"{stem}.{variant}.txt"
    json_name = f"{stem}.{variant}.json"
    html_name = f"{stem}.{variant}.html"
    pdf_name = f"{stem}.{variant}.pdf"

    txt_path = output_dir / txt_name
    json_path = output_dir / json_name
    html_path = output_dir / html_name
    pdf_path = output_dir / pdf_name

    html_content = render_report_html_master(
        payload=payload,
        title=_master(lang)["report_title"],
        lang=lang,
    )

    write_text(txt_path, render_report_text_master(payload, lang))
    write_json(json_path, payload)
    write_text(html_path, html_content)
    render_html_to_pdf_master(html_content, pdf_path, payload=payload, lang=lang)

    return {
        "txt": txt_name,
        "json": json_name,
        "html": html_name,
        "pdf": pdf_name,
    }

def _rt(lang: str, section: str, key: str = None):
    base = REPORT_I18N.get(lang, REPORT_I18N["es"])
    value = base.get(section, {})
    if key is None:
        return value
    return value.get(key, REPORT_I18N["es"].get(section, {}).get(key, key))



def _draw_pdf_branding(canvas, doc) -> None:
    try:
        from reportlab.lib.utils import ImageReader  # type: ignore
        from reportlab.lib.units import mm  # type: ignore

        assets = get_pdf_branding_assets()
        page_width, page_height = doc.pagesize

        # Logo superior izquierdo
        logo_path = assets.get("logo")
        if logo_path:
            logo_reader = ImageReader(str(logo_path))
            logo_width = PDF_LOGO_WIDTH_MM * mm
            logo_height = PDF_LOGO_HEIGHT_MM * mm
            logo_x = PDF_HEADER_LEFT_OFFSET_MM * mm
            logo_y = page_height - (PDF_HEADER_TOP_OFFSET_MM * mm) - logo_height
            canvas.drawImage(
                logo_reader,
                logo_x,
                logo_y,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto",
            )

        # Imagen inferior ancho completo
        bottom_path = assets.get("bottom")
        if bottom_path:
            bottom_reader = ImageReader(str(bottom_path))
            footer_height = PDF_FOOTER_HEIGHT_MM * mm
            footer_y = PDF_FOOTER_BOTTOM_OFFSET_MM * mm
            canvas.drawImage(
                bottom_reader,
                0,
                footer_y,
                width=page_width,
                height=footer_height,
                preserveAspectRatio=False,
                mask="auto",
            )

    except Exception:
        pass


def build_dimension_recommendations_html(payload: dict) -> str:
    sections = build_dimension_recommendations(payload)
    blocks = []

    for section in sections:
        items_html = []
        for item in section["items"]:
            units_text = _format_units_for_review(payload, item["units"])
            items_html.append(
                f"""
                <article class="card issue-card">
                  <div class="issue-location">{html.escape(str(item['metric']))}</div>
                  <div class="issue-recommendation"><strong>Recomendación:</strong> {html.escape(str(item['recommendation']))}</div>
                  <div class="issue-meta">{html.escape(units_text)}</div>
                </article>
                """
            )

        blocks.append(
            f"""
            <section class="section">
              <h2>{html.escape(str(section['dimension']))}</h2>
              {''.join(items_html)}
            </section>
            """
        )

    return "".join(blocks)


# ---------------------------------------------------------
# PDF branding
# trecho añadido o modificado
# ---------------------------------------------------------

def get_script_dir() -> Path:
    return Path(__file__).resolve().parent


def get_pdf_branding_assets() -> Dict[str, Optional[Path]]:
    script_dir = get_script_dir()
    logo_path = script_dir / PDF_HEADER_LOGO_NAME
    bottom_path = script_dir / PDF_FOOTER_IMAGE_NAME

    return {
        "logo": logo_path if logo_path.exists() else None,
        "bottom": bottom_path if bottom_path.exists() else None,
    }


# ---------------------------------------------------------
# Informe - Recomendaciones por Dimensión
# trecho añadido o modificado
# ---------------------------------------------------------


def _collect_unit_indexes_for_categories(payload: dict, category_codes: List[str]) -> List[int]:
    issues = _filter_reportable_issues(payload)
    unit_indexes = sorted({
        int(issue.get("unit_index"))
        for issue in issues
        if issue.get("category_code") in category_codes and issue.get("unit_index") is not None
    })
    return unit_indexes

def _format_units_for_review_i18n(payload: dict, unit_indexes: List[int], lang: str) -> str:
    if not unit_indexes:
        return _ui(lang, "no_slides_review")
    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    unit_label = _ui(lang, "pages_for_review") if document_type == "pdf" else _ui(lang, "slides_for_review")
    return f"{unit_label}: " + ", ".join(str(x) for x in unit_indexes)

def build_dimension_recommendations_i18n(payload: dict, lang: str) -> List[dict]:
    rec = _ri(lang, "recommendations")
    dim = _ri(lang, "dimension_summaries")

    return [
        {
            "dimension": _ui(lang, "dimension_legibility"),
            "summary": dim["legibility"],
            "items": [
                {
                    "metric": _ui(lang, "metric_font_size"),
                    "recommendation": rec["font_size"].format(min_font=SMALL_FONT_THRESHOLD_PT),
                    "units": _collect_unit_indexes_for_categories(payload, ["small_fonts"]),
                },
                {
                    "metric": _ui(lang, "metric_typography"),
                    "recommendation": rec["typography"],
                    "units": _collect_unit_indexes_for_categories(payload, ["font_family"]),
                },
                {
                    "metric": _ui(lang, "metric_line_spacing"),
                    "recommendation": rec["line_spacing"].format(min_spacing=MIN_LINE_SPACING),
                    "units": _collect_unit_indexes_for_categories(payload, ["line_spacing"]),
                },
                {
                    "metric": _ui(lang, "metric_text_excess"),
                    "recommendation": rec["text_excess"].format(max_words=MAX_WORDS_PER_UNIT),
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_words", "dense_text"]),
                },
            ],
        },
        {
            "dimension": _ui(lang, "dimension_contrast"),
            "summary": dim["contrast"],
            "items": [
                {
                    "metric": "Color",
                    "recommendation": rec["color"],
                    "units": _collect_unit_indexes_for_categories(payload, ["cvd_risk"]),
                },
                {
                    "metric": _ui(lang, "metric_contrast_level"),
                    "recommendation": rec["contrast"],
                    "units": _collect_unit_indexes_for_categories(payload, ["text_contrast", "figure_contrast"]),
                },
            ],
        },
        {
            "dimension": _ui(lang, "dimension_organization"),
            "summary": dim["organization"],
            "items": [
                {
                    "metric": _ui(lang, "metric_text_blocks"),
                    "recommendation": rec["text_blocks"].format(min_blocks=MIN_TEXT_BLOCKS),
                    "units": _collect_unit_indexes_for_categories(payload, ["insufficient_text_blocks"]),
                },
                {
                    "metric": _ui(lang, "metric_elements"),
                    "recommendation": rec["elements"].format(max_elements=MAX_ELEMENTS),
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_elements"]),
                },
            ],
        },
        {
            "dimension": _ui(lang, "dimension_images"),
            "summary": dim["images"],
            "items": [
                {
                    "metric": _ui(lang, "metric_alt_text"),
                    "recommendation": rec["alt_text"],
                    "units": _collect_unit_indexes_for_categories(payload, ["missing_alt_text"]),
                },
            ],
        },
    ]

def build_dimension_recommendations_html_i18n(payload: dict, lang: str) -> str:
    sections = build_dimension_recommendations_i18n(payload, lang=lang)
    blocks = []

    for section in sections:
        items_html = []
        for item in section["items"]:
            units_text = _format_units_for_review_i18n(payload, item["units"], lang)
            items_html.append(
                f"""
                <article class="card issue-card">
                  <div class="issue-location">{html.escape(str(item['metric']))}</div>
                  <div class="issue-recommendation"><strong>{html.escape(_ui(lang, "recommendation"))}</strong> {html.escape(str(item['recommendation']))}</div>
                  <div class="issue-meta">{html.escape(units_text)}</div>
                </article>
                """
            )

        blocks.append(
            f"""
            <section class="section">
              <h2>{html.escape(str(section['dimension']))}</h2>
              <p class="dimension-summary">{html.escape(str(section.get('summary', '')))}</p>
              {''.join(items_html)}
            </section>
            """
        )

    return "".join(blocks)

def build_slide_recommendations_summary_i18n(payload: dict, lang: str) -> List[dict]:
    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    unit_label = _ui(lang, "page") if document_type == "pdf" else _ui(lang, "slide")

    sections = build_dimension_recommendations_i18n(payload, lang=lang)
    per_unit: Dict[int, List[dict]] = {}

    for section in sections:
        dimension = section.get("dimension", "")
        for item in section.get("items", []):
            metric = item.get("metric", "")
            recommendation = item.get("recommendation", "")
            unit_indexes = _normalize_recommendation_units(item.get("units"))

            for unit_index in unit_indexes:
                per_unit.setdefault(unit_index, []).append(
                    {
                        "dimension": dimension,
                        "metric": metric,
                        "recommendation": recommendation,
                    }
                )

    result = []
    for unit_index in sorted(per_unit.keys()):
        result.append(
            {
                "unit_index": unit_index,
                "label": f"{unit_label} {unit_index}",
                "items": per_unit[unit_index],
            }
        )

    return result


def build_slide_recommendations_html_i18n(payload: dict, lang: str) -> str:
    slides = build_slide_recommendations_summary_i18n(payload, lang=lang)

    if not slides:
        return f"""
        <section class="section">
          <div class="card">
            <p>{html.escape(_ui(lang, "no_slides_review"))}</p>
          </div>
        </section>
        """

    blocks = []
    for slide in slides:
        item_html = []
        for item in slide["items"]:
            item_html.append(
                f"""
                <article class="slide-rec-item">
                  <div class="slide-rec-metric">{html.escape(str(item["metric"]))}</div>
                  <div class="slide-rec-dimension">{html.escape(str(item["dimension"]))}</div>
                  <div class="slide-rec-text"><strong>{html.escape(_ui(lang, "recommendation"))}</strong> {html.escape(str(item["recommendation"]))}</div>
                </article>
                """
            )

        blocks.append(
            f"""
            <section class="section">
              <div class="slide-summary-card">
                <h2>{html.escape(str(slide["label"]))}</h2>
                {''.join(item_html)}
              </div>
            </section>
            """
        )

    return "".join(blocks)

def build_fixed_criteria_section_html_i18n(lang: str) -> str:
    c = _ri(lang, "fixed_criteria")
    return f"""
    <section class="section">
      <h2>{html.escape(c['section_title'])}</h2>
      <div class="card">
        <p>{html.escape(c['intro'])}</p>

        <h3>{html.escape(c['visual_contrast_title'])}</h3>
        <p><strong>{html.escape(c['wcag_143_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['wcag_143_detail'])}</p>

        <p><strong>{html.escape(c['wcag_1411_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['wcag_1411_detail'])}</p>

        <h3>{html.escape(c['documents_title'])}</h3>
        <p><strong>{html.escape(c['wcag2ict_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['wcag2ict_detail'])}</p>

        <h3>{html.escape(c['color_title'])}</h3>
        <p><strong>{html.escape(c['brettel_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['brettel_detail'])}</p>

        <p><strong>{html.escape(c['machado_title'])}</strong></p>
        <p class="reference-detail">{html.escape(c['machado_detail'])}</p>
      </div>
    </section>
    """


def build_dimension_recommendations(payload: dict) -> List[dict]:
    return [
        {
            "dimension": "Dimensión Legibilidad",
            "items": [
                {
                    "metric": "Tamaño de letra",
                    "recommendation": f"Aumentar el tamaño de la letra  manteniendo, como referencia, un tamaño mínimo de {SMALL_FONT_THRESHOLD_PT:.0f}.",
                    "units": _collect_unit_indexes_for_categories(payload, ["small_fonts"]),
                },
                {
                    "metric": "Tipografía",
                    "recommendation": "Priorizar tipografías sans serif consistentes, especialmente en títulos, cuerpo y etiquetas.",
                    "units": _collect_unit_indexes_for_categories(payload, ["font_family"]),
                },
                {
                    "metric": "Interlineado",
                    "recommendation": f"Aumentar el espacio entre líneas manteniendo, como referencia, un interlineado mínimo de {MIN_LINE_SPACING:.2f} pts.",
                    "units": _collect_unit_indexes_for_categories(payload, ["line_spacing"]),
                },
                {
                    "metric": "Cantidad de texto",
                    "recommendation": f"Reduce la cantidad de texto por diapositiva o página cuando supere la referencia de  {MAX_WORDS_PER_UNIT} palabras.",
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_words", "dense_text"]),
                },
                {
                    "metric": "Color",
                    "recommendation": f"Revisar el uso de colores en las diapositivas para asegurar que la información sea distinguible para personas con diferentes tipos de visión del color. Evitar combinaciones que puedan generar confusión (por ejemplo, rojo/verde) y reforzar la información con otros recursos como texto, íconos o subrayados..",
                    "units": _collect_unit_indexes_for_categories(payload, ["cvd_risk"]),
                },
                {
                    "metric": "Contraste",
                    "recommendation": f"Mejorar el contraste entre el texto y el fondo para facilitar la lectura. En algunos casos, puede ser necesario ajustar los colores o reorganizar el contenido de la diapositiva.",
                    "units": _collect_unit_indexes_for_categories(payload, ["text_contrast"])
                },

            ],
        },
        {
            "dimension": "Dimensión organización del contenido ",
            "items": [
                {
                    "metric": "Jerarquia visual",
                    "recommendation": f"Segmentar el contenido organizando  cada diapositiva en, al menos, {MIN_TEXT_BLOCKS} bloques, cuando sea posible.",
                    "units": _collect_unit_indexes_for_categories(payload, ["insufficient_text_blocks"]),
                },
                {
                    "metric": "Cantidad de elementos",
                    "recommendation": f"Reducir la cantidad total de elementos por diapositiva manteniendo  un máximo de {MAX_ELEMENTS} elementos visibles.",
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_elements"]),
                },
            ],
        },
        {
            "dimension": "Dimensión uso de imágenes",
            "items": [
                {
                    "metric": "Texto alternativo (ALT)",
                    "recommendation": "Añadir texto alternativo a las imágenes relevantes para que puedan interpretarse con tecnologías de apoyo.",
                    "units": _collect_unit_indexes_for_categories(payload, ["missing_alt_text"]),
                },
            ],
        },
    ]


# ---------------------------------------------------------
# Tiempo estimado de lectura
# trecho añadido o modificado
# ---------------------------------------------------------

def estimate_unit_read_time_seconds(
        total_words: Optional[int],
        image_count: Optional[int],
        elements_count: Optional[int],
) -> Optional[float]:
    if total_words is None:
        return None

    total_words = int(total_words or 0)
    image_count = int(image_count or 0)
    elements_count = int(elements_count or 0)

    # 1) tiempo base por lectura de palabras
    time_words = (total_words / READING_WORDS_PER_MINUTE) * 60.0

    # 2) tiempo extra por imágenes
    time_images = image_count * SECONDS_PER_IMAGE

    # 3) penalización suave por complejidad visual
    extra_elements = max(elements_count - ELEMENTS_BASELINE, 0)
    time_elements = extra_elements * 1.0

    # 4) penalización suave por exceso de palabras
    extra_words = max(total_words - WORDS_BASELINE, 0)
    time_word_overload = extra_words * 0.10

    return round(time_words + time_images + time_elements + time_word_overload, 2)


def seconds_to_human_readable(seconds: Optional[float]) -> str:
    if seconds is None:
        return "unavailable"

    total_seconds = int(round(seconds))
    minutes = total_seconds // 60
    secs = total_seconds % 60

    if minutes == 0:
        return f"{secs} s"
    return f"{minutes} min {secs} s"


def minutes_decimal(seconds: Optional[float]) -> Optional[float]:
    if seconds is None:
        return None
    return round(float(seconds) / 60.0, 2)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_whitespace(text: str) -> str:
    text = str(text or "")
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\ufffe\uffff]", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
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


# ---------------------------------------------------------
# Informe - Resumen por diapositivas
# trecho añadido o modificado
# ---------------------------------------------------------

def _normalize_recommendation_units(units: Any) -> List[int]:
    if isinstance(units, list):
        out = []
        for value in units:
            try:
                out.append(int(value))
            except Exception:
                continue
        return sorted(set(out))
    return []


def build_slide_recommendations_summary(payload: dict) -> List[dict]:
    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    unit_label = "Página" if document_type == "pdf" else "Diapositiva"

    # Usa la misma fuente que ya alimenta "Recomendaciones por dimensión"
    sections = build_dimension_recommendations(payload)

    per_unit: Dict[int, List[dict]] = {}

    for section in sections:
        dimension = section.get("dimension", "")
        for item in section.get("items", []):
            metric = item.get("metric", "")
            recommendation = item.get("recommendation", "")
            unit_indexes = _normalize_recommendation_units(item.get("units"))

            for unit_index in unit_indexes:
                per_unit.setdefault(unit_index, []).append(
                    {
                        "dimension": dimension,
                        "metric": metric,
                        "recommendation": recommendation,
                    }
                )

    result = []
    for unit_index in sorted(per_unit.keys()):
        result.append(
            {
                "unit_index": unit_index,
                "label": f"{unit_label} {unit_index}",
                "items": per_unit[unit_index],
            }
        )

    return result


def build_slide_recommendations_html(payload: dict) -> str:
    slides = build_slide_recommendations_summary(payload)

    if not slides:
        return """
        <section class="section">
          <div class="card">
            <p>No se detectaron diapositivas con recomendaciones específicas para esta sección.</p>
          </div>
        </section>
        """

    blocks = []
    for slide in slides:
        item_html = []
        for item in slide["items"]:
            item_html.append(
                f"""
                <article class="slide-rec-item">
                  <div class="slide-rec-metric">{html.escape(str(item["metric"]))}</div>
                  <div class="slide-rec-dimension">{html.escape(str(item["dimension"]))}</div>
                  <div class="slide-rec-text"><strong>Recomendación:</strong> {html.escape(str(item["recommendation"]))}</div>
                </article>
                """
            )

        blocks.append(
            f"""
            <section class="section">
              <div class="slide-summary-card">
                <h2>{html.escape(str(slide["label"]))}</h2>
                {''.join(item_html)}
              </div>
            </section>
            """
        )

    return "".join(blocks)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_output_filenames(output_dir: Path) -> List[str]:
    return sorted([p.name for p in output_dir.iterdir() if p.is_file()])


def build_logger(output_dir: Path) -> logging.Logger:
    logger = logging.getLogger("aiuda_docs")
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


def detect_language_heuristic(text: str) -> str:
    text = normalize_whitespace(text).lower()
    if not text:
        return "es"

    sample = text[:4000]
    scores = {"es": 0, "en": 0, "pt": 0, "gl": 0}

    stopwords = {
        "es": [" el ", " la ", " de ", " que ", " y ", " en ", " los ", " las ", " para ", " con ", " una ", " por ",
               " del "],
        "en": [" the ", " and ", " of ", " to ", " in ", " for ", " with ", " on ", " this ", " that ", " is ",
               " are "],
        "pt": [" o ", " a ", " de ", " que ", " e ", " em ", " para ", " com ", " uma ", " os ", " as ", " do ", " da ",
               " não "],
        "gl": [" o ", " a ", " de ", " que ", " e ", " en ", " para ", " con ", " unha ", " os ", " as ", " do ",
               " da ", " non "],
    }

    padded = f" {sample} "
    for lang, words in stopwords.items():
        for word in words:
            scores[lang] += padded.count(word)

    if any(ch in sample for ch in "ñáéíóú¿¡"):
        scores["es"] += 2
    if any(ch in sample for ch in "ãõêçâô"):
        scores["pt"] += 3
    if " não " in padded:
        scores["pt"] += 3
    if " non " in padded:
        scores["gl"] += 3
    if " unha " in padded or " dende " in padded or " co " in padded:
        scores["gl"] += 2
    if " the " in padded or " this " in padded or " with " in padded:
        scores["en"] += 2

    return max(scores, key=scores.get)


def safe_round(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except Exception:
        return None


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def make_excerpt(text: str, max_chars: int = 220) -> str:
    text = normalize_whitespace(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalize_bbox(bbox: Any) -> Optional[List[float]]:
    if bbox is None:
        return None

    candidate = bbox
    if isinstance(candidate, dict) and "bbox" in candidate:
        candidate = candidate.get("bbox")

    if isinstance(candidate, (list, tuple)) and len(candidate) == 4:
        raw_values = list(candidate)
    elif all(hasattr(candidate, attr) for attr in ("x0", "y0", "x1", "y1")):
        raw_values = [getattr(candidate, "x0"), getattr(candidate, "y0"), getattr(candidate, "x1"),
                      getattr(candidate, "y1")]
    elif all(hasattr(candidate, attr) for attr in ("x", "y", "width", "height")):
        x = getattr(candidate, "x")
        y = getattr(candidate, "y")
        width = getattr(candidate, "width")
        height = getattr(candidate, "height")
        raw_values = [x, y, x + width, y + height]
    else:
        return None

    try:
        x0, y0, x1, y1 = [float(v) for v in raw_values]
        return [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)]
    except Exception:
        return None


def humanize_bbox(bbox: Optional[List[float]], page_rect: Optional[List[float]] = None) -> str:
    if not bbox:
        return "ubicación no disponible"

    if page_rect and len(page_rect) == 4:
        try:
            px0, py0, px1, py1 = page_rect
            width = max(float(px1) - float(px0), 1.0)
            height = max(float(py1) - float(py0), 1.0)
            x0, y0, x1, y1 = bbox
            cx = ((float(x0) + float(x1)) / 2.0 - float(px0)) / width
            cy = ((float(y0) + float(y1)) / 2.0 - float(py0)) / height

            if cx < 0.33:
                hz = "izquierda"
            elif cx > 0.67:
                hz = "derecha"
            else:
                hz = "centro"

            if cy < 0.33:
                vt = "superior"
            elif cy > 0.67:
                vt = "inferior"
            else:
                vt = "central"

            mapping = {
                ("superior", "izquierda"): "zona superior izquierda",
                ("superior", "centro"): "zona superior central",
                ("superior", "derecha"): "zona superior derecha",
                ("central", "izquierda"): "zona media izquierda",
                ("central", "centro"): "zona central",
                ("central", "derecha"): "zona media derecha",
                ("inferior", "izquierda"): "zona inferior izquierda",
                ("inferior", "centro"): "zona inferior central",
                ("inferior", "derecha"): "zona inferior derecha",
            }
            return mapping.get((vt, hz), "zona aproximada del documento")
        except Exception:
            pass

    return "ubicación aproximada disponible"


def clean_list_items(items: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for item in items:
        value = normalize_whitespace(str(item or ""))
        if value:
            out.append(value)
    return out


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR issue_sort_key(...)
# ---------------------------------------------------------

def issue_sort_key(issue: dict) -> Tuple[int, int, str, int]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}.get(issue.get("severity_code"), 3)
    category_rank = {
        "text_contrast": 0,
        "figure_contrast": 1,
        "cvd_risk": 2,
        "missing_alt_text": 3,
        "line_spacing": 4,
        "small_fonts": 5,
        "font_family": 5,
        "too_many_words": 6,
        "dense_text": 7,
        "insufficient_text_blocks": 8,
        "too_many_elements": 9,
        "metric_unavailable_pdf": 10,
        "no_text": 11,
        "processing_note": 99,
    }.get(issue.get("category_code"), 50)
    unit_index = int(issue.get("unit_index", 0) or 0)
    return (severity_rank, category_rank, str(issue.get("location", "")), unit_index)


# ----------------------


def classify_text_metric_status(ratio: Optional[float], threshold: Optional[float]) -> str:
    if ratio is None or threshold is None:
        return "sin dato"
    if ratio < threshold:
        return "incidencia"
    if ratio < threshold + 1.0:
        return "cercano al umbral"
    return "correcto"


def classify_figure_metric_status(ratio: Optional[float], threshold: Optional[float],
                                  worst_cvd_ratio: Optional[float]) -> str:
    if ratio is not None and threshold is not None and ratio < threshold:
        return "incidencia"
    if worst_cvd_ratio is not None and worst_cvd_ratio < 0.75:
        return "riesgo CVD"
    if ratio is not None and threshold is not None and ratio < threshold + 0.8:
        return "cercano al umbral"
    return "correcto"


def summarize_text_metrics(rows: List[dict]) -> dict:
    ratios = [float(row["ratio"]) for row in rows if row.get("ratio") is not None]
    estimated_count = sum(1 for row in rows if row.get("estimated"))
    below_count = sum(
        1
        for row in rows
        if row.get("ratio") is not None and row.get("threshold") is not None and float(row["ratio"]) < float(
            row["threshold"])
    )
    near_count = sum(
        1
        for row in rows
        if row.get("ratio") is not None
        and row.get("threshold") is not None
        and float(row["threshold"]) <= float(row["ratio"]) < float(row["threshold"]) + 1.0
    )
    return {
        "min_ratio": safe_round(min(ratios), 2) if ratios else None,
        "avg_ratio": safe_round(sum(ratios) / len(ratios), 2) if ratios else None,
        "estimated_count": estimated_count,
        "below_threshold_count": below_count,
        "near_threshold_count": near_count,
    }


def summarize_figure_metrics(rows: List[dict]) -> dict:
    ratios = [float(row["ratio"]) for row in rows if row.get("ratio") is not None]
    worst_scores = [float(row["worst_cvd_ratio"]) for row in rows if row.get("worst_cvd_ratio") is not None]
    worst_scores = [float(row["worst_cvd_ratio"]) for row in rows if row.get("worst_cvd_ratio") is not None]
    low_contrast_count = sum(
        1
        for row in rows
        if row.get("ratio") is not None and row.get("threshold") is not None and float(row["ratio"]) < float(
            row["threshold"])
    )
    cvd_risk_count = sum(
        1 for row in rows if row.get("worst_cvd_ratio") is not None and float(row["worst_cvd_ratio"]) < 0.75)
    return {
        "min_ratio": safe_round(min(ratios), 2) if ratios else None,
        "avg_ratio": safe_round(sum(ratios) / len(ratios), 2) if ratios else None,
        "min_cvd_ratio": safe_round(min(worst_scores), 3) if worst_scores else None,
        "low_contrast_count": low_contrast_count,
        "cvd_risk_count": cvd_risk_count,
    }


def select_text_metric_rows(rows: List[dict], max_rows: int = 8) -> List[dict]:
    if not rows:
        return []
    scored = []
    for row in rows:
        ratio = float(row.get("ratio") or 0.0)
        threshold = float(row.get("threshold") or 0.0)
        delta = ratio - threshold
        status = classify_text_metric_status(row.get("ratio"), row.get("threshold"))
        scored.append(
            (0 if ratio < threshold else 1 if delta < 1.0 else 2, delta, ratio, row.get("location", ""), row, status))
    scored.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    selected: List[dict] = []
    seen = set()
    for _bucket, _delta, _ratio, _location, row, status in scored:
        key = (row.get("location"), row.get("text_block_index"))
        if key in seen:
            continue
        seen.add(key)
        new_row = dict(row)
        new_row["status"] = status
        selected.append(new_row)
        if len(selected) >= max_rows:
            break
    return selected


def select_figure_metric_rows(rows: List[dict], max_rows: int = 8) -> List[dict]:
    if not rows:
        return []
    scored = []
    for row in rows:
        ratio = float(row.get("ratio") or 99.0) if row.get("ratio") is not None else 99.0
        threshold = float(row.get("threshold") or WCAG_NON_TEXT_RATIO)
        worst_cvd = float(row.get("worst_cvd_ratio") or 1.0) if row.get("worst_cvd_ratio") is not None else 1.0
        status = classify_figure_metric_status(row.get("ratio"), row.get("threshold"), row.get("worst_cvd_ratio"))
        bucket = 0 if (row.get("ratio") is not None and float(row.get(
            "ratio")) < threshold) or worst_cvd < 0.75 else 1 if ratio < threshold + 0.8 or worst_cvd < 0.9 else 2
        scored.append((bucket, worst_cvd, ratio, row.get("location", ""), row, status))
    scored.sort(key=lambda item: (item[0], item[1], item[2], item[3]))

    selected: List[dict] = []
    seen = set()
    for _bucket, _worst_cvd, _ratio, _location, row, status in scored:
        key = (row.get("location"), row.get("figure_index"))
        if key in seen:
            continue
        seen.add(key)
        new_row = dict(row)
        new_row["status"] = status
        selected.append(new_row)
        if len(selected) >= max_rows:
            break
    return selected


def build_metric_summary_lines(summary: dict, kind: str) -> List[str]:
    if not summary:
        return []
    if kind == "text":
        return [
            f"Mínimo observado: {summary['min_ratio']}:1" if summary.get(
                "min_ratio") is not None else "Mínimo observado: -",
            f"Media observada: {summary['avg_ratio']}:1" if summary.get(
                "avg_ratio") is not None else "Media observada: -",
            f"Por debajo del umbral: {summary.get('below_threshold_count', 0)}",
            f"Cercanos al umbral: {summary.get('near_threshold_count', 0)}",
            f"Estimados por rasterización: {summary.get('estimated_count', 0)}",
        ]
    return [
        f"Mínimo de contraste observado: {summary['min_ratio']}:1" if summary.get(
            "min_ratio") is not None else "Mínimo de contraste observado: -",
        f"Media observada: {summary['avg_ratio']}:1" if summary.get("avg_ratio") is not None else "Media observada: -",
        f"Figuras bajo umbral: {summary.get('low_contrast_count', 0)}",
        f"Peor score CVD: {summary['min_cvd_ratio']}" if summary.get(
            "min_cvd_ratio") is not None else "Peor score CVD: -",
        f"Figuras con riesgo CVD: {summary.get('cvd_risk_count', 0)}",
    ]


def rgb_to_hex(rgb: Optional[Tuple[int, int, int]]) -> Optional[str]:
    if not rgb:
        return None
    try:
        r, g, b = [int(clamp(float(c), 0, 255)) for c in rgb]
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return None


def normalize_rgb(value: Any) -> Optional[Tuple[int, int, int]]:
    if value is None:
        return None
    if isinstance(value, tuple) and len(value) == 3:
        try:
            return tuple(int(clamp(float(c), 0, 255)) for c in value)
        except Exception:
            return None
    if hasattr(value, "rgb") and getattr(value, "rgb", None) is not None:
        value = getattr(value, "rgb")
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        data = list(value)
        if len(data) >= 3:
            try:
                return tuple(int(clamp(float(c), 0, 255)) for c in data[:3])
            except Exception:
                return None
    if isinstance(value, int):
        try:
            return ((value >> 16) & 255, (value >> 8) & 255, value & 255)
        except Exception:
            return None
    if isinstance(value, str):
        val = value.strip().lstrip("#")
        if len(val) == 6:
            try:
                return (int(val[0:2], 16), int(val[2:4], 16), int(val[4:6], 16))
            except Exception:
                return None
    return None


def int_to_rgb(color_int: Any) -> Optional[Tuple[int, int, int]]:
    try:
        color_int = int(color_int)
    except Exception:
        return None
    return ((color_int >> 16) & 255, (color_int >> 8) & 255, color_int & 255)


def srgb_to_linear_channel(channel: float) -> float:
    channel = clamp(channel / 255.0, 0.0, 1.0)
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    r_lin = srgb_to_linear_channel(r)
    g_lin = srgb_to_linear_channel(g)
    b_lin = srgb_to_linear_channel(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(rgb_a: Tuple[int, int, int], rgb_b: Tuple[int, int, int]) -> float:
    la = relative_luminance(rgb_a)
    lb = relative_luminance(rgb_b)
    lighter = max(la, lb)
    darker = min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def infer_severity_for_ratio(ratio: float, threshold: float) -> str:
    if ratio >= threshold:
        return "low"
    if ratio >= threshold * 0.8:
        return "medium"
    return "high"


def severity_label(code: str) -> str:
    return {"low": "baja", "medium": "media", "high": "alta"}.get(code, code)


def is_large_text(size_pt: Optional[float]) -> bool:
    return bool(size_pt is not None and size_pt >= SMALL_FONT_THRESHOLD_PT)


def average_color(colors: List[Tuple[int, int, int]], weights: Optional[List[float]] = None) -> Optional[
    Tuple[int, int, int]]:
    if not colors:
        return None
    if weights and len(weights) == len(colors):
        total = float(sum(max(w, 0.0) for w in weights)) or 1.0
        r = sum(c[0] * max(w, 0.0) for c, w in zip(colors, weights)) / total
        g = sum(c[1] * max(w, 0.0) for c, w in zip(colors, weights)) / total
        b = sum(c[2] * max(w, 0.0) for c, w in zip(colors, weights)) / total
    else:
        r = sum(c[0] for c in colors) / len(colors)
        g = sum(c[1] for c in colors) / len(colors)
        b = sum(c[2] for c in colors) / len(colors)
    return (int(round(r)), int(round(g)), int(round(b)))


def get_optional_numpy():
    try:
        import numpy as np  # type: ignore

        return np
    except Exception:
        return None


def get_optional_pil_image():
    try:
        from PIL import Image  # type: ignore

        return Image
    except Exception:
        return None


def scale_image_if_needed(image: Any, max_side: int = MAX_RENDER_SIDE) -> Any:
    width, height = getattr(image, "size", (0, 0))
    if not width or not height:
        return image
    current_max = max(width, height)
    if current_max <= max_side:
        return image
    ratio = max_side / float(current_max)
    target = (max(1, int(width * ratio)), max(1, int(height * ratio)))
    try:
        return image.resize(target)
    except Exception:
        return image


def pil_image_from_bytes(blob: Optional[bytes]) -> Any:
    if not blob:
        return None
    Image = get_optional_pil_image()
    if Image is None:
        return None
    try:
        image = Image.open(io.BytesIO(blob))
        image.load()
        if image.mode != "RGB":
            image = image.convert("RGB")
        return scale_image_if_needed(image)
    except Exception:
        return None


def pil_image_from_pixmap(pixmap: Any) -> Any:
    Image = get_optional_pil_image()
    if Image is None or pixmap is None:
        return None
    try:
        mode = "RGBA" if getattr(pixmap, "alpha", False) else "RGB"
        image = Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return scale_image_if_needed(image)
    except Exception:
        return None


def image_to_palette(image: Any, color_count: int = 6) -> List[dict]:
    Image = get_optional_pil_image()
    np = get_optional_numpy()
    if image is None or Image is None or np is None:
        return []

    try:
        small = image.convert("RGB")
        small.thumbnail((180, 180))
        quantized = small.quantize(colors=color_count, method=Image.MEDIANCUT)
        palette = quantized.getpalette() or []
        color_counts = quantized.getcolors() or []
        total = float(sum(count for count, _ in color_counts) or 1)
        out: List[dict] = []
        for count, color_idx in sorted(color_counts, reverse=True):
            pos = color_idx * 3
            rgb = tuple(int(v) for v in palette[pos:pos + 3])
            if len(rgb) == 3:
                out.append(
                    {
                        "rgb": rgb,
                        "hex": rgb_to_hex(rgb),
                        "weight": round(count / total, 4),
                    }
                )
        return out[:color_count]
    except Exception:
        return []


def simulate_cvd_rgb(rgb: Tuple[int, int, int], deficiency: str) -> Tuple[int, int, int]:
    matrix = CVD_MATRICES.get(deficiency)
    if matrix is None:
        return rgb
    r, g, b = [c / 255.0 for c in rgb]
    r2 = matrix[0][0] * r + matrix[0][1] * g + matrix[0][2] * b
    g2 = matrix[1][0] * r + matrix[1][1] * g + matrix[1][2] * b
    b2 = matrix[2][0] * r + matrix[2][1] * g + matrix[2][2] * b
    return (
        int(round(clamp(r2, 0.0, 1.0) * 255)),
        int(round(clamp(g2, 0.0, 1.0) * 255)),
        int(round(clamp(b2, 0.0, 1.0) * 255)),
    )


def weighted_average_pairwise_distance(palette: List[dict], deficiency: Optional[str] = None) -> float:
    if len(palette) < 2:
        return 0.0
    total_weight = 0.0
    total_distance = 0.0
    for i in range(len(palette)):
        rgb_i = palette[i]["rgb"]
        if deficiency:
            rgb_i = simulate_cvd_rgb(rgb_i, deficiency)
        for j in range(i + 1, len(palette)):
            rgb_j = palette[j]["rgb"]
            if deficiency:
                rgb_j = simulate_cvd_rgb(rgb_j, deficiency)
            weight = max(float(palette[i].get("weight", 0.0)), 0.0) * max(float(palette[j].get("weight", 0.0)), 0.0)
            if weight <= 0:
                continue
            distance = math.sqrt(
                (rgb_i[0] - rgb_j[0]) ** 2 + (rgb_i[1] - rgb_j[1]) ** 2 + (rgb_i[2] - rgb_j[2]) ** 2
            )
            total_distance += distance * weight
            total_weight += weight
    if total_weight <= 0:
        return 0.0
    return total_distance / total_weight


def estimate_clip_contrast(image: Any) -> Optional[dict]:
    np = get_optional_numpy()
    if image is None or np is None:
        return None
    try:
        image = scale_image_if_needed(image, max_side=240).convert("RGB")
        arr = np.asarray(image, dtype=np.uint8)
        flat = arr.reshape(-1, 3)
        if len(flat) < 16:
            return None
        luminance = np.array([relative_luminance((int(r), int(g), int(b))) for r, g, b in flat])
        if luminance.size == 0:
            return None
        lower_thr = float(np.quantile(luminance, 0.15))
        upper_thr = float(np.quantile(luminance, 0.85))
        darker_pixels = flat[luminance <= lower_thr]
        lighter_pixels = flat[luminance >= upper_thr]
        if len(darker_pixels) == 0 or len(lighter_pixels) == 0:
            return None
        fg = tuple(int(round(v)) for v in darker_pixels.mean(axis=0))
        bg = tuple(int(round(v)) for v in lighter_pixels.mean(axis=0))
        ratio = contrast_ratio(fg, bg)
        return {
            "foreground_rgb": fg,
            "background_rgb": bg,
            "contrast_ratio": ratio,
            "estimated": True,
        }
    except Exception:
        return None


def assess_text_block_contrast(text_block: dict, unit: dict) -> Optional[dict]:
    block_font = normalize_rgb(text_block.get("font_color"))
    block_bg = normalize_rgb(text_block.get("background_color"))
    size_pt = safe_round(text_block.get("size_pt"), 1)
    threshold = WCAG_LARGE_TEXT_RATIO if is_large_text(size_pt) else WCAG_NORMAL_TEXT_RATIO

    if block_font and block_bg:
        ratio = contrast_ratio(block_font, block_bg)
        return {
            "ratio": ratio,
            "threshold": threshold,
            "estimated": False,
            "foreground_rgb": block_font,
            "background_rgb": block_bg,
            "size_pt": size_pt,
        }

    render_meta = text_block.get("rendered_contrast") or {}
    fg = normalize_rgb(render_meta.get("foreground_rgb"))
    bg = normalize_rgb(render_meta.get("background_rgb"))
    ratio = render_meta.get("contrast_ratio")
    if ratio is not None and fg and bg:
        return {
            "ratio": float(ratio),
            "threshold": threshold,
            "estimated": True,
            "foreground_rgb": fg,
            "background_rgb": bg,
            "size_pt": size_pt,
        }
    return None


def analyze_figure_visuals(figure: dict) -> Optional[dict]:
    image = figure.get("image")
    if image is None:
        return None
    palette = image_to_palette(image, color_count=6)
    clip_contrast = estimate_clip_contrast(image)
    contrast_val = clip_contrast.get("contrast_ratio") if clip_contrast else None
    base_distance = weighted_average_pairwise_distance(palette)
    cvd_results: Dict[str, dict] = {}
    worst_ratio = 1.0
    worst_type = None
    for deficiency in ("protanopia", "deuteranopia", "tritanopia"):
        transformed_distance = weighted_average_pairwise_distance(palette, deficiency=deficiency)
        ratio = transformed_distance / base_distance if base_distance > 0 else 1.0
        worst_ratio = min(worst_ratio, ratio)
        if worst_type is None or ratio == worst_ratio:
            worst_type = deficiency
        if ratio < 0.55:
            risk_level = "high"
        elif ratio < 0.75:
            risk_level = "medium"
        else:
            risk_level = "low"
        cvd_results[deficiency] = {
            "score_ratio": safe_round(ratio, 3),
            "risk_code": risk_level,
            "risk": severity_label(risk_level),
        }

    non_text_severity = "low"
    if contrast_val is not None:
        non_text_severity = infer_severity_for_ratio(float(contrast_val), WCAG_NON_TEXT_RATIO)

    color_dependency = "moderada"
    if base_distance > 100 and worst_ratio < 0.7:
        color_dependency = "alta"
    elif base_distance < 45:
        color_dependency = "baja"

    return {
        "contrast_ratio": safe_round(contrast_val, 2),
        "non_text_threshold": WCAG_NON_TEXT_RATIO,
        "non_text_severity_code": non_text_severity,
        "non_text_severity": severity_label(non_text_severity),
        "palette": palette,
        "cvd": cvd_results,
        "worst_cvd_ratio": safe_round(worst_ratio, 3),
        "worst_cvd_type": worst_type,
        "color_dependency": color_dependency,
        "estimated": True,
    }


def render_pdf_block_contrast_estimates(unit: dict, logger: logging.Logger) -> None:
    page_ref = unit.get("_page_ref")
    fitz_module = unit.get("_fitz_module")
    if page_ref is None or fitz_module is None:
        return
    blocks = unit.get("text_blocks", []) or []
    if not blocks:
        return

    for block in blocks:
        bbox = block.get("bbox")
        if not bbox:
            continue
        try:
            rect = fitz_module.Rect(*bbox)
            matrix = fitz_module.Matrix(1.8, 1.8)
            pix = page_ref.get_pixmap(matrix=matrix, clip=rect, alpha=False)
            image = pil_image_from_pixmap(pix)
            if image is None:
                continue
            contrast_data = estimate_clip_contrast(image)
            if contrast_data:
                block["rendered_contrast"] = contrast_data
        except Exception as exc:
            logger.debug("No se pudo estimar el contraste renderizado del bloque %s: %s", bbox, exc)


def paragraph_lengths(text: str) -> List[int]:
    paragraphs = [p.strip() for p in re.split(r"\n+", normalize_whitespace(text)) if p.strip()]
    return [count_words(p) for p in paragraphs]


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# ---------------------------------------------------------

def build_pdf_extension_hint(unavailable_metrics: List[str]) -> str:
    unavailable_metrics = [normalize_whitespace(x) for x in unavailable_metrics if normalize_whitespace(x)]
    if not unavailable_metrics:
        return ""
    metrics_txt = ", ".join(unavailable_metrics)
    return (
        f"No fue posible verificar con fiabilidad las siguientes métricas en este PDF: {metrics_txt}. "
        "Para extender el analisis actual, considera utilizar el formato pptx."
    )


def friendly_units_label(document_type: str) -> str:
    return "páginas" if document_type == "pdf" else "diapositivas"


def normalize_font_name(font_name: Optional[str]) -> str:
    if not font_name:
        return ""

    fn = str(font_name).strip().lower()

    # Quitar prefijo de subset típico de PDF: ABCDEF+FontName
    fn = re.sub(r"^[a-z0-9]{6}\+", "", fn, flags=re.IGNORECASE)

    # Eliminar separadores y espacios
    fn = fn.replace("-", "")
    fn = fn.replace("_", "")
    fn = fn.replace(" ", "")
    fn = fn.replace(",", "")
    fn = fn.replace(".", "")

    # Quitar sufijos frecuentes de estilo / PostScript
    suffixes = [
        "regular", "bold", "italic", "oblique",
        "medium", "light", "semibold", "demibold",
        "extrabold", "black", "condensed", "narrow",
        "psmt", "mt", "ps", "std",
    ]

    changed = True
    while changed:
        changed = False
        for suf in suffixes:
            if fn.endswith(suf) and len(fn) > len(suf) + 2:
                fn = fn[:-len(suf)]
                changed = True

    return fn


def classify_font_basic(font_name: Optional[str]) -> str:
    if not font_name:
        return "unknown"

    raw = str(font_name).strip().lower()
    norm = normalize_font_name(font_name)

    # 1) match exacto
    if norm in FONT_SANS_ALIASES:
        return "sans"
    if norm in FONT_SERIF_ALIASES:
        return "serif"

    # 2) match por substring normalizado
    for alias in FONT_SANS_ALIASES:
        if alias and alias in norm:
            return "sans"

    for alias in FONT_SERIF_ALIASES:
        if alias and alias in norm:
            return "serif"

    # 3) fallback sobre nombre crudo compactado
    raw_compact = raw.replace("-", "").replace("_", "").replace(" ", "").replace(",", "").replace(".", "")
    for alias in FONT_SANS_ALIASES:
        if alias and alias in raw_compact:
            return "sans"

    for alias in FONT_SERIF_ALIASES:
        if alias and alias in raw_compact:
            return "serif"

    return "unknown"


def evaluate_sans_serif_compliance(accessibility_meta: dict, document_type: str) -> dict:
    sans_words = int(accessibility_meta.get("sans_words", 0) or 0)
    serif_words = int(accessibility_meta.get("serif_words", 0) or 0)
    unknown_words = int(accessibility_meta.get("unknown_words", 0) or 0)
    font_name_counts = accessibility_meta.get("font_name_counts", {}) or {}

    total_font_words = sans_words + serif_words + unknown_words
    known_words = sans_words + serif_words

    known_ratio = (known_words / total_font_words) if total_font_words > 0 else 0.0
    sans_ratio_known = (sans_words / known_words) if known_words > 0 else None
    serif_ratio_known = (serif_words / known_words) if known_words > 0 else None

    if total_font_words == 0:
        status = "unavailable"
    elif known_ratio < FONT_MIN_KNOWN_WORD_RATIO:
        status = "unavailable" if document_type == "pdf" else "partial"
    elif serif_ratio_known is not None and serif_ratio_known >= FONT_SERIF_NONCOMPLIANCE_RATIO:
        status = "no"
    elif sans_ratio_known is not None and sans_ratio_known >= FONT_SANS_COMPLIANCE_RATIO:
        status = "yes"
    else:
        status = "partial"

    examples = [name for name, _count in
                sorted(font_name_counts.items(), key=lambda item: item[1], reverse=True)[:MAX_FONT_EXAMPLES]]

    return {
        "status": status,
        "known_ratio": round(known_ratio, 3),
        "sans_ratio_known": round(sans_ratio_known, 3) if sans_ratio_known is not None else None,
        "serif_ratio_known": round(serif_ratio_known, 3) if serif_ratio_known is not None else None,
        "examples": examples,
    }


def yes_no_unavailable(value: Optional[bool]) -> str:
    if value is None:
        return "unavailable"
    return "yes" if bool(value) else "no"


def fmt_csv_value(value: Any, digits: int = 3) -> Any:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return round(value, digits)
    return value


def extract_pptx_alt_text(shape: Any) -> Tuple[str, str, bool]:
    descr = ""
    title = ""
    try:
        nodes = shape.element.xpath("./p:nvPicPr/p:cNvPr", namespaces=PPTX_NS)
        if not nodes:
            nodes = shape.element.xpath(".//p:cNvPr[1]", namespaces=PPTX_NS)
        if nodes:
            cNvPr = nodes[0]
            descr = (cNvPr.get("descr") or "").strip()
            title = (cNvPr.get("title") or "").strip()
    except Exception:
        pass
    return descr, title, bool(descr or title)


def paragraph_line_spacing_ratio_pptx(paragraph: Any, fallback_size_pt: float = 18.0) -> Optional[float]:
    text = normalize_whitespace("".join(getattr(run, "text", "") for run in getattr(paragraph, "runs", [])))
    if not text:
        return None

    try:
        line_spacing = paragraph.line_spacing
    except Exception:
        line_spacing = None

    if line_spacing is None:
        return 1.0

    if isinstance(line_spacing, float):
        return float(line_spacing)

    try:
        sizes = []
        for run in getattr(paragraph, "runs", []):
            if not normalize_whitespace(getattr(run, "text", "")):
                continue
            size = getattr(getattr(run, "font", None), "size", None)
            if size is not None:
                sizes.append(float(size.pt))
        font_pt = sum(sizes) / len(sizes) if sizes else fallback_size_pt
        spacing_pt = float(line_spacing.pt)
        return spacing_pt / font_pt if font_pt > 0 else None
    except Exception:
        return None


def estimate_pdf_min_line_spacing_ratio(block: dict) -> Optional[float]:
    lines_meta = []

    for line in block.get("lines", []):
        spans = line.get("spans", [])
        line_text = normalize_whitespace("".join(span.get("text", "") for span in spans))
        if not line_text:
            continue

        sizes = [float(span.get("size", 0)) for span in spans if normalize_whitespace(span.get("text", ""))]
        baselines = []
        for span in spans:
            origin = span.get("origin")
            if origin and len(origin) >= 2:
                baselines.append(float(origin[1]))

        if not sizes:
            continue

        line_size = median(sizes)
        baseline_y = median(baselines) if baselines else float(line["bbox"][3])
        lines_meta.append((baseline_y, line_size))

    if len(lines_meta) < 2:
        return None

    lines_meta.sort(key=lambda x: x[0])
    ratios = []

    for i in range(len(lines_meta) - 1):
        y1, s1 = lines_meta[i]
        y2, _ = lines_meta[i + 1]
        if s1 <= 0:
            continue
        dy = y2 - y1
        ratio = dy / s1
        if 0 < ratio < 5:
            ratios.append(ratio)

    return min(ratios) if ratios else None


# -----------------------------------


# ---------------------------------------------------------
# EXTRACTION
# ---------------------------------------------------------

# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# ---------------------------------------------------------

def extract_pdf_units(input_file: Path, use_ocr: bool, logger: logging.Logger) -> List[dict]:
    from pypdf import PdfReader

    logger.info("Extrayendo texto de PDF: %s", input_file.name)
    reader = PdfReader(str(input_file))
    units: List[dict] = []

    fitz_module = None
    try:
        import fitz as _fitz  # type: ignore
        fitz_module = _fitz
    except Exception:
        fitz_module = None

    fitz_doc = None
    if fitz_module:
        try:
            fitz_doc = fitz_module.open(str(input_file))
        except Exception:
            fitz_doc = None

    for idx, page in enumerate(reader.pages, start=1):
        font_name_counts = Counter()
        text = normalize_whitespace(page.extract_text() or "")
        notes: List[str] = []
        text_blocks: List[dict] = []
        figures: List[dict] = []
        page_rect: Optional[List[float]] = None

        min_line_spacing = None
        bullet_like_count = 0
        sans_words = 0
        serif_words = 0
        unknown_words = 0

        fitz_page = None
        if fitz_doc is not None:
            try:
                fitz_page = fitz_doc[idx - 1]
                page_rect = normalize_bbox(fitz_page.rect)
                page_dict = fitz_page.get_text("dict")
                structured_texts: List[str] = []

                for block_idx, block in enumerate(page_dict.get("blocks", []), start=1):
                    block_type = int(block.get("type", 0) or 0)
                    bbox = normalize_bbox(block.get("bbox"))

                    if block_type == 0:
                        block_texts: List[str] = []
                        span_sizes: List[float] = []
                        span_colors: List[Tuple[int, int, int]] = []

                        block_spacing = estimate_pdf_min_line_spacing_ratio(block)
                        if block_spacing is not None:
                            min_line_spacing = block_spacing if min_line_spacing is None else min(min_line_spacing,
                                                                                                  block_spacing)

                        for line in block.get("lines", []):
                            line_text = normalize_whitespace(
                                "".join(span.get("text", "") for span in line.get("spans", [])))
                            if line_text and BULLET_RE.match(line_text):
                                bullet_like_count += 1

                            for span in line.get("spans", []):
                                span_text = normalize_whitespace(span.get("text", ""))
                                if not span_text:
                                    continue

                                structured_texts.append(span_text)
                                block_texts.append(span_text)

                                size_val = safe_round(span.get("size"), 1)
                                if size_val is not None:
                                    span_sizes.append(size_val)

                                rgb = int_to_rgb(span.get("color"))
                                if rgb:
                                    span_colors.append(rgb)

                                raw_font_name = span.get("font")
                                wc = count_words(span_text)
                                font_kind = classify_font_basic(raw_font_name)

                                if raw_font_name:
                                    font_name_counts[str(raw_font_name).strip()] += wc

                                if font_kind == "sans":
                                    sans_words += wc
                                elif font_kind == "serif":
                                    serif_words += wc
                                else:
                                    unknown_words += wc

                        joined = normalize_whitespace(" ".join(block_texts))
                        if joined:
                            text_blocks.append(
                                {
                                    "text_block_index": block_idx,
                                    "text": joined,
                                    "bbox": bbox,
                                    "size_pt": safe_round(sum(span_sizes) / len(span_sizes), 1) if span_sizes else None,
                                    "font_color": average_color(span_colors),
                                    "background_color": None,
                                    "source": "pdf_structured_block",
                                }
                            )

                    elif block_type == 1:
                        figures.append(
                            {
                                "figure_index": len(figures) + 1,
                                "location": f"Página {idx} · figura {len(figures) + 1}",
                                "bbox": bbox,
                                "image": None,
                                "notes": ["Figura detectada en PDF mediante bloque gráfico."],
                            }
                        )

                if not text and structured_texts:
                    text = normalize_whitespace("\n\n".join(structured_texts))

            except Exception as exc:
                logger.warning("No se pudo extraer estructura avanzada de la página %s: %s", idx, exc)

        if not text and fitz_doc is not None:
            try:
                text = normalize_whitespace(fitz_doc[idx - 1].get_text("text") or "")
            except Exception:
                pass

        if fitz_doc is not None and fitz_page is not None:
            try:
                seen_rects = set()
                for image_info in fitz_page.get_images(full=True):
                    xref = image_info[0]
                    rects = fitz_page.get_image_rects(xref) or []
                    image_blob = None
                    try:
                        extracted = fitz_doc.extract_image(xref)
                        image_blob = extracted.get("image") if extracted else None
                    except Exception:
                        image_blob = None

                    for rect in rects:
                        bbox = normalize_bbox(rect)
                        key = tuple(bbox or [])
                        if key in seen_rects:
                            continue
                        seen_rects.add(key)
                        figures.append(
                            {
                                "figure_index": len(figures) + 1,
                                "location": f"Página {idx} · figura {len(figures) + 1}",
                                "bbox": bbox,
                                "image": pil_image_from_bytes(image_blob),
                                "notes": [],
                            }
                        )
            except Exception as exc:
                notes.append(f"No se pudieron aislar todas las figuras incrustadas del PDF: {exc}")

        if fitz_doc is not None and fitz_page is not None and text_blocks:
            unit_stub = {"_page_ref": fitz_page, "_fitz_module": fitz_module, "text_blocks": text_blocks}
            render_pdf_block_contrast_estimates(unit_stub, logger=logger)

        if use_ocr and not text:
            notes.append("No se ha aplicado OCR porque no hay un motor OCR configurado en este pipeline.")

        units.append(
            {
                "unit_type": "page",
                "unit_index": idx,
                "label": f"Página {idx}",
                "title": f"Página {idx}",
                "text": text,
                "text_blocks": text_blocks,
                "figures": figures,
                "small_font_hits": [],
                "notes": notes,
                "page_rect": page_rect,
                "accessibility_meta": {
                    "min_line_spacing": min_line_spacing,
                    "paragraph_count": len(text_blocks),
                    "bullet_like_count": bullet_like_count,
                    "text_blocks_count": len(text_blocks),
                    "elements_count": len(text_blocks) + bullet_like_count + len(figures),
                    "sans_words": sans_words,
                    "font_name_counts": dict(font_name_counts),
                    "serif_words": serif_words,
                    "unknown_words": unknown_words,
                    "missing_alt_text_count": None,
                    "image_count": len(figures),
                    "total_words": count_words(text) if text else None,
                    "total_chars": len(text) if text else None,
                },
            }
        )

    return units


# ------------------------------


def _convert_ppt_to_pptx(input_file: Path, logger: logging.Logger) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            "No se encontró LibreOffice/soffice para convertir .ppt a .pptx. "
            "Convierte el archivo a .pptx o instala LibreOffice en el servidor."
        )

    tmp_dir = Path(tempfile.mkdtemp(prefix="aluda_ppt_convert_"))
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pptx",
        "--outdir",
        str(tmp_dir),
        str(input_file),
    ]
    logger.info("Convirtiendo PPT a PPTX con LibreOffice")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"No se pudo convertir el PPT: {proc.stderr.strip() or proc.stdout.strip()}")

    candidates = list(tmp_dir.glob("*.pptx"))
    if not candidates:
        raise RuntimeError("La conversión de PPT a PPTX no generó ningún archivo de salida.")
    return candidates[0]


def get_ppt_fill_rgb(fill: Any) -> Optional[Tuple[int, int, int]]:
    if fill is None:
        return None
    try:
        fore = getattr(fill, "fore_color", None)
        if fore is not None and getattr(fore, "rgb", None) is not None:
            return normalize_rgb(fore.rgb)
    except Exception:
        return None
    return None


def get_shape_background_color(shape: Any, default_bg: Optional[Tuple[int, int, int]]) -> Optional[
    Tuple[int, int, int]]:
    try:
        fill = getattr(shape, "fill", None)
        rgb = get_ppt_fill_rgb(fill)
        if rgb:
            return rgb
    except Exception:
        pass
    return default_bg


def get_run_font_color(run: Any, fallback: Optional[Tuple[int, int, int]]) -> Optional[Tuple[int, int, int]]:
    try:
        color = getattr(getattr(run, "font", None), "color", None)
        if color is not None and getattr(color, "rgb", None) is not None:
            rgb = normalize_rgb(color.rgb)
            if rgb:
                return rgb
    except Exception:
        pass
    return fallback


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# ---------------------------------------------------------

def extract_pptx_units(input_file: Path, logger: logging.Logger) -> List[dict]:
    from pptx import Presentation

    font_name_counts = Counter()

    logger.info("Extrayendo texto de presentación: %s", input_file.name)
    prs = Presentation(str(input_file))
    units: List[dict] = []
    slide_width = float(getattr(prs, "slide_width", 0) or 0)
    slide_height = float(getattr(prs, "slide_height", 0) or 0)

    for idx, slide in enumerate(prs.slides, start=1):
        texts: List[str] = []
        title_text = ""
        small_font_hits: List[dict] = []
        text_blocks: List[dict] = []
        figures: List[dict] = []
        notes: List[str] = []

        min_line_spacing = None
        paragraph_count = 0
        bullet_like_count = 0
        sans_words = 0
        serif_words = 0
        unknown_words = 0
        missing_alt_text_count = 0

        slide_bg = (255, 255, 255)
        try:
            bg_fill = getattr(slide.background, "fill", None)
            slide_bg = get_ppt_fill_rgb(bg_fill) or slide_bg
        except Exception:
            slide_bg = (255, 255, 255)

        for shape_idx, shape in enumerate(slide.shapes, start=1):
            bbox = normalize_bbox([
                float(getattr(shape, "left", 0) or 0),
                float(getattr(shape, "top", 0) or 0),
                float((getattr(shape, "left", 0) or 0) + (getattr(shape, "width", 0) or 0)),
                float((getattr(shape, "top", 0) or 0) + (getattr(shape, "height", 0) or 0)),
            ])

            if getattr(shape, "has_text_frame", False) and shape.text_frame is not None:
                raw_text = normalize_whitespace(shape.text_frame.text)
                if raw_text:
                    texts.append(raw_text)
                try:
                    if slide.shapes.title is shape and raw_text:
                        title_text = raw_text
                except Exception:
                    pass

                block_bg = get_shape_background_color(shape, slide_bg)
                run_sizes: List[float] = []
                run_colors: List[Tuple[int, int, int]] = []
                block_text_parts: List[str] = []

                for paragraph in shape.text_frame.paragraphs:
                    p_text = normalize_whitespace("".join(run.text for run in paragraph.runs))
                    if p_text:
                        paragraph_count += 1
                        if BULLET_RE.match(p_text):
                            bullet_like_count += 1

                        ls = paragraph_line_spacing_ratio_pptx(paragraph)
                        if ls is not None:
                            min_line_spacing = ls if min_line_spacing is None else min(min_line_spacing, ls)

                    for run in paragraph.runs:
                        run_text = normalize_whitespace(run.text)
                        if not run_text:
                            continue

                        block_text_parts.append(run_text)

                        size = getattr(run.font, "size", None)
                        size_pt = None
                        try:
                            if size is not None:
                                size_pt = float(size.pt)
                        except Exception:
                            size_pt = None

                        if size_pt is not None:
                            run_sizes.append(size_pt)

                        run_color = get_run_font_color(run, fallback=None)
                        if run_color:
                            run_colors.append(run_color)

                        raw_font_name = getattr(run.font, "name", None)
                        wc = count_words(run_text)
                        font_kind = classify_font_basic(raw_font_name)

                        if raw_font_name:
                            font_name_counts[str(raw_font_name).strip()] += wc

                        if font_kind == "sans":
                            sans_words += wc
                        elif font_kind == "serif":
                            serif_words += wc
                        else:
                            unknown_words += wc

                        if run_text and size_pt is not None and size_pt < SMALL_FONT_THRESHOLD_PT:
                            small_font_hits.append(
                                {
                                    "text": run_text[:120],
                                    "size_pt": round(size_pt, 1),
                                }
                            )

                block_text = normalize_whitespace(" ".join(block_text_parts)) or raw_text
                if block_text:
                    text_blocks.append(
                        {
                            "text_block_index": len(text_blocks) + 1,
                            "text": block_text,
                            "bbox": bbox,
                            "size_pt": safe_round(sum(run_sizes) / len(run_sizes), 1) if run_sizes else None,
                            "font_color": average_color(run_colors),
                            "background_color": block_bg,
                            "source": "pptx_text_frame",
                        }
                    )

            try:
                if hasattr(shape, "image") and getattr(shape, "image", None) is not None:
                    descr, title, has_alt = extract_pptx_alt_text(shape)
                    if not has_alt:
                        missing_alt_text_count += 1

                    figures.append(
                        {
                            "figure_index": len(figures) + 1,
                            "location": f"Diapositiva {idx} · figura {len(figures) + 1}",
                            "bbox": bbox,
                            "image": pil_image_from_bytes(shape.image.blob),
                            "notes": [],
                            "alt_text_present": has_alt,
                            "alt_text_descr": descr,
                            "alt_text_title": title,
                        }
                    )
            except Exception as exc:
                notes.append(f"No se pudo procesar una figura de la diapositiva {idx}: {exc}")

        text = normalize_whitespace("\n\n".join(texts))
        units.append(
            {
                "unit_type": "slide",
                "unit_index": idx,
                "label": f"Diapositiva {idx}",
                "title": title_text or f"Diapositiva {idx}",
                "text": text,
                "text_blocks": text_blocks,
                "figures": figures,
                "small_font_hits": small_font_hits,
                "notes": notes,
                "page_rect": normalize_bbox([0, 0, slide_width, slide_height]),
                "accessibility_meta": {
                    "min_line_spacing": min_line_spacing,
                    "paragraph_count": paragraph_count,
                    "bullet_like_count": bullet_like_count,
                    "text_blocks_count": len(text_blocks),
                    "elements_count": paragraph_count + len(figures),
                    "sans_words": sans_words,
                    "serif_words": serif_words,
                    "font_name_counts": dict(font_name_counts),
                    "unknown_words": unknown_words,
                    "missing_alt_text_count": missing_alt_text_count,
                    "image_count": len(figures),
                    "total_words": count_words(text),
                    "total_chars": len(text),
                },
            }
        )

    return units


# --------------------------------

def extract_document_units(input_file: Path, use_ocr: bool, logger: logging.Logger) -> Tuple[str, List[dict]]:
    suffix = input_file.suffix.lower()

    if suffix == ".pdf":
        return "pdf", extract_pdf_units(input_file, use_ocr, logger)

    if suffix == ".pptx":
        return "pptx", extract_pptx_units(input_file, logger)

    if suffix == ".ppt":
        converted = _convert_ppt_to_pptx(input_file, logger)
        return "ppt", extract_pptx_units(converted, logger)

    raise RuntimeError("Formato documental no soportado. Usa PDF, PPT o PPTX.")


# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------


def add_issue(
        issues: List[dict],
        issue_id: int,
        location: str,
        category_code: str,
        category: str,
        severity_code: str,
        severity: str,
        message: str,
        recommendation: str,
        excerpt: str,
        unit_index: int,
        extra: Optional[dict] = None,
) -> int:
    payload = {
        "id": f"issue-{issue_id:03d}",
        "location": location,
        "category_code": category_code,
        "category": category,
        "severity_code": severity_code,
        "severity": severity,
        "message": message,
        "recommendation": recommendation,
        "excerpt": excerpt,
        "unit_index": unit_index,
    }
    if extra:
        payload.update(extra)
    issues.append(payload)
    return issue_id + 1


def build_methodology_section() -> dict:
    return {
        "title": "Metodología y referencias",
        "contrast_rules": [
            {
                "metric_key": "text_normal",
                "label": "Contraste textual para texto normal",
                "metric_type_code": "normative",
                "metric_type": "Umbral normativo de referencia",
                "threshold": WCAG_NORMAL_TEXT_RATIO,
                "reference_code": "WCAG-1.4.3",
                "details": "Referencia orientativa: 4.5:1.",
            },
            {
                "metric_key": "text_large",
                "label": "Contraste textual para texto grande",
                "metric_type_code": "normative",
                "metric_type": "Umbral normativo de referencia",
                "threshold": WCAG_LARGE_TEXT_RATIO,
                "reference_code": "WCAG-1.4.3",
                "details": "Referencia orientativa: 3:1.",
            },
            {
                "metric_key": "non_text",
                "label": "Contraste de figuras y componentes visuales relevantes",
                "metric_type_code": "normative",
                "metric_type": "Umbral normativo de referencia",
                "threshold": WCAG_NON_TEXT_RATIO,
                "reference_code": "WCAG-1.4.11",
                "details": "Referencia orientativa: 3:1.",
            },
            {
                "metric_key": "cvd_risk",
                "label": "Riesgo CVD / daltonismo",
                "metric_type_code": "heuristic",
                "metric_type": "Métrica heurística del sistema",
                "threshold": None,
                "reference_code": "BRETTEL-1997 + MACHADO-2009",
                "details": "Estimación automática basada en simulaciones aproximadas de protanopia, deuteranopia y tritanopia. No equivale a certificación oficial.",
            },
        ],
        "references": deepcopy(METHODOLOGY_REFERENCES),
        "limitations": [
            "En PPT/PPTX el contraste puede calcularse con más precisión cuando existen colores RGB explícitos en shapes y runs.",
            "En PDF, cuando no hay colores estructurados, el contraste textual puede estimarse a partir de renderización local del bloque y debe interpretarse como una estimación.",
            "La evaluación CVD es heurística y orientativa: ayuda a detectar riesgo relativo de confusión cromática, pero no sustituye una revisión experta.",
        ],
    }


def analyze_document(units: List[dict], document_type: str, input_filename: str) -> dict:
    issues: List[dict] = []
    recommendations: List[str] = []
    issue_id = 1
    dense_text_count = 0
    small_font_count = 0
    text_contrast_checks = 0
    text_contrast_issue_count = 0
    figures_total = 0
    figures_analyzed = 0
    figure_contrast_issue_count = 0
    cvd_issue_count = 0
    processing_notes: List[str] = []
    all_text_metric_rows: List[dict] = []
    all_figure_metric_rows: List[dict] = []
    line_spacing_issue_count = 0
    too_many_words_count = 0
    insufficient_text_blocks_count = 0
    too_many_elements_count = 0
    missing_alt_text_issue_count = 0
    unavailable_pdf_metric_count = 0
    total_estimated_read_time_seconds = 0.0
    units_with_estimated_read_time = 0
    font_family_issue_count = 0

    for unit in units:
        text = normalize_whitespace(unit.get("text", ""))
        location = unit.get("label", "Documento")
        unit_index = int(unit.get("unit_index", 0) or 0)
        excerpt = make_excerpt(text)
        text_blocks = unit.get("text_blocks", []) or []
        figures = unit.get("figures", []) or []
        page_rect = normalize_bbox(unit.get("page_rect"))
        figures_total += len(figures)

        # ---------------------------------------------------------
        # Acesibilidad
        # trecho añadido o modificado
        # dentro de analyze_document(...)

        accessibility_meta = unit.get("accessibility_meta", {}) or {}

        font_eval = evaluate_sans_serif_compliance(accessibility_meta, document_type=document_type)

        min_line_spacing = accessibility_meta.get("min_line_spacing")
        total_words_structured = accessibility_meta.get("total_words")
        text_blocks_count = accessibility_meta.get("text_blocks_count")
        elements_count = accessibility_meta.get("elements_count")
        missing_alt_text_count = accessibility_meta.get("missing_alt_text_count")

        estimated_unit_read_time = estimate_unit_read_time_seconds(
            total_words=total_words_structured,
            image_count=accessibility_meta.get("image_count"),
            elements_count=elements_count,
        )

        if estimated_unit_read_time is not None:
            total_estimated_read_time_seconds += estimated_unit_read_time
            units_with_estimated_read_time += 1

        # ---------------------------------------------------------

        unavailable_metrics: List[str] = []

        if min_line_spacing is None:
            if document_type == "pdf":
                unavailable_metrics.append("espacio entre líneas")
        else:
            if float(min_line_spacing) < MIN_LINE_SPACING:
                line_spacing_issue_count += 1
                issue_id = add_issue(
                    issues,
                    issue_id,
                    location,
                    "line_spacing",
                    "Espaciado entre líneas",
                    "medium",
                    "media",
                    f"Se detectó un espaciado mínimo entre líneas de {float(min_line_spacing):.2f}, por debajo de la referencia 1.15.",
                    "Aumenta el espacio entre líneas y procura mantener, como referencia, un interlineado mínimo de 1.15.",
                    excerpt,
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "min_line_spacing": safe_round(min_line_spacing, 2),
                    },
                )

        if total_words_structured is None:
            if document_type == "pdf":
                unavailable_metrics.append("cantidad de palabras por unidad")
        else:
            if int(total_words_structured) > MAX_WORDS_PER_UNIT:
                too_many_words_count += 1
                issue_id = add_issue(
                    issues,
                    issue_id,
                    location,
                    "too_many_words",
                    "Cantidad de palabras",
                    "medium",
                    "media",
                    f"Se detectaron {int(total_words_structured)} palabras, por encima de la referencia de {MAX_WORDS_PER_UNIT}.",
                    "Reduce la cantidad de texto por diapositiva o página y reparte mejor el contenido.",
                    excerpt,
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "word_count": int(total_words_structured),
                        "threshold": MAX_WORDS_PER_UNIT,
                    },
                )

        if text_blocks_count is None:
            if document_type == "pdf":
                unavailable_metrics.append("cantidad de bloques de texto")
        else:
            if int(text_blocks_count) < MIN_TEXT_BLOCKS:
                insufficient_text_blocks_count += 1
                issue_id = add_issue(
                    issues,
                    issue_id,
                    location,
                    "insufficient_text_blocks",
                    "Bloques de texto",
                    "low",
                    "baja",
                    f"Se detectó {int(text_blocks_count)} bloque de texto; se recomienda contar con al menos {MIN_TEXT_BLOCKS}.",
                    "Divide el contenido en al menos dos bloques de texto o secciones visuales más claras.",
                    excerpt,
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "text_blocks_count": int(text_blocks_count),
                        "threshold": MIN_TEXT_BLOCKS,
                    },
                )

        if elements_count is None:
            if document_type == "pdf":
                unavailable_metrics.append("cantidad total de elementos")
        else:
            if int(elements_count) > MAX_ELEMENTS:
                too_many_elements_count += 1
                issue_id = add_issue(
                    issues,
                    issue_id,
                    location,
                    "too_many_elements",
                    "Cantidad de elementos",
                    "medium",
                    "media",
                    f"Se detectaron {int(elements_count)} elementos, por encima de la referencia de {MAX_ELEMENTS}.",
                    "Reduce la cantidad de elementos visibles por unidad y simplifica la composición.",
                    excerpt,
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "elements_count": int(elements_count),
                        "threshold": MAX_ELEMENTS,
                    },
                )

        if missing_alt_text_count is None:
            if document_type == "pdf":
                unavailable_metrics.append("texto alternativo en imágenes")
        else:
            if int(missing_alt_text_count) > 0:
                missing_alt_text_issue_count += 1
                issue_id = add_issue(
                    issues,
                    issue_id,
                    location,
                    "missing_alt_text",
                    "Texto alternativo en imágenes",
                    "medium",
                    "media",
                    f"Se detectaron {int(missing_alt_text_count)} imágenes sin texto alternativo.",
                    "Añade texto alternativo a las imágenes relevantes para que puedan interpretarse con tecnologías de apoyo.",
                    excerpt,
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "images_missing_alt_text": int(missing_alt_text_count),
                    },
                )
        if font_eval["status"] == "no":
            font_family_issue_count += 1
            issue_id = add_issue(
                issues,
                issue_id,
                location,
                "font_family",
                "Tipografía sans serif",
                "medium",
                "media",
                (
                    f"Se detecta uso relevante de tipografías con serifa o mezcla tipográfica no recomendada "
                    f"para este criterio. Cobertura reconocida: {font_eval.get('known_ratio', 0):.2f}. "
                    f"Ejemplos detectados: {', '.join(font_eval.get('examples', [])[:3]) or 'sin muestra'}."
                ),
                "Prioriza tipografías sans serif consistentes, especialmente en títulos, cuerpo y etiquetas.",
                excerpt,
                unit_index,
                extra={
                    "metric_type": "Métrica heurística del sistema",
                    "font_family_status": font_eval["status"],
                    "font_known_word_ratio": font_eval.get("known_ratio"),
                    "font_examples": font_eval.get("examples", []),
                },
            )
        elif document_type == "pdf" and font_eval["status"] == "unavailable":
            unavailable_metrics.append("tipografía sans serif")

        if document_type == "pdf" and unavailable_metrics:
            unavailable_pdf_metric_count += 1
            issue_id = add_issue(
                issues,
                issue_id,
                location,
                "metric_unavailable_pdf",
                "Métricas no verificables en PDF",
                "low",
                "baja",
                build_pdf_extension_hint(unavailable_metrics),
                "Para extender el analisis actual, considera utilizar el formato pptx.",
                excerpt,
                unit_index,
                extra={
                    "metric_type": "Métrica heurística del sistema",
                    "unavailable_metrics": unavailable_metrics,
                },
            )
        # ----------------------------
        if not text and not figures:
            issue_id = add_issue(
                issues,
                issue_id,
                location,
                "no_text",
                "Sin texto detectable",
                "low",
                "baja",
                "No se ha detectado texto utilizable en esta sección del documento.",
                "Verifica si la página o diapositiva contiene texto seleccionable o si requiere una revisión manual.",
                excerpt,
                unit_index,
            )

        if text:
            word_count = count_words(text)
            paragraph_word_lengths = paragraph_lengths(text)
            longest_paragraph_words = max(paragraph_word_lengths, default=0)
            if word_count >= TEXT_DENSITY_WORD_THRESHOLD or longest_paragraph_words >= PARAGRAPH_DENSITY_WORD_THRESHOLD:
                dense_text_count += 1
                issue_id = add_issue(
                    issues,
                    issue_id,
                    location,
                    "dense_text",
                    "Carga visual de texto",
                    "medium",
                    "media",
                    "Se ha detectado un bloque textual denso que puede dificultar el escaneo visual y la lectura rápida.",
                    "Divide la información en bloques más breves, usa más aire visual y redistribuye el contenido entre más páginas o diapositivas cuando sea necesario.",
                    excerpt,
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "word_count": word_count,
                        "longest_paragraph_words": longest_paragraph_words,
                    },
                )

        if document_type in {"ppt", "pptx"} and unit.get("small_font_hits"):
            sample = unit["small_font_hits"][0]
            small_font_count += len(unit["small_font_hits"])
            issue_id = add_issue(
                issues,
                issue_id,
                location,
                "small_fonts",
                "Tamaño de letra",
                "medium",
                "media",
                f"Se han detectado textos potencialmente pequeños para una visualización cómoda. Ejemplo aproximado: {sample.get('size_pt', '?')} pt.",
                "Aumenta el tamaño de las fuentes y verifica la legibilidad en pantalla completa, proyección o móvil.",
                make_excerpt(sample.get("text", "")),
                unit_index,
                extra={
                    "metric_type": "Métrica heurística del sistema",
                    "threshold": SMALL_FONT_THRESHOLD_PT,
                },
            )

        for block in text_blocks:
            contrast_data = assess_text_block_contrast(block, unit)
            if not contrast_data:
                continue
            text_contrast_checks += 1
            ratio = float(contrast_data["ratio"])
            threshold = float(contrast_data["threshold"])
            estimated = bool(contrast_data.get("estimated"))
            bbox = normalize_bbox(block.get("bbox"))
            bbox_human = humanize_bbox(bbox, page_rect)
            all_text_metric_rows.append(
                {
                    "location": location,
                    "text_block_index": block.get("text_block_index"),
                    "ratio": safe_round(ratio, 2),
                    "threshold": threshold,
                    "estimated": estimated,
                    "method": "estimado" if estimated else "estructurado",
                    "size_pt": contrast_data.get("size_pt"),
                    "bbox": bbox,
                    "bbox_human": bbox_human,
                    "color_fg": rgb_to_hex(contrast_data.get("foreground_rgb")),
                    "color_bg": rgb_to_hex(contrast_data.get("background_rgb")),
                }
            )

            if ratio < threshold:
                text_contrast_issue_count += 1
                severity_code = infer_severity_for_ratio(ratio, threshold)
                issue_id = add_issue(
                    issues,
                    issue_id,
                    f"{location} · bloque textual {block.get('text_block_index', '?')}",
                    "text_contrast",
                    "Contraste textual",
                    severity_code,
                    severity_label(severity_code),
                    (
                        f"Se estima un contraste texto-fondo de {ratio:.2f}:1, por debajo del umbral de referencia {threshold:.1f}:1. "
                        f"Zona aproximada: {bbox_human}."
                    ),
                    "Aumenta la diferencia entre color de texto y fondo, o reestructura el bloque visual para cumplir mejor con WCAG/WCAG2ICT.",
                    make_excerpt(block.get("text", "")),
                    unit_index,
                    extra={
                        "metric_type": "Umbral normativo de referencia" if not estimated else "Métrica heurística del sistema",
                        "ratio": safe_round(ratio, 2),
                        "threshold": threshold,
                        "bbox": bbox,
                        "bbox_human": bbox_human,
                        "color_fg": rgb_to_hex(contrast_data.get("foreground_rgb")),
                        "color_bg": rgb_to_hex(contrast_data.get("background_rgb")),
                        "estimated": estimated,
                        "reference_code": "WCAG-1.4.3 / WCAG2ICT",
                    },
                )

        for figure in figures:
            figure_metrics = analyze_figure_visuals(figure)
            if not figure_metrics:
                note = f"{figure.get('location', location)}: no se pudo calcular la métrica visual figura a figura con fiabilidad suficiente."
                processing_notes.append(note)
                continue

            figures_analyzed += 1
            ratio = figure_metrics.get("contrast_ratio")
            bbox = normalize_bbox(figure.get("bbox"))
            bbox_human = humanize_bbox(bbox, page_rect)
            all_figure_metric_rows.append(
                {
                    "location": figure.get("location", location),
                    "figure_index": figure.get("figure_index"),
                    "ratio": ratio,
                    "threshold": WCAG_NON_TEXT_RATIO,
                    "bbox": bbox,
                    "bbox_human": bbox_human,
                    "worst_cvd_type": figure_metrics.get("worst_cvd_type"),
                    "worst_cvd_ratio": figure_metrics.get("worst_cvd_ratio"),
                    "color_dependency": figure_metrics.get("color_dependency"),
                }
            )

            if ratio is not None and float(ratio) < WCAG_NON_TEXT_RATIO:
                figure_contrast_issue_count += 1
                severity_code = infer_severity_for_ratio(float(ratio), WCAG_NON_TEXT_RATIO)
                issue_id = add_issue(
                    issues,
                    issue_id,
                    figure.get("location", location),
                    "figure_contrast",
                    "Contraste en figura",
                    severity_code,
                    severity_label(severity_code),
                    (
                        f"La figura presenta un contraste visual estimado de {float(ratio):.2f}:1, por debajo del umbral orientativo {WCAG_NON_TEXT_RATIO:.1f}:1 para elementos no textuales relevantes. "
                        f"Zona aproximada: {bbox_human}."
                    ),
                    "Revisa si la figura depende de diferencias muy sutiles de luminancia o color, y refuerza contornos, etiquetas o contraste.",
                    f"Ubicación aproximada: {bbox_human}",
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "ratio": ratio,
                        "threshold": WCAG_NON_TEXT_RATIO,
                        "bbox": bbox,
                        "bbox_human": bbox_human,
                        "reference_code": "WCAG-1.4.11 / WCAG2ICT",
                    },
                )

            worst_ratio = figure_metrics.get("worst_cvd_ratio")
            if worst_ratio is not None and float(worst_ratio) < 0.75:
                cvd_issue_count += 1
                severity_code = "high" if float(worst_ratio) < 0.55 else "medium"
                issue_id = add_issue(
                    issues,
                    issue_id,
                    figure.get("location", location),
                    "cvd_risk",
                    "Riesgo para daltonismo",
                    severity_code,
                    severity_label(severity_code),
                    (
                        f"La figura muestra una pérdida relativa de separabilidad cromática bajo simulación CVD. El caso más sensible es {figure_metrics.get('worst_cvd_type', 'desconocido')} con score {float(worst_ratio):.3f}."
                    ),
                    "Añade codificación redundante mediante etiquetas, patrones, contornos o diferencias de luminancia para reducir la dependencia exclusiva del color.",
                    f"Zona aproximada: {bbox_human}. Dependencia del color estimada: {figure_metrics.get('color_dependency', 'desconocida')}",
                    unit_index,
                    extra={
                        "metric_type": "Métrica heurística del sistema",
                        "score_ratio": worst_ratio,
                        "reference_code": "BRETTEL-1997 / MACHADO-2009",
                        "bbox": bbox,
                        "bbox_human": bbox_human,
                        "cvd": figure_metrics.get("cvd"),
                    },
                )

        for note in unit.get("notes", []):
            clean_note = normalize_whitespace(note)
            if not clean_note:
                continue
            processing_notes.append(f"{location}: {clean_note}")
            issue_id = add_issue(
                issues,
                issue_id,
                location,
                "processing_note",
                "Nota de procesamiento",
                "low",
                "baja",
                clean_note,
                "Revisa manualmente esta sección del documento para completar la validación.",
                excerpt,
                unit_index,
                extra={"metric_type": "Métrica heurística del sistema"},
            )

    if font_family_issue_count:
        recommendations.append(
            "Prioriza el uso consistente de tipografías sans serif para mejorar legibilidad y claridad visual."
        )
    if dense_text_count:
        recommendations.append(
            "Reduce la densidad de contenido por página o diapositiva, priorizando bloques más cortos, jerarquía visual más clara y más espacio en blanco."
        )
    if small_font_count:
        recommendations.append(
            "Revisa el tamaño de las fuentes y asegúrate de que sigan siendo legibles en pantalla compartida, proyección o visualización móvil."
        )
    if text_contrast_issue_count:
        recommendations.append(
            "Ajusta pares texto-fondo con bajo contraste, especialmente en bloques pequeños, subtítulos o etiquetas con colores suaves."
        )
    if figure_contrast_issue_count:
        recommendations.append(
            "Refuerza el contraste de figuras y gráficos con contornos, etiquetas directas y diferencias de luminancia más claras."
        )
    if cvd_issue_count:
        recommendations.append(
            "Evita depender solo del color en figuras relevantes: añade texto, patrones, marcadores o codificación redundante accesible para personas con CVD."
        )
    if not recommendations:
        recommendations.append(
            "El análisis automático no detectó alertas visuales relevantes, aunque siempre conviene una revisión manual final de contraste, jerarquía visual y dependencia del color."
        )

    # Acesibility
    if missing_alt_text_issue_count:
        recommendations.append(
            "Añade texto alternativo a las imágenes relevantes para mejorar la accesibilidad con tecnologías de apoyo."
        )
    if line_spacing_issue_count:
        recommendations.append(
            "Revisa el interlineado en las unidades señaladas y procura mantener, como referencia, un valor mínimo de 1.15."
        )
    if too_many_words_count:
        recommendations.append(
            "Reduce la cantidad de palabras por diapositiva o página cuando supere la referencia establecida."
        )
    if insufficient_text_blocks_count:
        recommendations.append(
            "Segmenta mejor el contenido y procura organizar cada unidad en al menos dos bloques de texto cuando sea posible."
        )
    if too_many_elements_count:
        recommendations.append(
            "Reduce la cantidad total de elementos por unidad para evitar sobrecarga visual."
        )
    if unavailable_pdf_metric_count:
        recommendations.append(
            "En algunos PDF no fue posible verificar todas las métricas estructurales. Para extender el analisis actual, considera utilizar el formato pptx."
        )

    recommendations = clean_list_items(recommendations)
    processing_notes = clean_list_items(list(dict.fromkeys(processing_notes)))[:20]
    issues.sort(key=issue_sort_key)
    reportable_issues = [issue for issue in issues if issue.get("category_code") != "processing_note"]

    units_label = friendly_units_label(document_type)
    finished_at = datetime.now()

    finished_at = datetime.now()

    overview = (
        f"Se analizaron {len(units)} {units_label} del archivo {input_filename}.\n"
        f"Se detectaron {len(reportable_issues)} alertas.\n"
        f"Fecha de finalización: {finished_at.strftime('%d/%m/%Y %H:%M')}."
    )

    severity_totals = {
        "alta": sum(1 for issue in reportable_issues if issue.get("severity_code") == "high"),
        "media": sum(1 for issue in reportable_issues if issue.get("severity_code") == "medium"),
        "baja": sum(1 for issue in reportable_issues if issue.get("severity_code") == "low"),
    }

    methodology = build_methodology_section()
    text_metric_samples = select_text_metric_rows(all_text_metric_rows, max_rows=8)
    figure_metric_samples = select_figure_metric_rows(all_figure_metric_rows, max_rows=8)
    visual_metrics = {
        "reportable_issue_count": len(reportable_issues),
        "processing_note_count": len(processing_notes),
        "text_blocks_analyzed": text_contrast_checks,
        "text_contrast_issues": text_contrast_issue_count,
        "dense_text_sections": dense_text_count,
        "small_font_hits": small_font_count,
        "figure_count": figures_total,
        "figures_analyzed": figures_analyzed,
        "figure_contrast_issues": figure_contrast_issue_count,
        "cvd_risk_issues": cvd_issue_count,
        "text_metrics_summary": summarize_text_metrics(all_text_metric_rows),
        "figure_metrics_summary": summarize_figure_metrics(all_figure_metric_rows),
        "text_metric_samples": text_metric_samples,
        "figure_metric_samples": figure_metric_samples,
        "processing_notes": processing_notes,
        "line_spacing_issues": line_spacing_issue_count,
        "too_many_words_issues": too_many_words_count,
        "insufficient_text_blocks_issues": insufficient_text_blocks_count,
        "too_many_elements_issues": too_many_elements_count,
        "missing_alt_text_issues": missing_alt_text_issue_count,
        "metric_unavailable_pdf_issues": unavailable_pdf_metric_count,
        "estimated_read_time_seconds": round(total_estimated_read_time_seconds, 2),
        "estimated_read_time_minutes": minutes_decimal(total_estimated_read_time_seconds),
        "estimated_read_time_human": seconds_to_human_readable(total_estimated_read_time_seconds),
        "units_with_estimated_read_time": units_with_estimated_read_time,
        "font_family_issues": font_family_issue_count
    }

    return {
        "summary": {
            "title": "Informe de accesibilidad",
            "overview": overview,
            "totals": {
                "units_analyzed": len(units),
                "issue_count": len(issues),
                "reportable_issue_count": len(reportable_issues),
                "processing_note_count": len(processing_notes),
                "document_type": document_type,
                "text_blocks_analyzed": text_contrast_checks,
                "figures_analyzed": figures_analyzed,
            },
            "severity_totals": severity_totals,
        },
        "issues": issues,
        "recommendations": recommendations,
        "visual_metrics": visual_metrics,
        "methodology": methodology,
    }


# Acesibilidad



# ---------------------------------------------------------
# OUTPUTS
# ---------------------------------------------------------

SLIDE_ACCESSIBILITY_FIELDS = [
    "unit_index",
    "unit_type",
    "label",
    "min_line_spacing_detected",
    "line_spacing_ge_1_15",
    "sans_serif_ok",
    "font_family_status",
    "font_known_word_ratio",
    "font_detected_examples",
    "total_words",
    "words_le_60",
    "text_blocks_count",
    "has_at_least_2_text_blocks",
    "elements_count",
    "elements_le_7",
    "image_count",
    "images_missing_alt_text",
    "all_images_have_alt_text",
    "char_count",
    "estimated_read_time_seconds",
    "estimated_read_time_minutes",
    "estimated_read_time_human",
    "notes",
]


def build_slide_accessibility_rows(units: List[dict], document_type: str) -> List[dict]:
    rows = []

    for unit in units:
        meta = unit.get("accessibility_meta", {}) or {}
        unit_type = unit.get("unit_type", "page" if document_type == "pdf" else "slide")
        unit_index = int(unit.get("unit_index", 0) or 0)
        label = unit.get("label") or unit.get("title") or f"{unit_type.title()} {unit_index}"

        min_line_spacing = meta.get("min_line_spacing")
        total_words = meta.get("total_words")
        total_chars = meta.get("total_chars")
        text_blocks_count = meta.get("text_blocks_count")
        elements_count = meta.get("elements_count")
        image_count = meta.get("image_count", 0)
        missing_alt = meta.get("missing_alt_text_count")

        estimated_read_time_seconds = estimate_unit_read_time_seconds(
            total_words=total_words,
            image_count=image_count,
            elements_count=elements_count,
        )

        sans_words = meta.get("sans_words", 0) or 0
        serif_words = meta.get("serif_words", 0) or 0
        unknown_words = meta.get("unknown_words", 0) or 0

        known_words = sans_words + serif_words

        font_eval = evaluate_sans_serif_compliance(meta, document_type=document_type)

        if font_eval["status"] == "yes":
            sans_serif_ok = True
        elif font_eval["status"] == "no":
            sans_serif_ok = False
        else:
            sans_serif_ok = None

        notes = []
        for note in unit.get("notes", []) or []:
            clean_note = normalize_whitespace(note)
            if clean_note:
                notes.append(clean_note)

        rows.append(
            {
                "unit_index": unit_index,
                "unit_type": unit_type,
                "label": label,
                "min_line_spacing_detected": min_line_spacing,
                "line_spacing_ge_1_15": None if min_line_spacing is None else (
                            float(min_line_spacing) >= MIN_LINE_SPACING),
                "sans_serif_ok": sans_serif_ok,
                "font_family_status": font_eval["status"],
                "font_known_word_ratio": font_eval["known_ratio"],
                "font_detected_examples": " | ".join(font_eval["examples"]),
                "total_words": total_words,
                "words_le_60": None if total_words is None else (int(total_words) <= MAX_WORDS_PER_UNIT),
                "text_blocks_count": text_blocks_count,
                "has_at_least_2_text_blocks": None if text_blocks_count is None else (
                            int(text_blocks_count) >= MIN_TEXT_BLOCKS),
                "elements_count": elements_count,
                "elements_le_7": None if elements_count is None else (int(elements_count) <= MAX_ELEMENTS),
                "image_count": image_count,
                "images_missing_alt_text": missing_alt,
                "all_images_have_alt_text": None if missing_alt is None else (int(missing_alt) == 0),
                "char_count": total_chars,
                "notes": " | ".join(notes),
                "estimated_read_time_seconds": estimated_read_time_seconds,
                "estimated_read_time_minutes": minutes_decimal(estimated_read_time_seconds),
                "estimated_read_time_human": seconds_to_human_readable(estimated_read_time_seconds),
            }
        )

    return rows


def write_slide_accessibility_report_csv(path: Path, rows: List[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SLIDE_ACCESSIBILITY_FIELDS)
        writer.writeheader()

        for row in rows:
            out = dict(row)
            out["min_line_spacing_detected"] = fmt_csv_value(out.get("min_line_spacing_detected"))
            out["line_spacing_ge_1_15"] = yes_no_unavailable(out.get("line_spacing_ge_1_15"))
            out["sans_serif_ok"] = yes_no_unavailable(out.get("sans_serif_ok"))
            out["words_le_60"] = yes_no_unavailable(out.get("words_le_60"))
            out["has_at_least_2_text_blocks"] = yes_no_unavailable(out.get("has_at_least_2_text_blocks"))
            out["elements_le_7"] = yes_no_unavailable(out.get("elements_le_7"))
            out["all_images_have_alt_text"] = yes_no_unavailable(out.get("all_images_have_alt_text"))

            out["total_words"] = fmt_csv_value(out.get("total_words"))
            out["text_blocks_count"] = fmt_csv_value(out.get("text_blocks_count"))
            out["elements_count"] = fmt_csv_value(out.get("elements_count"))
            out["image_count"] = fmt_csv_value(out.get("image_count"))
            out["images_missing_alt_text"] = fmt_csv_value(out.get("images_missing_alt_text"))
            out["char_count"] = fmt_csv_value(out.get("char_count"))
            out["estimated_read_time_seconds"] = fmt_csv_value(out.get("estimated_read_time_seconds"))
            out["estimated_read_time_minutes"] = fmt_csv_value(out.get("estimated_read_time_minutes"))
            out["estimated_read_time_human"] = out.get("estimated_read_time_human", "unavailable")

            writer.writerow(out)


def build_document_summary_dict(
        input_file: Path,
        analyzed_file: Path,
        document_type: str,
        units: List[dict],
) -> dict:
    slide_rows = build_slide_accessibility_rows(units, document_type=document_type)

    words_known = [r["total_words"] for r in slide_rows if isinstance(r.get("total_words"), int)]
    chars_known = [r["char_count"] for r in slide_rows if isinstance(r.get("char_count"), int)]
    images_known = [r["image_count"] for r in slide_rows if isinstance(r.get("image_count"), int)]
    missing_alt_known = [r["images_missing_alt_text"] for r in slide_rows if
                         isinstance(r.get("images_missing_alt_text"), int)]
    read_time_known = [r["estimated_read_time_seconds"] for r in slide_rows if
                       isinstance(r.get("estimated_read_time_seconds"), (int, float))]

    total_read_time_seconds = round(sum(read_time_known), 2) if read_time_known else None

    return {
        "input_file": str(input_file),
        "analyzed_file": str(analyzed_file),
        "document_type": document_type,
        "total_units": len(slide_rows),
        "document_total_words_estimated": sum(words_known),
        "document_total_chars_estimated": sum(chars_known),
        "document_total_images": sum(images_known),
        "document_total_images_missing_alt_text": (
            sum(missing_alt_known) if len(missing_alt_known) == len(slide_rows) else "unavailable"
        ),
        "document_estimated_read_time_seconds": total_read_time_seconds if total_read_time_seconds is not None else "unavailable",
        "document_estimated_read_time_minutes": minutes_decimal(
            total_read_time_seconds) if total_read_time_seconds is not None else "unavailable",
        "document_estimated_read_time_human": seconds_to_human_readable(total_read_time_seconds),
        "units_with_estimated_read_time": len(read_time_known),
        "units_with_unavailable_text_metrics": sum(
            1 for r in slide_rows
            if r.get("total_words") is None or r.get("char_count") is None or r.get("text_blocks_count") is None
        ),
    }


def write_document_summary_csv(path: Path, summary_dict: dict) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_dict.keys()))
        writer.writeheader()
        writer.writerow(summary_dict)


def save_accessibility_csv_outputs(
        input_file: Path,
        analyzed_file: Path,
        document_type: str,
        units: List[dict],
        output_dir: Path,
) -> Dict[str, str]:
    slide_rows = build_slide_accessibility_rows(units, document_type=document_type)

    slide_csv = output_dir / "slide_accessibility_report.csv"
    summary_csv = output_dir / "document_summary.csv"

    write_slide_accessibility_report_csv(slide_csv, slide_rows)
    write_document_summary_csv(
        summary_csv,
        build_document_summary_dict(
            input_file=input_file,
            analyzed_file=analyzed_file,
            document_type=document_type,
            units=units,
        ),
    )

    return {
        "slide_accessibility_report_csv": slide_csv.name,
        "document_summary_csv": summary_csv.name,
    }


# ----------------------------

def render_metric_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _filter_reportable_issues(payload: dict) -> List[dict]:
    all_issues = payload.get("issues", []) or []
    issues = [issue for issue in all_issues if issue.get("category_code") != "processing_note"]
    return sorted(issues, key=issue_sort_key)

def build_localized_overview(payload: dict, lang: str) -> str:
    totals = (payload.get("summary", {}) or {}).get("totals", {}) or {}

    units_count = int(totals.get("units_analyzed", 0) or 0)
    issue_count = int(totals.get("reportable_issue_count", totals.get("issue_count", 0)) or 0)
    document_type = str(totals.get("document_type", payload.get("document_type", "pptx")) or "pptx")
    filename = str(payload.get("input_filename", "documento"))
    finished_at = str(payload.get("report_generated_at", ""))

    if document_type == "pdf":
        unit_es = "página" if units_count == 1 else "páginas"
        unit_en = "page" if units_count == 1 else "pages"
        unit_pt = "página" if units_count == 1 else "páginas"
        unit_gl = "páxina" if units_count == 1 else "páxinas"
    else:
        unit_es = "diapositiva" if units_count == 1 else "diapositivas"
        unit_en = "slide" if units_count == 1 else "slides"
        unit_pt = "diapositiva" if units_count == 1 else "diapositivas"
        unit_gl = "diapositiva" if units_count == 1 else "diapositivas"

    if lang == "en":
        line1 = f"{units_count} {unit_en} from the {filename} file {'was' if units_count == 1 else 'were'} analyzed."
        line2 = f"{issue_count} {'alert' if issue_count == 1 else 'alerts'} {'was' if issue_count == 1 else 'were'} detected."
        line3 = f"Completion date: {finished_at}"
        return f"{line1}\n{line2}\n{line3}"

    if lang == "pt":
        if units_count == 1:
            line1 = f"Foi analisada 1 {unit_pt} do arquivo {filename}."
        else:
            line1 = f"Foram analisadas {units_count} {unit_pt} do arquivo {filename}."

        if issue_count == 1:
            line2 = "Foi detectado 1 alerta."
        else:
            line2 = f"Foram detectados {issue_count} alertas."

        line3 = f"Data de finalização: {finished_at}"
        return f"{line1}\n{line2}\n{line3}"

    if lang == "gl":
        if units_count == 1:
            line1 = f"Analizouse 1 {unit_gl} do arquivo {filename}."
        else:
            line1 = f"Analizáronse {units_count} {unit_gl} do arquivo {filename}."

        if issue_count == 1:
            line2 = "Detectouse 1 alerta."
        else:
            line2 = f"Detectáronse {issue_count} alertas."

        line3 = f"Data de finalización: {finished_at}"
        return f"{line1}\n{line2}\n{line3}"

    # Español por defecto
    line1 = f"Se analizaron {units_count} {unit_es} del archivo {filename}."
    line2 = f"Se detectaron {issue_count} alertas."
    line3 = f"Fecha de finalización: {finished_at}"
    return f"{line1}\n{line2}\n{line3}"

def _teacher_area_label(category_code: str) -> str:
    mapping = {
        "cvd_risk": "Color, daltonismo y figuras",
        "figure_contrast": "Color, daltonismo y figuras",
        "missing_alt_text": "Imágenes y accesibilidad",
        "text_contrast": "Tamaño de letra y legibilidad",
        "small_fonts": "Tamaño de letra y legibilidad",
        "line_spacing": "Tamaño de letra y legibilidad",
        "dense_text": "Cantidad de texto",
        "too_many_words": "Cantidad de texto",
        "insufficient_text_blocks": "Estructura del contenido",
        "too_many_elements": "Estructura del contenido",
        "metric_unavailable_pdf": "Alcance del análisis",
        "no_text": "Contenido no detectable",
        "font_family": "Tamaño de letra y legibilidad",
    }
    return mapping.get(normalize_whitespace(str(category_code or "")).lower(), "Accesibilidad visual")


# -----------------------------


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR _teacher_area_key(...)
# ---------------------------------------------------------

def _teacher_area_key(category_code: str) -> str:
    category_code = normalize_whitespace(str(category_code or "")).lower()
    if category_code in {"cvd_risk", "figure_contrast"}:
        return "color"
    if category_code in {"text_contrast", "small_fonts", "line_spacing", "font_family"}:
        return "legibility"
    if category_code in {"dense_text", "too_many_words"}:
        return "text_load"
    if category_code in {"missing_alt_text", "insufficient_text_blocks", "too_many_elements"}:
        return "structure"
    if category_code in {"metric_unavailable_pdf", "no_text"}:
        return "content"

    return "other"


# -----------------------------


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR _teacher_severity_weight(...)
# ---------------------------------------------------------

def _teacher_severity_weight(issue: dict) -> float:
    severity_code = normalize_whitespace(str(issue.get("severity_code") or "")).lower()
    base = {"high": 3.0, "medium": 2.0, "low": 1.0}.get(severity_code, 1.0)
    category_code = normalize_whitespace(str(issue.get("category_code") or "")).lower()
    bonus = {
        "cvd_risk": 1.0,
        "figure_contrast": 0.7,
        "missing_alt_text": 0.6,
        "small_fonts": 0.45,
        "line_spacing": 0.40,
        "text_contrast": 0.35,
        "too_many_words": 0.35,
        "dense_text": 0.2,
        "insufficient_text_blocks": 0.25,
        "too_many_elements": 0.25,
        "metric_unavailable_pdf": 0.10,
        "no_text": 0.2,
    }.get(category_code, 0.0)
    return base + bonus


# ------------------


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR _teacher_priority_sort_key(...)
# ---------------------------------------------------------

def _teacher_priority_sort_key(issue: dict) -> Tuple[float, int, str]:
    category_code = normalize_whitespace(str(issue.get("category_code") or "")).lower()
    category_rank = {
        "cvd_risk": 0,
        "figure_contrast": 1,
        "missing_alt_text": 2,
        "small_fonts": 3,
        "line_spacing": 4,
        "text_contrast": 5,
        "too_many_words": 6,
        "dense_text": 7,
        "insufficient_text_blocks": 8,
        "too_many_elements": 9,
        "metric_unavailable_pdf": 10,
        "no_text": 11,
    }.get(category_code, 50)
    unit_index = int(issue.get("unit_index", 0) or 0)
    return (-_teacher_severity_weight(issue), category_rank, f"{unit_index:04d}:{issue.get('location', '')}")


# ---------------------

# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR _teacher_issue_message(...)
# ---------------------------------------------------------

def _teacher_issue_message(issue: dict) -> str:
    category_code = normalize_whitespace(str(issue.get("category_code") or "")).lower()
    mapping = {
        "cvd_risk": "Parte de la información puede depender demasiado del color para interpretarse con claridad.",
        "figure_contrast": "Hay figuras o gráficos cuyo contraste visual puede quedarse corto en proyección o pantalla compartida.",
        "missing_alt_text": "Hay imágenes sin texto alternativo, lo que limita la accesibilidad con lectores de pantalla.",
        "text_contrast": "Hay algunos textos o etiquetas con legibilidad limitada frente al fondo.",
        "small_fonts": "Hay elementos de texto que pueden resultar pequeños para una lectura cómoda en clase.",
        "line_spacing": "El interlineado detectado puede ser insuficiente para una lectura cómoda.",
        "dense_text": "Hay secciones con demasiada información para una explicación o lectura ágil.",
        "too_many_words": "Hay diapositivas o páginas con una cantidad de palabras superior a la recomendada.",
        "insufficient_text_blocks": "Hay unidades con una estructura textual poco segmentada, con menos bloques de texto de los recomendables.",
        "too_many_elements": "Hay unidades con demasiados elementos visuales o textuales, lo que puede aumentar la sobrecarga.",
        "metric_unavailable_pdf": "Hay métricas estructurales que no se pudieron verificar con suficiente fiabilidad en el PDF.",
        "no_text": "Hay una parte del material que conviene revisar manualmente porque no se ha podido interpretar con suficiente fiabilidad.",
        "font_family": "Se detecta una tipografía con serifa o una mezcla tipográfica que puede reducir la claridad visual.",
    }
    return mapping.get(category_code, normalize_whitespace(
        str(issue.get("message") or "")) or "Se ha detectado una incidencia visual relevante.")


# --------------------------

def _build_teacher_area_stats(issues: List[dict]) -> Dict[str, dict]:
    stats = {
        "color": {"weight": 0.0, "high": 0, "medium": 0, "low": 0, "count": 0},
        "legibility": {"weight": 0.0, "high": 0, "medium": 0, "low": 0, "count": 0},
        "text_load": {"weight": 0.0, "high": 0, "medium": 0, "low": 0, "count": 0},
        "structure": {"weight": 0.0, "high": 0, "medium": 0, "low": 0, "count": 0},
        "content": {"weight": 0.0, "high": 0, "medium": 0, "low": 0, "count": 0},
        "other": {"weight": 0.0, "high": 0, "medium": 0, "low": 0, "count": 0},
    }
    for issue in issues:
        area_key = _teacher_area_key(issue.get("category_code"))
        severity_code = normalize_whitespace(str(issue.get("severity_code") or "")).lower()
        bucket = stats[area_key]
        bucket["count"] += 1
        bucket["weight"] += _teacher_severity_weight(issue)
        if severity_code in {"high", "medium", "low"}:
            bucket[severity_code] += 1
    return stats


def _teacher_color_signal(payload: dict, issues: List[dict]) -> dict:
    visual_metrics = payload.get("visual_metrics", {}) or {}
    figure_summary = visual_metrics.get("figure_metrics_summary", {}) or {}
    min_cvd_ratio = figure_summary.get("min_cvd_ratio")
    figure_contrast_issues = int(visual_metrics.get("figure_contrast_issues", 0) or 0)
    cvd_issue_count = int(visual_metrics.get("cvd_risk_issues", 0) or 0)
    color_issues = [issue for issue in issues if _teacher_area_key(issue.get("category_code")) == "color"]
    high_color = sum(
        1 for issue in color_issues if normalize_whitespace(str(issue.get("severity_code") or "")).lower() == "high")
    medium_color = sum(
        1 for issue in color_issues if normalize_whitespace(str(issue.get("severity_code") or "")).lower() == "medium")

    if cvd_issue_count > 0 or high_color > 0:
        level = "high"
    elif figure_contrast_issues > 0 or medium_color > 0:
        level = "medium"
    elif min_cvd_ratio is not None and float(min_cvd_ratio) < 0.90:
        level = "watch"
    else:
        level = "low"

    return {
        "level": level,
        "min_cvd_ratio": min_cvd_ratio,
        "cvd_issue_count": cvd_issue_count,
        "figure_contrast_issues": figure_contrast_issues,
    }


def _teacher_focus_text(area_key: str, issues: List[dict], payload: Optional[dict] = None) -> str:
    payload = payload or {}
    color_signal = _teacher_color_signal(payload, issues)
    visual_metrics = payload.get("visual_metrics", {}) or {}
    text_contrast_issues = int(visual_metrics.get("text_contrast_issues", 0) or 0)
    small_font_hits = int(visual_metrics.get("small_font_hits", 0) or 0)

    if color_signal["level"] == "high":
        return (
            "La principal mejora pendiente está en cómo se distingue la información visual en algunas figuras y esquemas. "
            "Parte del material puede depender demasiado del color para transmitir significado."
        )
    if color_signal["level"] == "medium":
        return (
            "Conviene reforzar la forma de distinguir la información visual en figuras y gráficos. "
            "En algunas zonas, el contraste o la diferenciación por color puede quedarse corto para clase o proyección."
        )
    if color_signal["level"] == "watch":
        return "La legibilidad general es adecuada, pero conviene revisar algunas figuras donde la diferenciación visual puede depender demasiado del color."
    if area_key == "legibility":
        if small_font_hits and text_contrast_issues:
            return "La principal mejora pendiente está en el tamaño de letra, el interlineado y en algunos elementos de texto con legibilidad limitada."
        if small_font_hits:
            return "La principal mejora pendiente está en el tamaño de letra para proyección o pantalla compartida."
        return "La principal mejora pendiente está en reforzar la legibilidad del texto frente al fondo."
    if area_key == "text_load":
        return "La principal mejora pendiente está en simplificar la cantidad de información por página o diapositiva."
    if area_key == "structure":
        return "La principal mejora pendiente está en la estructura del contenido y en la accesibilidad de las imágenes."
    if area_key == "content":
        return "Hay partes del análisis que no se pudieron verificar con suficiente fiabilidad en el formato actual."
    return "El material presenta un resultado general correcto, con mejoras puntuales recomendables antes de usarlo en clase."


def _teacher_decision_block(payload: dict, issues: List[dict]) -> dict:
    summary = payload.get("summary", {}) or {}
    totals = summary.get("totals", {}) or {}
    severity_totals = summary.get("severity_totals", {}) or {}
    visual_metrics = payload.get("visual_metrics", {}) or {}
    reportable_count = int(totals.get("reportable_issue_count", totals.get("issue_count", 0)) or 0)
    high_count = int(severity_totals.get("alta", 0) or 0)
    medium_count = int(severity_totals.get("media", 0) or 0)
    text_contrast_issues = int(visual_metrics.get("text_contrast_issues", 0) or 0)
    small_font_hits = int(visual_metrics.get("small_font_hits", 0) or 0)

    stats = _build_teacher_area_stats(issues)
    color_signal = _teacher_color_signal(payload, issues)
    if color_signal["level"] == "high":
        stats["color"]["weight"] += 6.0
    elif color_signal["level"] == "medium":
        stats["color"]["weight"] += 3.5
    elif color_signal["level"] == "watch":
        stats["color"]["weight"] += 2.0
    if text_contrast_issues > 0:
        stats["legibility"]["weight"] += min(2.0, 0.35 * text_contrast_issues)
    if small_font_hits > 0:
        stats["legibility"]["weight"] += min(2.0, 0.25 * small_font_hits)

    dominant_area = \
    max(stats.items(), key=lambda item: (item[1]["weight"], item[1]["high"], item[1]["medium"], item[1]["count"]))[
        0] if issues or any(v.get("weight") for v in stats.values()) else "other"
    focus_text = _teacher_focus_text(dominant_area, issues, payload=payload)

    if reportable_count == 0:
        label = "Muy bien"
        decision = "Se puede usar tal como está."
        decision_summary = "El análisis automático no ha detectado incidencias visuales prioritarias en el material."
    elif high_count >= 2 or reportable_count >= 8:
        label = "Revisar"
        decision = "Conviene revisarlo antes de usarlo en clase."
        decision_summary = f"Se han detectado {reportable_count} incidencias prioritarias. La revisión previa puede mejorar la legibilidad, la interpretación visual o ambas."
    elif high_count >= 1 or medium_count >= 3 or reportable_count >= 4 or color_signal["level"] == "high":
        label = "Atención"
        decision = "Se puede usar, pero conviene corregir algunos puntos antes de clase."
        decision_summary = f"Se han detectado {reportable_count} incidencias que conviene revisar para reforzar la claridad visual del material."
    else:
        label = "Bien"
        decision = "Se puede usar con ajustes menores."
        decision_summary = "El material presenta una base adecuada, aunque conviene revisar algunos detalles antes de proyectarlo o compartirlo."

    return {
        "label": label,
        "decision": decision,
        "summary": decision_summary,
        "focus": focus_text,
    }


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR _build_teacher_priorities(...)
# ---------------------------------------------------------

def _build_teacher_priorities(payload: dict, issues: List[dict], max_items: int = 3) -> List[dict]:
    priorities = []
    asset_map = {item.get("issue_id"): item for item in (payload.get("teacher_priority_assets", []) or []) if
                 item.get("issue_id")}

    for issue in sorted(issues, key=_teacher_priority_sort_key)[:max_items]:
        category_code = normalize_whitespace(str(issue.get("category_code") or "")).lower()
        action = normalize_whitespace(
            str(issue.get("recommendation") or "")) or "Revisa esta parte del material antes de usarlo."

        if category_code in {"cvd_risk", "figure_contrast"}:
            action = "Añade etiquetas directas, iconos, patrones o diferencias de forma para que la información no dependa solo del color."
        elif category_code == "missing_alt_text":
            action = "Añade texto alternativo a las imágenes relevantes para que puedan interpretarse con tecnologías de apoyo."
        elif category_code == "small_fonts":
            action = "Aumenta el tamaño de letra y comprueba la legibilidad en proyección o pantalla compartida."
        elif category_code == "line_spacing":
            action = "Aumenta el espacio entre líneas y procura mantener, como referencia, un interlineado mínimo de 1.15."
        elif category_code == "text_contrast":
            action = "Refuerza el contraste entre texto y fondo, especialmente en etiquetas, notas breves y elementos secundarios."
        elif category_code in {"dense_text", "too_many_words"}:
            action = "Reduce la cantidad de texto por diapositiva o página, divide ideas y reparte mejor el contenido."
        elif category_code == "insufficient_text_blocks":
            action = "Divide el contenido en al menos dos bloques de texto o secciones visuales más claras."
        elif category_code == "too_many_elements":
            action = "Reduce la cantidad de elementos por unidad y prioriza una composición más simple."
        elif category_code == "metric_unavailable_pdf":
            action = "Para extender el analisis actual, considera utilizar el formato pptx."
        elif category_code == "font_family":
            action = "Prioriza tipografías sans serif consistentes en títulos, cuerpo y etiquetas del material."

        asset = asset_map.get(issue.get("id"), {})
        priorities.append({
            "issue_id": issue.get("id"),
            "location": issue.get("location", "Documento"),
            "area": _teacher_area_label(str(issue.get("category_code") or "")),
            "severity": issue.get("severity", "-"),
            "what": _teacher_issue_message(issue),
            "action": action,
            "preview_image_path": asset.get("preview_image_path"),
            "preview_alt": asset.get("preview_alt"),
            "preview_caption": asset.get("preview_caption"),
        })
    return priorities


# ---------------------------------------------------------
# Acesibilidad
# trecho añadido o modificado
# REEMPLAZAR _build_teacher_categories(...)
# ---------------------------------------------------------

def _build_teacher_categories(payload: dict, issues: List[dict]) -> List[dict]:
    color_signal = _teacher_color_signal(payload, issues)
    buckets = [
        {"key": "color", "title": "Color, daltonismo y figuras", "codes": {"cvd_risk", "figure_contrast"}},
        {"key": "legibility", "title": "Tamaño de letra y legibilidad",
         "codes": {"text_contrast", "small_fonts", "line_spacing", "font_family"}},
        {"key": "text_load", "title": "Cantidad de texto", "codes": {"dense_text", "too_many_words"}},
        {"key": "structure", "title": "Estructura del contenido e imágenes",
         "codes": {"missing_alt_text", "insufficient_text_blocks", "too_many_elements"}},
        {"key": "content", "title": "Alcance del análisis", "codes": {"metric_unavailable_pdf", "no_text"}},
    ]

    categories = []
    for bucket in buckets:
        bucket_issues = [issue for issue in issues if
                         normalize_whitespace(str(issue.get("category_code") or "")).lower() in bucket["codes"]]
        high_count = sum(1 for issue in bucket_issues if
                         normalize_whitespace(str(issue.get("severity_code") or "")).lower() == "high")
        medium_count = sum(1 for issue in bucket_issues if
                           normalize_whitespace(str(issue.get("severity_code") or "")).lower() == "medium")

        if bucket["key"] == "color" and not bucket_issues and color_signal["level"] == "watch":
            status = "Bien"
        elif not bucket_issues:
            status = "Muy bien"
        elif high_count >= 1:
            status = "Revisar"
        elif medium_count >= 1 or len(bucket_issues) >= 2:
            status = "Atención"
        else:
            status = "Bien"

        if bucket["key"] == "color":
            if bucket_issues:
                detail = "Conviene revisar figuras donde el contraste o la diferenciación cromática puede no ser suficiente."
            elif color_signal["level"] == "watch":
                detail = "No aparecen incidencias duras en esta categoría, pero sí señales de dependencia cromática que conviene revisar."
            else:
                detail = "No se han detectado incidencias prioritarias en color, daltonismo o figuras."

        elif bucket["key"] == "legibility":
            if any(normalize_whitespace(str(i.get("category_code") or "")).lower() == "line_spacing" for i in
                   bucket_issues):
                detail = "Hay unidades donde el interlineado o la presentación del texto puede dificultar la lectura."
            elif bucket_issues:
                detail = "Hay elementos de texto que conviene revisar por contraste o por tamaño de letra."
            else:
                detail = "La legibilidad general del texto es adecuada."

        elif bucket["key"] == "text_load":
            if bucket_issues:
                detail = "Hay unidades con demasiadas palabras o con carga textual superior a la recomendable."
            else:
                detail = "La carga textual general es adecuada y no se aprecia sobrecarga relevante."

        elif bucket["key"] == "structure":
            if any(normalize_whitespace(str(i.get("category_code") or "")).lower() == "missing_alt_text" for i in
                   bucket_issues):
                detail = "Hay imágenes sin texto alternativo o con estructura visual que conviene revisar."
            elif bucket_issues:
                detail = "Hay aspectos estructurales del contenido que conviene simplificar o segmentar mejor."
            else:
                detail = "La estructura general del contenido y de las imágenes es adecuada."

        else:
            if bucket_issues:
                detail = "Hay partes del análisis que no se pudieron verificar con suficiente fiabilidad en el formato actual."
            else:
                detail = "El alcance del análisis ha sido suficiente para las métricas aplicadas."

        categories.append({
            "title": bucket["title"],
            "status": status,
            "count": len(bucket_issues),
            "detail": detail,
        })

    return categories


# ----------------------

def _build_teacher_strengths(payload: dict, categories: List[dict]) -> List[str]:
    strengths: List[str] = []
    visual_metrics = payload.get("visual_metrics", {}) or {}
    if int(visual_metrics.get("dense_text_sections", 0) or 0) == 0:
        strengths.append("La cantidad general de texto es adecuada para un seguimiento razonable en clase.")
    for category in categories:
        if normalize_whitespace(str(category.get("status") or "")) == "Muy bien":
            detail = normalize_whitespace(str(category.get("detail") or ""))
            title = normalize_whitespace(str(category.get("title") or ""))
            if detail:
                strengths.append(f"{title}: {detail}")
    deduped = []
    for item in strengths:
        if item not in deduped:
            deduped.append(item)
    return deduped[:3]


def _set_mupdf_warning_display(enabled: bool) -> Optional[bool]:
    try:
        import fitz  # type: ignore

        tools = getattr(fitz, "TOOLS", None)
        if tools is None or not hasattr(tools, "mupdf_display_warnings"):
            return None
        previous = tools.mupdf_display_warnings()
        try:
            if hasattr(tools, "reset_mupdf_warnings"):
                tools.reset_mupdf_warnings()
        except Exception:
            pass
        tools.mupdf_display_warnings(bool(enabled))
        return bool(previous)
    except Exception:
        return None


def _restore_mupdf_warning_display(previous: Optional[bool]) -> None:
    if previous is None:
        return
    try:
        import fitz  # type: ignore

        tools = getattr(fitz, "TOOLS", None)
        if tools is None or not hasattr(tools, "mupdf_display_warnings"):
            return
        tools.mupdf_display_warnings(bool(previous))
        try:
            if hasattr(tools, "reset_mupdf_warnings"):
                tools.reset_mupdf_warnings()
        except Exception:
            pass
    except Exception:
        pass


def _prepare_preview_pdf(input_file: Path, logger: logging.Logger) -> Tuple[Optional[Path], Optional[Path]]:
    suffix = input_file.suffix.lower()
    if suffix == ".pdf":
        return input_file, None

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        logger.warning("No se pudo generar previsualización de prioridades: LibreOffice no está disponible.")
        return None, None

    tmp_dir = Path(tempfile.mkdtemp(prefix="aluda_preview_pdf_"))
    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(tmp_dir),
        str(input_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.warning("No se pudo generar PDF de previsualización para prioridades: %s",
                       proc.stderr.strip() or proc.stdout.strip())
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None, None

    candidates = list(tmp_dir.glob("*.pdf"))
    if not candidates:
        logger.warning("No se generó ningún PDF de previsualización para prioridades.")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None, None
    return candidates[0], tmp_dir


def _clip_rect_with_padding(rect: Any, bbox: Optional[List[float]]) -> Any:
    if bbox is None:
        return rect
    try:
        import fitz  # type: ignore

        clip = fitz.Rect(*bbox)
        if clip.is_empty or clip.is_infinite:
            return rect
        pad_x = max((clip.x1 - clip.x0) * 0.14, rect.width * 0.02)
        pad_y = max((clip.y1 - clip.y0) * 0.18, rect.height * 0.02)
        clip = fitz.Rect(clip.x0 - pad_x, clip.y0 - pad_y, clip.x1 + pad_x, clip.y1 + pad_y)
        min_w = rect.width * 0.18
        min_h = rect.height * 0.16
        if clip.width < min_w:
            extra = (min_w - clip.width) / 2.0
            clip = fitz.Rect(clip.x0 - extra, clip.y0, clip.x1 + extra, clip.y1)
        if clip.height < min_h:
            extra = (min_h - clip.height) / 2.0
            clip = fitz.Rect(clip.x0, clip.y0 - extra, clip.x1, clip.y1 + extra)
        clip = clip & rect
        return clip if not clip.is_empty else rect
    except Exception:
        return rect


def _save_priority_preview(page: Any, bbox: Optional[List[float]], output_path: Path) -> bool:
    try:
        import fitz  # type: ignore

        clip = _clip_rect_with_padding(page.rect, bbox)
        zoom = 2.0 if bbox else 1.25
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
        pix.save(str(output_path))
        return True
    except Exception:
        return False


def _build_teacher_priority_assets(input_file: Path, output_dir: Path, payload: dict, logger: logging.Logger,
                                   max_items: int = 3) -> List[dict]:
    issues = _filter_reportable_issues(payload)
    if not issues:
        return []

    ranked = sorted(issues, key=_teacher_priority_sort_key)[:max_items]
    preview_pdf, cleanup_dir = _prepare_preview_pdf(input_file, logger)
    if preview_pdf is None:
        return []

    asset_dir = output_dir / "_teacher_assets"
    ensure_dir(asset_dir)
    assets: List[dict] = []
    previous_warning_state = _set_mupdf_warning_display(False)

    try:
        import fitz  # type: ignore

        doc = fitz.open(str(preview_pdf))
        try:
            for idx, issue in enumerate(ranked, start=1):
                if len(doc) == 0:
                    break
                page_index = max(0, min(len(doc) - 1, int(issue.get("unit_index", 1) or 1) - 1))
                page = doc[page_index]
                bbox = normalize_bbox(issue.get("bbox"))
                rel_path = f"_teacher_assets/priority_{idx:02d}.png"
                out_path = output_dir / rel_path
                if _save_priority_preview(page, bbox, out_path):
                    assets.append({
                        "issue_id": issue.get("id"),
                        "preview_image_path": rel_path,
                        "preview_alt": f"Vista de apoyo de {issue.get('location', 'la incidencia prioritaria')}",
                        "preview_caption": issue.get("bbox_human") or issue.get("location") or "Vista de apoyo",
                        "preview_source_page": page_index + 1,
                    })
        finally:
            doc.close()
    except Exception as exc:
        logger.warning("No se pudieron generar imágenes de apoyo para las prioridades docentes: %s", exc)
    finally:
        _restore_mupdf_warning_display(previous_warning_state)
        if cleanup_dir is not None:
            shutil.rmtree(cleanup_dir, ignore_errors=True)

    return assets


# ---------------------------------------------------------
# Informe - Recomendaciones por Dimensión
# trecho añadido o modificado
# ---------------------------------------------------------

def _collect_unit_indexes_for_categories(payload: dict, category_codes: List[str]) -> List[int]:
    issues = _filter_reportable_issues(payload)
    unit_indexes = sorted({
        int(issue.get("unit_index"))
        for issue in issues
        if issue.get("category_code") in category_codes and issue.get("unit_index") is not None
    })
    return unit_indexes


def _format_units_for_review(payload: dict, unit_indexes: List[int]) -> str:
    if not unit_indexes:
        return "No se detectaron diapositivas para revisión."
    document_type = (payload.get("summary", {}) or {}).get("totals", {}).get("document_type", "pptx")
    unit_label = "Páginas" if document_type == "pdf" else "Diapositivas"
    return f"{unit_label} para revisión: " + ", ".join(str(x) for x in unit_indexes)


def render_teacher_report_text(payload: dict) -> str:
    issues = _filter_reportable_issues(payload)
    recommendations = clean_list_items(payload.get("recommendations", []) or [])
    decision = _teacher_decision_block(payload, issues)

    visual_metrics = payload.get("visual_metrics", {}) or {}
    estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")

    priorities = _build_teacher_priorities(payload, issues, max_items=3)
    categories = _build_teacher_categories(payload, issues)
    strengths = _build_teacher_strengths(payload, categories)

    lines = [
        "Informe para profesorado",
        "",
        f"Resultado para docencia: {decision.get('label', '-')}",
        f"Decisión rápida: {decision.get('decision', '-')}",
        f"Resumen ejecutivo: {decision.get('summary', '-')}",
        f"Tiempo estimado de lectura del material: {estimated_read_time_human}",
        f"Foco principal: {decision.get('focus', '-')}",
        "",
        "Qué conviene corregir primero",
    ]
    if priorities:
        for item in priorities:
            lines.extend([
                f"- {item.get('location', '-')}",
                f"  Área: {item.get('area', '-')}",
                f"  Qué ocurre: {item.get('what', '-')}",
                f"  Qué hacer: {item.get('action', '-')}",
                "",
            ])
    else:
        lines.extend(["- No se detectaron incidencias prioritarias en este análisis automático.", ""])

    lines.append("Resumen rápido por categorías")
    for category in categories:
        lines.append(f"- {category.get('title', '-')}: {category.get('status', '-')}")
        lines.append(f"  {category.get('detail', '-')}")

    lines.extend(["", "Qué ya funciona bien"])
    if strengths:
        for item in strengths:
            lines.append(f"- {item}")
    else:
        lines.append(
            "- El material presenta una base general utilizable, aunque conviene revisar algunos detalles antes de clase.")

    lines.extend(["", "Recomendaciones prácticas"])
    if recommendations:
        for item in recommendations[:5]:
            lines.append(f"- {item}")
    else:
        lines.append("- No hay recomendaciones adicionales.")

    lines.extend(["",
                  "A continuación se incluye un anexo técnico con el detalle completo del análisis automático, para consulta y revisión más especializada.",
                  ""])
    return "\n".join(lines) + "\n"


def render_technical_report_text(payload: dict) -> str:
    summary = payload.get("summary", {}) or {}
    totals = summary.get("totals", {}) or {}
    severity_totals = summary.get("severity_totals", {}) or {}
    all_issues = payload.get("issues", []) or []
    issues = [issue for issue in all_issues if issue.get("category_code") != "processing_note"]
    recommendations = clean_list_items(payload.get("recommendations", []) or [])
    visual_metrics = payload.get("visual_metrics", {}) or {}
    methodology = payload.get("methodology", {}) or {}

    lines = [
        "Anexo técnico",
        "",
        summary.get("title", "Informe de accesibilidad documental"),
        "",
        summary.get("overview", ""),
        "",
        "Resumen",
        f"- Unidades analizadas: {totals.get('units_analyzed', '-')}",
        f"- Alertas visuales: {totals.get('reportable_issue_count', totals.get('issue_count', '-'))}",
        f"- Notas de procesamiento: {totals.get('processing_note_count', 0)}",
        f"- Tipo de documento: {totals.get('document_type', '-')}",
        f"- Bloques textuales evaluados: {totals.get('text_blocks_analyzed', '-')}",
        f"- Figuras analizadas: {totals.get('figures_analyzed', '-')}",
        f"- Severidad alta/media/baja: {severity_totals.get('alta', 0)}/{severity_totals.get('media', 0)}/{severity_totals.get('baja', 0)}",
        "",
        #  "Incidencias prioritarias",
    ]

    if issues:
        for issue in issues:
            lines.extend([
                f"- {issue.get('location', '-')}: {issue.get('category', '-')}",
                f"  Severidad: {issue.get('severity', '-')}",
                f"  Mensaje: {issue.get('message', '-')}",
                f"  Recomendación: {issue.get('recommendation', '-')}",
                (f"  Extracto: {issue.get('excerpt', '')}" if issue.get("excerpt") else ""),
                (f"  Referencia: {issue.get('reference_code', '')}" if issue.get("reference_code") else ""),
                "",
            ])
    else:
        lines.append("- No se detectaron incidencias visuales prioritarias en este análisis automático.")
        lines.append("")

        # ---------------------------------------------------------
        # Acesibilidad
        # trecho añadido o modificado
        # dentro de render_technical_report_text(...)
        # ---------------------------------------------------------

        lines.extend([
            "Métricas visuales y estructurales",
            f"- Contrastes textuales evaluados: {visual_metrics.get('text_blocks_analyzed', '-')}",
            f"- Incidencias de contraste textual: {visual_metrics.get('text_contrast_issues', '-')}",
            f"- Secciones con carga visual alta: {visual_metrics.get('dense_text_sections', '-')}",
            f"- Alertas de fuente pequeña: {visual_metrics.get('small_font_hits', '-')}",
            f"- Incidencias de interlineado: {visual_metrics.get('line_spacing_issues', 0)}",
            f"- Unidades con exceso de palabras: {visual_metrics.get('too_many_words_issues', 0)}",
            f"- Unidades con bloques de texto insuficientes: {visual_metrics.get('insufficient_text_blocks_issues', 0)}",
            f"- Unidades con demasiados elementos: {visual_metrics.get('too_many_elements_issues', 0)}",
            f"- Incidencias de texto alternativo en imágenes: {visual_metrics.get('missing_alt_text_issues', 0)}",
            f"- Métricas no verificables en PDF: {visual_metrics.get('metric_unavailable_pdf_issues', 0)}",
            f"- Figuras detectadas: {visual_metrics.get('figure_count', '-')}",
            f"- Incidencias de contraste en figuras: {visual_metrics.get('figure_contrast_issues', '-')}",
            f"- Incidencias de riesgo CVD: {visual_metrics.get('cvd_risk_issues', '-')}",
            f"- Incidencias de familia tipográfica: {visual_metrics.get('font_family_issues', 0)}",
            "",
        ])

    text_compact_note = build_text_metric_compact_note(visual_metrics)
    figure_compact_note = build_figure_metric_compact_note(visual_metrics)

    lines.append("Resumen técnico de contraste textual")
    if text_compact_note:
        lines.append(f"- {text_compact_note}")
    else:
        for item in build_metric_summary_lines(visual_metrics.get("text_metrics_summary", {}) or {}, "text"):
            lines.append(f"- {item}")
        text_rows = _select_relevant_metric_rows(visual_metrics.get("text_metric_samples", []) or [])
        if text_rows:
            lines.extend(["", "Muestras de contraste textual"])
            for row in text_rows:
                lines.append(
                    f"- {row.get('location', '-')}, bloque {row.get('text_block_index', '-')}: {row.get('status', '-')} · {row.get('ratio', '-')}:1 (umbral {row.get('threshold', '-')}:1) · {row.get('bbox_human', '-')}")

    lines.append("")
    lines.append("Resumen técnico de figuras y CVD")
    if figure_compact_note:
        lines.append(f"- {figure_compact_note}")
    else:
        for item in build_metric_summary_lines(visual_metrics.get("figure_metrics_summary", {}) or {}, "figure"):
            lines.append(f"- {item}")
        figure_rows = _select_relevant_metric_rows(visual_metrics.get("figure_metric_samples", []) or [])
        if figure_rows:
            lines.extend(["", "Muestras de figuras y CVD"])
            for row in figure_rows:
                ratio_text = f"{row.get('ratio')}:1" if row.get('ratio') is not None else "sin dato"
                cvd_text = row.get('worst_cvd_ratio', '-')
                lines.append(
                    f"- {row.get('location', '-')}, figura {row.get('figure_index', '-')}: {row.get('status', '-')} · contraste {ratio_text} · peor score CVD {cvd_text} · {row.get('bbox_human', '-')}")

    processing_notes = clean_list_items(visual_metrics.get("processing_notes", []) or [])
    if processing_notes:
        lines.extend(["", "Notas de procesamiento"])
        for note in processing_notes:
            lines.append(f"- {note}")

    lines.extend(["", "Recomendaciones generales"])
    for item in recommendations:
        lines.append(f"- {item}")

    lines.extend(["", methodology.get("title", "Metodología y referencias")])
    for rule in methodology.get("contrast_rules", []) or []:
        threshold = rule.get("threshold")
        threshold_text = f" · Umbral: {threshold}:1" if threshold is not None else ""
        lines.append(
            f"- {rule.get('label', '-')}: {rule.get('metric_type', '-')} · {rule.get('reference_code', '-')}{threshold_text}")
        if rule.get("details"):
            lines.append(f"  {rule.get('details')}")
    if methodology.get("limitations"):
        lines.append("")
        lines.append("Limitaciones de la estimación")
        for item in clean_list_items(methodology.get("limitations", [])):
            lines.append(f"- {item}")
    if methodology.get("references"):
        lines.append("")
        lines.append("Referencias")
        for ref in methodology.get("references", []):
            lines.append(f"- {ref.get('title', '-')}")
            if ref.get("details"):
                lines.append(f"  {ref.get('details')}")

    return "\n".join(lines) + "\n"


def render_report_text(payload: dict) -> str:
    return render_teacher_report_text(payload) + render_technical_report_text(payload)


def build_metric_table_html(rows: Iterable[dict], columns: List[Tuple[str, str]],
                            empty_text: str = "No hay muestras suficientes para mostrar en esta sección.") -> str:
    rows = [row for row in rows if row]
    if not rows:
        return f"<div class='muted'>{html.escape(empty_text)}</div>"
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_parts = []
    for row in rows:
        row_class = ""
        status = str(row.get("status", "")).lower()
        if "incidencia" in status or "riesgo" in status:
            row_class = " class='row-alert'"
        elif "cercano" in status:
            row_class = " class='row-warn'"
        cols = []
        for key, _label in columns:
            cols.append(f"<td>{html.escape(render_metric_value(row.get(key)))}</td>")
        body_parts.append(f"<tr{row_class}>" + "".join(cols) + "</tr>")
    return f"<table class='data-table'><thead><tr>{head}</tr></thead><tbody>{''.join(body_parts)}</tbody></table>"


def build_metric_summary_list_html(lines: List[str]) -> str:
    lines = clean_list_items(lines)
    if not lines:
        return "<div class='muted'>No hay datos agregados disponibles.</div>"
    return "<ul class='summary-list'>" + "".join(f"<li>{html.escape(item)}</li>" for item in lines) + "</ul>"


def _metric_row_is_relevant(row: dict) -> bool:
    status = normalize_whitespace(str((row or {}).get("status", ""))).lower()
    return any(token in status for token in ("incidencia", "riesgo", "cercano"))


def _select_relevant_metric_rows(rows: Iterable[dict]) -> List[dict]:
    selected = [row for row in (rows or []) if row and _metric_row_is_relevant(row)]
    return selected


def build_text_metric_compact_note(visual_metrics: dict) -> Optional[str]:
    summary = visual_metrics.get("text_metrics_summary", {}) or {}
    total = int(visual_metrics.get("text_blocks_total", 0) or 0)
    analyzed = int(visual_metrics.get("text_blocks_analyzed", 0) or 0)
    below = int(summary.get("below_threshold_count", 0) or 0)
    near = int(summary.get("near_threshold_count", 0) or 0)

    if analyzed <= 0:
        if total <= 0:
            return "No se obtuvieron métricas estructuradas de contraste textual aplicables a este documento."
        return "No se generaron métricas estructuradas de contraste textual suficientemente fiables como para mostrar una tabla detallada en esta sección."

    if below == 0 and near == 0:
        return f"Se evaluaron {analyzed} bloques de texto y no se detectaron incidencias prioritarias de contraste textual."

    return None


def build_figure_metric_compact_note(visual_metrics: dict) -> Optional[str]:
    figure_count = int(visual_metrics.get("figure_count", 0) or 0)
    analyzed = int(visual_metrics.get("figures_analyzed", 0) or 0)
    contrast_issues = int(visual_metrics.get("figure_contrast_issues", 0) or 0)
    cvd_issues = int(visual_metrics.get("cvd_risk_issues", 0) or 0)
    skip_reasons = visual_metrics.get("figure_skip_reasons", {}) or {}

    if contrast_issues > 0 or cvd_issues > 0:
        return None

    if figure_count <= 0:
        return "No se han detectado figuras relevantes en el documento, por lo que no se muestra un bloque técnico ampliado de figuras y CVD."

    if analyzed > 0:
        return f"Se detectaron {figure_count} figuras y no presentan incidencias prioritarias de contraste o riesgo CVD en este análisis automático."

    if skip_reasons:
        return "Se detectaron elementos visuales, pero no requieren aquí un desarrollo técnico ampliado; en este contexto parecen principalmente ilustrativos o no críticos para el análisis."

    return "Se detectaron figuras, pero no presentan incidencias prioritarias y por ello esta sección se muestra de forma compacta."


def build_teacher_summary_cards_html(categories: List[dict]) -> str:
    if not categories:
        return "<div class='muted'>No hay datos suficientes para mostrar un resumen docente.</div>"
    return "".join(
        f"<div class='metric-card teacher-card'><div class='metric-label'>{html.escape(str(item.get('title', '-')))}</div><div class='metric-value metric-value-small'>{html.escape(str(item.get('status', '-')))}</div><div class='teacher-detail'>{html.escape(str(item.get('detail', '-')))}</div></div>"
        for item in categories
    )


def build_dimension_recommendations_html(payload: dict) -> str:
    sections = build_dimension_recommendations(payload)
    blocks = []

    for section in sections:
        items_html = []
        for item in section["items"]:
            units_text = _format_units_for_review(payload, item["units"])
            items_html.append(
                f"""
                <article class="card issue-card">
                  <div class="issue-location">{html.escape(str(item['metric']))}</div>
                  <div class="issue-recommendation"><strong>Recomendación:</strong> {html.escape(str(item['recommendation']))}</div>
                  <div class="issue-meta">{html.escape(units_text)}</div>
                </article>
                """
            )

        blocks.append(
            f"""
            <section class="section">
              <h2>{html.escape(str(section['dimension']))}</h2>
              {''.join(items_html)}
            </section>
            """
        )

    return "".join(blocks)


def build_teacher_priorities_html(priorities: List[dict]) -> str:
    if not priorities:
        return "<div class='muted'>No se detectaron incidencias prioritarias en este análisis automático.</div>"
    cards = []
    for item in priorities:
        image_html = ""
        if item.get("preview_image_path"):
            caption = html.escape(str(item.get("preview_caption") or "Vista de apoyo"))
            alt = html.escape(str(item.get("preview_alt") or "Vista de apoyo"))
            src = html.escape(str(item.get("preview_image_path")))
            image_html = f"""
              <figure class="priority-figure">
                <img src="{src}" alt="{alt}">
                <figcaption class="priority-caption">{caption}</figcaption>
              </figure>
            """
        cards.append(
            f"""
            <article class="card issue-card teacher-priority-card">
              <div class="teacher-priority-layout">
                <div class="teacher-priority-text">
                  <div class="issue-location">{html.escape(str(item.get('location', '-')))}</div>
                  <div class="issue-meta">{html.escape(str(item.get('area', '-')))} · {html.escape(str(item.get('severity', '-')))}</div>
                  <div class="issue-message"><strong>Qué ocurre:</strong> {html.escape(str(item.get('what', '-')))}</div>
                  <div class="issue-recommendation"><strong>Qué hacer:</strong> {html.escape(str(item.get('action', '-')))}</div>
                </div>
                {image_html}
              </div>
            </article>
            """
        )
    return "".join(cards)


# ---------------------------------------------------------
# HTML/PDF alternativo en español
# trecho añadido o modificado
# ---------------------------------------------------------

def _get_reportable_issues_v2(payload: dict) -> List[dict]:
    return _filter_reportable_issues(payload)


def _intro_message_v2(payload: dict) -> str:
    reportable = len(_get_reportable_issues_v2(payload))
    if reportable == 0:
        return "El análisis de la presentación consideró:"
    return (
        "En el análisis del documento identificamos oportunidades de mejora "
        "para ayudarte a crear materiales más claros y accesibles, considerando:"
    )


def _summary_dimensions_v2(payload: dict) -> List[dict]:
    visual_metrics = payload.get("visual_metrics", {}) or {}
    read_time = visual_metrics.get("estimated_read_time_human", "unavailable")

    return [
        {
            "title": "Comprensión visual",
            "detail": "Tamaño de letra, interlineado, tipografía, cantidad de texto, color y contraste.",
        },
        {
            "title": "Organización del contenido",
            "detail": "Jerarquía visual y cantidad de elementos por diapositiva.",
        },
        {
            "title": "Uso de imágenes",
            "detail": "Presencia de descripciones alternativas de accesibilidad (ALT).",
        }

    ]


def _collect_units_v2(payload: dict, category_codes: List[str]) -> List[int]:
    issues = _get_reportable_issues_v2(payload)
    return sorted({
        int(issue.get("unit_index"))
        for issue in issues
        if issue.get("category_code") in category_codes and issue.get("unit_index") is not None
    })


def _color_findings_summary_v2(payload: dict) -> dict:
    cvd_units = _collect_units_v2(payload, ["cvd_risk"])
    contrast_units = _collect_units_v2(payload, ["text_contrast", "figure_contrast"])

    visual_metrics = payload.get("visual_metrics", {}) or {}
    cvd_count = int(visual_metrics.get("cvd_risk_issues", 0) or 0)
    contrast_count = int(visual_metrics.get("text_contrast_issues", 0) or 0) + int(
        visual_metrics.get("figure_contrast_issues", 0) or 0)

    if not cvd_units and not contrast_units:
        message = (
            "No se detectaron alertas prioritarias asociadas a dificultades de color, "
            "riesgo CVD o contraste cromático en este análisis automático."
        )
    else:
        parts = []
        if cvd_count > 0:
            parts.append(f"{cvd_count} alerta(s) asociada(s) a riesgo CVD")
        if contrast_count > 0:
            parts.append(f"{contrast_count} alerta(s) asociada(s) a contraste")
        joined = " y ".join(parts) if parts else "alertas visuales"
        all_units = sorted(set(cvd_units + contrast_units))
        message = f"Se detectaron {joined}. {_format_units_for_review(payload, all_units)}"

    return {
        "cvd_units": cvd_units,
        "contrast_units": contrast_units,
        "message": message,
    }


def build_dimension_recommendations_v2(payload: dict) -> List[dict]:
    return [
        {
            "dimension": "Dimensión Comprensión visual",
            "summary": "Tamaño de letra, interlineado, tipografía y cantidad de texto.",
            "items": [
                {
                    "metric": "Tamaño de letra",
                    "recommendation": f"Aumentar el tamaño de la letra  manteniendo, como referencia, un tamaño mínimo de {SMALL_FONT_THRESHOLD_PT:.0f} pts.",
                    "units": _collect_units_v2(payload, ["small_fonts"]),
                },
                {
                    "metric": "Tipografía",
                    "recommendation": "Priorizar tipografías sans serif consistentes, especialmente en títulos, cuerpo y etiquetas..",
                    "units": _collect_units_v2(payload, ["font_family"]),
                },
                {
                    "metric": "Interlineado",
                    "recommendation": f"Aumentar el espacio entre líneas manteniendo, como referencia, un interlineado mínimo de {MIN_LINE_SPACING:.2f} pt.",
                    "units": _collect_units_v2(payload, ["line_spacing"]),
                },
                {
                    "metric": "Cantidad de texto",
                    "recommendation": f"Reducir la cantidad de texto por diapositiva o página cuando supere la referencia de  {MAX_WORDS_PER_UNIT} palabras.",
                    "units": _collect_units_v2(payload, ["too_many_words", "dense_text"]),
                },
                {
                    "metric": "Color",
                    "recommendation": f"Revisar el uso de colores en las diapositivas para asegurar que la información sea distinguible para personas con diferentes tipos de visión del color. Evitar combinaciones que puedan generar confusión (por ejemplo, rojo/verde) y reforzar la información con otros recursos como texto, íconos o subrayados..",
                    "units": _collect_unit_indexes_for_categories(payload, ["cvd_risk"]),
                },
                {
                    "metric": "Contraste",
                    "recommendation": f"Mejorar el contraste entre el texto y el fondo para facilitar la lectura. En algunos casos, puede ser necesario ajustar los colores o reorganizar el contenido de la diapositiva.",
                    "units": _collect_unit_indexes_for_categories(payload, ["text_contrast"])
                },
            ],
        },

        {
            "dimension": "Dimensión Organización del contenido",
            "summary": "Jerarquía visual, bloques de contenido y cantidad de elementos por diapositiva.",
            "items": [
                {
                    "metric": "Jerarquia visual",
                    "recommendation": f"Segmentar el contenido organizando  cada diapositiva en, al menos, {MIN_TEXT_BLOCKS} bloques, cuando sea posible.",
                    "units": _collect_units_v2(payload, ["insufficient_text_blocks"]),
                },
                {
                    "metric": "Cantidad de elementos",
                    "recommendation": f"Reducir la cantidad total de elementos por diapositiva manteniendo  un máximo de {MAX_ELEMENTS} elementos visibles.",
                    "units": _collect_unit_indexes_for_categories(payload, ["too_many_elements"]),
                },
            ],
        },
        {
            "dimension": "Dimensión uso de imágenes",
            "summary": "Presencia de descripciones alternativas de accesibilidad.",
            "items": [
                {
                    "metric": "Texto alternativo (ALT)",
                    "recommendation": "Añadir texto alternativo a las imágenes relevantes para que puedan interpretarse con tecnologías de apoyo.",
                    "units": _collect_unit_indexes_for_categories(payload, ["missing_alt_text"]),
                },
            ],
        },
    ]


def build_dimension_recommendations_html_v2(payload: dict) -> str:
    sections = build_dimension_recommendations_v2(payload)
    parts = []

    for section in sections:
        item_cards = []
        for item in section["items"]:
            units_text = _format_units_for_review(payload, item["units"])
            item_cards.append(
                f"""
                <article class="dim-item-card">
                  <div class="dim-metric">{html.escape(str(item["metric"]))}</div>
                  <div class="dim-rec"><strong>Recomendación:</strong> {html.escape(str(item["recommendation"]))}</div>
                  <div class="dim-units">{html.escape(units_text)}</div>
                </article>
                """
            )

        parts.append(
            f"""
            <section class="section">
              <div class="dimension-card">
                <h2>{html.escape(str(section["dimension"]))}</h2>
                <p class="dimension-summary">{html.escape(str(section["summary"]))}</p>
                {''.join(item_cards)}
              </div>
            </section>
            """
        )

    return "".join(parts)


def _build_methodology_html_v2(payload: dict) -> str:
    methodology = payload.get("methodology", {}) or {}
    contrast_rules_html = "".join(
        f"<li><strong>{html.escape(str(rule.get('label', '-')))}</strong>"
        + (f" · Umbral: {html.escape(str(rule.get('threshold')))}:1" if rule.get("threshold") is not None else "")
        + (f"<div class='reference-detail'>{html.escape(str(rule.get('details', '')))}</div>" if rule.get(
            "details") else "")
        + "</li>"
        for rule in (methodology.get("contrast_rules", []) or [])
    )
    limitations_html = "".join(
        f"<li>{html.escape(str(item))}</li>"
        for item in clean_list_items(methodology.get("limitations", []) or [])
    )
    reference_items = "".join(
        f"<li><strong>{html.escape(str(ref.get('title', '-')))}</strong>"
        + (f"<div class='reference-detail'>{html.escape(str(ref.get('details', '')))}</div>" if ref.get(
            "details") else "")
        + "</li>"
        for ref in (methodology.get("references", []) or [])
    )

    return f"""
    <section class="section">
      <h2>{html.escape(str(methodology.get('title', 'Metodología y referencias')))}</h2>
      <div class="card">
        <h3>Criterios y referencias utilizados</h3>
        <ul>{contrast_rules_html}</ul>
      </div>
      <div class="columns" style="margin-top:18px;">
        <div class="card">
          <h3>Limitaciones de la estimación</h3>
          <ul>{limitations_html or '<li>No se registraron limitaciones adicionales.</li>'}</ul>
        </div>
        <div class="card">
          <h3>Referencias</h3>
          <ul>{reference_items}</ul>
        </div>
      </div>
    </section>
    """


def render_report_html_es_v2(payload: dict, title: str) -> str:
    summary = payload.get("summary", {}) or {}
    visual_metrics = payload.get("visual_metrics", {}) or {}
    methodology = payload.get("methodology", {}) or {}

    branding_assets = get_pdf_branding_assets()
    logo_uri = branding_assets["logo"].as_uri() if branding_assets["logo"] else ""
    bottom_uri = branding_assets["bottom"].as_uri() if branding_assets["bottom"] else ""

    intro_message = _intro_message_v2(payload)
    summary_cards = _summary_dimensions_v2(payload)
    estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")

    summary_cards_html = "".join(
        f"""
        <div class="metric-card teacher-card">
          <div class="metric-label">{html.escape(str(card['title']))}</div>
          <div class="teacher-detail">{html.escape(str(card['detail']))}</div>
        </div>
        """
        for card in summary_cards
    )

    limitations_html = "".join(
        f"<li>{html.escape(str(item))}</li>"
        for item in clean_list_items(methodology.get("limitations", []) or [])
    )

    reference_items = "".join(
        f"<li><strong>{html.escape(str(ref.get('title', '-')))}</strong>"
        + (f"<div class='reference-detail'>{html.escape(str(ref.get('details', '')))}</div>" if ref.get(
            "details") else "")
        + "</li>"
        for ref in (methodology.get("references", []) or [])
    )

    styles = """
    :root {
      --bg: #f4f7fa;
      --panel: #ffffff;
      --line: #dde6ee;
      --line-strong: #c9d6e1;
      --text: #12263a;
      --muted: #536474;
      --soft: #f8fafc;
      --teacher-soft: #f4f8fb;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 24px; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; }
    .pdf-header-logo, .pdf-footer-image { display: none; }
    .page { max-width: 980px; margin: 0 auto; background: var(--panel); border: 1px solid var(--line); border-radius: 22px; overflow: hidden; box-shadow: 0 6px 24px rgba(18, 38, 58, 0.08); }
    .hero { padding: 30px 32px 18px 32px; border-bottom: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%); }
    .hero h1 { margin: 0; font-size: 30px; line-height: 1.2; }
    .hero p { margin: 10px 0 0 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .hero-overview { white-space: pre-line; }
    .section { padding: 24px 32px 0 32px; }
    .section:last-child { padding-bottom: 32px; }
    h2 { margin: 0 0 14px 0; font-size: 21px; line-height: 1.3; }
    h3 { margin: 0 0 12px 0; font-size: 17px; line-height: 1.3; }
    .section-kicker { color: var(--muted); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; font-weight: 700; }
    .metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .metric-card { border: 1px solid var(--line); border-radius: 16px; background: var(--soft); padding: 14px 16px; min-height: 90px; }
    .teacher-card { background: var(--teacher-soft); }
    .metric-label { color: var(--text); font-size: 15px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; }
    .teacher-detail { color: var(--muted); font-size: 14px; line-height: 1.7; }
    .card { border: 1px solid var(--line); border-radius: 16px; background: #fff; padding: 16px 18px; margin-bottom: 14px; }
    .decision-card { background: linear-gradient(180deg, #ffffff 0%, #f8fcff 100%); }
    .dimension-card { border: 1px solid var(--line); border-radius: 18px; background: #fff; padding: 18px 20px; }
    .dimension-summary { color: var(--muted); font-size: 14px; line-height: 1.7; margin: 0 0 14px 0; }
    .dim-item-card { border: 1px solid var(--line); border-radius: 14px; background: var(--soft); padding: 14px 16px; margin-bottom: 12px; }
    .dim-metric { font-size: 15px; font-weight: 700; margin-bottom: 8px; }
    .dim-rec, .dim-units, li, .reference-detail { font-size: 14px; line-height: 1.7; }
    .dim-units { color: var(--muted); margin-top: 6px; }
    .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
    .slide-summary-card {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  padding: 18px 20px;
}
.section-divider {
  border: 0;
  border-top: 1.2px solid #cfd6dd;
  margin: 20px 0 0 0;
}
.slide-rec-item {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--soft);
  padding: 14px 16px;
  margin-bottom: 12px;
}

.slide-rec-metric {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
}

.slide-rec-dimension {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.slide-rec-text {
  font-size: 14px;
  line-height: 1.7;
}
    @media print {
      @page {
        size: A4;
        margin-top: 46mm;
        margin-right: 14mm;
        margin-bottom: 34mm;
        margin-left: 14mm;
        @top-left { content: element(headerLogo); }
        @bottom-center { content: element(footerImage); }
      }
      body { padding: 0; background: #fff; }
      .page { max-width: none; border: 0; box-shadow: none; border-radius: 0; }
      .card, .metric-card, .dimension-card, .dim-item-card { break-inside: avoid; page-break-inside: avoid; }
      .pdf-header-logo {
        display: block;
        position: running(headerLogo);
        width: 30mm;
        height: 14mm;
        object-fit: contain;
        margin-top: 6mm;
        margin-left: 2mm;
      }
      .pdf-footer-image {
        display: block;
        position: running(footerImage);
        width: 210mm;
        height: 22mm;
        object-fit: cover;
        margin: 0;
      }
      .columns { display: block; }
      .columns > * { margin-bottom: 14px; }
      .section { padding-left: 0; padding-right: 0; }
    }
    """

    return f"""<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>{styles}</style>
  </head>
  <body>
    {f'<img class="pdf-header-logo" src="{logo_uri}" alt="Logo">' if logo_uri else ''}
    {f'<img class="pdf-footer-image" src="{bottom_uri}" alt="Bottom">' if bottom_uri else ''}

    <main class="page">
      <header class="hero">
        <h1>{html.escape(str(summary.get('title', title)))}</h1>
        <p class="hero-overview">{html.escape(str(summary.get('overview', '')))}</p>
        <p><strong>Tiempo estimado de lectura del material:</strong> {html.escape(str(estimated_read_time_human))}</p>
      </header>

      <section class="section">
        <div class="section-kicker">Resumen ejecutivo</div>
        <h2>Informe de accesibilidad para profesorado</h2>
        <div class="card decision-card">
          <p>{html.escape(intro_message)}</p>
          <div class="metric-grid">{summary_cards_html}</div>
        </div>
      </section>

      <section class="section">
        <h2>Recomendaciones por dimensión</h2>
        <div class="card">
          <p>Abajo se detallan las recomendaciones organizadas por dimensión, indicando junto con las diapositivas o páginas en que se sugiere verificar cada aspecto.</p>
        </div>
      </section>

      {build_dimension_recommendations_html_v2(payload)}
        <section class="section">
            <h2>Resumen por diapositivas</h2>
            <div class="card">
            <p>Abajo se presenta, para cada diapositiva, el conjunto de recomendaciones aplicables identificadas en el análisis.</p>
            </div>
        </section>

      {build_slide_recommendations_html(payload)}
      {build_fixed_criteria_section_html_es()}

      <section class="section">
        <div class="columns" style="margin-top:18px;">
          <div class="card">
            <h3>Limitaciones de la estimación</h3>
            <ul>{limitations_html or '<li>No se registraron limitaciones adicionales.</li>'}</ul>
          </div>
          <div class="card">
            <h3>Referencias</h3>
            <ul>{reference_items}</ul>
          </div>
        </div>
      </section>
    </main>
  </body>
</html>
"""


def build_fixed_criteria_section_html_es() -> str:
    return """
    <section class="section">
      <h2>Criterios y referencias utilizados</h2>
      <div class="card">
        <p>Las recomendaciones de este informe se basan en estándares internacionales de accesibilidad y en modelos de análisis reconocidos.</p>

        <h3>Accesibilidad visual y contraste</h3>
        <p><strong>W3C WCAG 2.1 — Criterio 1.4.3 (Contraste mínimo)</strong></p>
        <p class="reference-detail">Referencia: relación de contraste 4.5:1 para texto normal y 3:1 para texto grande.</p>

        <p><strong>W3C WCAG 2.1 — Criterio 1.4.11 (Contraste no textual)</strong></p>
        <p class="reference-detail">Referencia: relación mínima de 3:1 para elementos visuales relevantes.</p>

        <h3>Aplicación a documentos</h3>
        <p><strong>WCAG2ICT — Aplicación de WCAG a documentos y software no web</strong></p>
        <p class="reference-detail">Base para el análisis en presentaciones (PDF, PPT, PPTX).</p>

        <h3>Percepción del color</h3>
        <p><strong>Brettel et al. (1997)</strong></p>
        <p class="reference-detail">Modelo de simulación de visión del color (protanopia, deuteranopia, tritanopia).</p>

        <p><strong>Machado et al. (2009)</strong></p>
        <p class="reference-detail">Modelo para simulación de deficiencias en la percepción del color.</p>
      </div>
    </section>
    """


def render_report_html(payload: dict, title: str) -> str:
    summary = payload.get("summary", {}) or {}
    issues = _filter_reportable_issues(payload)
    recommendations = clean_list_items(payload.get("recommendations", []) or [])
    visual_metrics = payload.get("visual_metrics", {}) or {}
    methodology = payload.get("methodology", {}) or {}

    branding_assets = get_pdf_branding_assets()
    logo_uri = branding_assets["logo"].as_uri() if branding_assets["logo"] else ""
    bottom_uri = branding_assets["bottom"].as_uri() if branding_assets["bottom"] else ""

    decision = _teacher_decision_block(payload, issues)
    visual_metrics = payload.get("visual_metrics", {}) or {}
    estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")
    estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")
    priorities = _build_teacher_priorities(payload, issues, max_items=3)
    categories = _build_teacher_categories(payload, issues)
    strengths = _build_teacher_strengths(payload, categories)

    if issues:
        cards = []
        for issue in issues:
            meta_parts = [issue.get("category", "-"), issue.get("severity", "-")]
            if issue.get("reference_code"):
                meta_parts.append(issue.get("reference_code"))
            if issue.get("metric_type"):
                meta_parts.append(issue.get("metric_type"))
            excerpt_html = ""
            if issue.get("excerpt"):
                excerpt_html = f"<div class='excerpt'><strong>Extracto:</strong> {html.escape(str(issue['excerpt']))}</div>"
            metric_html = ""
            metric_bits = []
            if issue.get("ratio") is not None and issue.get("threshold") is not None:
                metric_bits.append(f"Ratio: {html.escape(str(issue.get('ratio')))}:1")
                metric_bits.append(f"Umbral: {html.escape(str(issue.get('threshold')))}:1")
            if issue.get("score_ratio") is not None:
                metric_bits.append(f"Score CVD: {html.escape(str(issue.get('score_ratio')))}")
            if issue.get("bbox_human"):
                metric_bits.append(f"Zona: {html.escape(str(issue.get('bbox_human')))}")
            if issue.get("color_fg") and issue.get("color_bg"):
                metric_bits.append(
                    f"Colores: {html.escape(str(issue.get('color_fg')))} sobre {html.escape(str(issue.get('color_bg')))}")
            if metric_bits:
                metric_html = "<div class='issue-metrics'>" + " · ".join(metric_bits) + "</div>"
            cards.append(
                f"""
                <article class="card issue-card">
                  <div class="issue-location">{html.escape(str(issue.get('location', '-')))}</div>
                  <div class="issue-meta">{' · '.join(html.escape(str(x)) for x in meta_parts if x)}</div>
                  <div class="issue-message">{html.escape(str(issue.get('message', '-')))}</div>
                  {metric_html}
                  <div class="issue-recommendation"><strong>Recomendación:</strong> {html.escape(str(issue.get('recommendation', '-')))}</div>
                  {excerpt_html}
                </article>
                """
            )
        issues_html = "".join(cards)
    else:
        issues_html = "<div class='muted'>No se detectaron incidencias visuales prioritarias en este análisis automático.</div>"

    teacher_recommendations_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in
                                           recommendations[:5]) or "<li>No hay recomendaciones adicionales.</li>"
    recommendations_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in
                                   recommendations) or "<li>No hay recomendaciones adicionales.</li>"

    text_compact_note = build_text_metric_compact_note(visual_metrics)
    figure_compact_note = build_figure_metric_compact_note(visual_metrics)
    text_metric_rows = _select_relevant_metric_rows(visual_metrics.get("text_metric_samples", []) or [])
    figure_metric_rows = _select_relevant_metric_rows(visual_metrics.get("figure_metric_samples", []) or [])

    if text_compact_note:
        text_summary_html = ""
        text_metrics_html = f"<div class='muted compact-note'>{html.escape(text_compact_note)}</div>"
    else:
        text_summary_html = build_metric_summary_list_html(
            build_metric_summary_lines(visual_metrics.get("text_metrics_summary", {}) or {}, "text"))
        text_metrics_html = build_metric_table_html(
            text_metric_rows,
            columns=[
                ("location", "Ubicación"),
                ("text_block_index", "Bloque"),
                ("status", "Estado"),
                ("ratio", "Ratio"),
                ("threshold", "Umbral"),
                ("bbox_human", "Zona"),
                ("method", "Método"),
            ],
            empty_text="No hay muestras relevantes de contraste textual para mostrar.",
        )

    if figure_compact_note:
        figure_summary_html = ""
        figure_metrics_html = f"<div class='muted compact-note'>{html.escape(figure_compact_note)}</div>"
    else:
        figure_summary_html = build_metric_summary_list_html(
            build_metric_summary_lines(visual_metrics.get("figure_metrics_summary", {}) or {}, "figure"))
        figure_metrics_html = build_metric_table_html(
            figure_metric_rows,
            columns=[
                ("location", "Ubicación"),
                ("figure_index", "Figura"),
                ("status", "Estado"),
                ("ratio", "Ratio figura"),
                ("worst_cvd_type", "CVD más sensible"),
                ("worst_cvd_ratio", "Score CVD"),
                ("bbox_human", "Zona"),
            ],
            empty_text="No hay muestras relevantes de figuras para mostrar.",
        )

    processing_notes = clean_list_items(visual_metrics.get("processing_notes", []) or [])
    processing_notes_html = "".join(
        f"<li>{html.escape(str(note))}</li>" for note in processing_notes) or "<li>No hay notas adicionales.</li>"

    reference_items = "".join(
        f"<li><strong>{html.escape(str(ref.get('metric_type', '-')))}</strong> · {html.escape(str(ref.get('title', '-')))}"
        + (f"<div class='reference-detail'>{html.escape(str(ref.get('details', '')))}</div>" if ref.get(
            "details") else "")
        + "</li>"
        for ref in (methodology.get("references", []) or [])
    )
    contrast_rules_html = "".join(
        f"<li><strong>{html.escape(str(rule.get('label', '-')))}</strong> · {html.escape(str(rule.get('metric_type', '-')))}"
        + (f" · <span class='rule-badge'>Umbral: {html.escape(str(rule.get('threshold')))}:1</span>" if rule.get(
            "threshold") is not None else "")
        + (f" · <span class='rule-badge'>{html.escape(str(rule.get('reference_code', '-')))}</span>" if rule.get(
            "reference_code") else "")
        + (f"<div class='reference-detail'>{html.escape(str(rule.get('details', '')))}</div>" if rule.get(
            "details") else "")
        + "</li>"
        for rule in (methodology.get("contrast_rules", []) or [])
    )
    limitations_html = "".join(
        f"<li>{html.escape(str(item))}</li>" for item in clean_list_items(methodology.get("limitations", []) or []))

    styles = """
    :root {
      --bg: #f4f7fa;
      --panel: #ffffff;
      --line: #dde6ee;
      --line-strong: #c9d6e1;
      --text: #12263a;
      --muted: #536474;
      --soft: #f8fafc;
      --accent: #184f75;
      --accent-soft: #eef6fb;
      --alert-soft: #fff5f5;
      --warn-soft: #fffaf0;
      --teacher-soft: #f4f8fb;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 24px; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; }
    .pdf-header-logo, .pdf-footer-image { display: none; }
    .page { max-width: 980px; margin: 0 auto; background: var(--panel); border: 1px solid var(--line); border-radius: 22px; overflow: hidden; box-shadow: 0 6px 24px rgba(18, 38, 58, 0.08); }
    .hero { padding: 30px 32px 18px 32px; border-bottom: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%); }
    .hero h1 { margin: 0; font-size: 30px; line-height: 1.2; }
    .hero p { margin: 12px 0 0 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .section { padding: 24px 32px 0 32px; }
    .section:last-child { padding-bottom: 32px; }
    h2 { margin: 0 0 14px 0; font-size: 21px; line-height: 1.3; }
    h3 { margin: 0 0 12px 0; font-size: 17px; line-height: 1.3; }
    .section-kicker { color: var(--muted); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; font-weight: 700; }
    .metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
    .metric-card { border: 1px solid var(--line); border-radius: 16px; background: var(--soft); padding: 14px 16px; min-height: 104px; }
    .teacher-card { background: var(--teacher-soft); }
    .metric-label { color: var(--muted); font-size: 13px; line-height: 1.45; margin-bottom: 8px; }
    .metric-value { font-size: 26px; font-weight: 700; color: var(--text); }
    .metric-value-small { font-size: 22px; }
    .teacher-detail { color: var(--muted); font-size: 13px; line-height: 1.6; margin-top: 8px; }
    .card { border: 1px solid var(--line); border-radius: 16px; background: #fff; padding: 16px 18px; margin-bottom: 14px; }
    .decision-card { background: linear-gradient(180deg, #ffffff 0%, #f8fcff 100%); }
    .executive-lead { font-size: 15px; line-height: 1.8; }
    .teacher-note { color: var(--muted); font-size: 14px; line-height: 1.7; }
    .issue-card { break-inside: avoid; page-break-inside: avoid; }
    .teacher-priority-card { background: #fffdf8; }
    .teacher-priority-layout { display: grid; grid-template-columns: minmax(0, 1fr) 220px; gap: 16px; align-items: start; }
    .teacher-priority-text { min-width: 0; }
    .priority-figure { margin: 0; }
    .priority-figure img { width: 100%; display: block; border: 1px solid var(--line-strong); border-radius: 12px; background: #fff; }
    .priority-caption { margin-top: 6px; color: var(--muted); font-size: 12px; line-height: 1.5; }
    .issue-location { font-weight: 700; font-size: 15px; margin-bottom: 6px; }
    .issue-meta { color: var(--muted); font-size: 13px; line-height: 1.5; margin-bottom: 10px; }
    .issue-message, .issue-recommendation, .reference-detail, li, td, th, .muted { font-size: 14px; line-height: 1.7; }
    .issue-metrics { margin: 10px 0; padding: 10px 12px; border-radius: 12px; background: var(--accent-soft); color: var(--accent); font-size: 13px; line-height: 1.6; }
    .excerpt { margin-top: 10px; padding: 10px 12px; background: var(--soft); border-radius: 12px; color: var(--muted); font-size: 13px; line-height: 1.6; }
    .muted { color: var(--muted); }
    .compact-note { padding: 2px 0 0 0; }
    .data-table { width: 100%; border-collapse: collapse; border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: #fff; }
    .data-table th, .data-table td { border-bottom: 1px solid var(--line); padding: 10px 12px; text-align: left; vertical-align: top; }
    .data-table thead th { background: var(--soft); font-size: 13px; color: var(--muted); font-weight: 700; }
    .row-alert td { background: var(--alert-soft); }
    .row-warn td { background: var(--warn-soft); }
    ul { margin: 0; padding-left: 20px; }
    .summary-list { margin-top: 0; }
    .rule-badge { display: inline-block; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--line-strong); background: var(--soft); font-size: 12px; color: var(--muted); }
    .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
    .annex-intro { background: #fbfcfd; }
    .section-break { padding-top: 28px; }
        @media print {
      @page {
        size: A4;
        margin-top: 46mm;
        margin-right: 14mm;
        margin-bottom: 34mm;
        margin-left: 14mm;
        @top-left { content: element(headerLogo); }
        @bottom-center { content: element(footerImage); }
      }

      body {
        padding: 0;
        background: #fff;
      }

      .page {
        max-width: none;
        border: 0;
        box-shadow: none;
        border-radius: 0;
      }

      .hero, .metric-card, .card, .issue-card {
        break-inside: avoid;
        page-break-inside: avoid;
      }

      .columns {
        display: block;
      }

      .columns > * {
        margin-bottom: 14px;
      }

      .section {
        padding-left: 0;
        padding-right: 0;
      }

      .hero {
        padding-left: 0;
        padding-right: 0;
      }

      .section-break {
        page-break-before: always;
        break-before: page;
      }

      .pdf-header-logo {
        display: block;
        position: running(headerLogo);
        width: 30mm;
        height: 14mm;
        object-fit: contain;
        margin-top: 6mm;
        margin-left: 2mm;
      }

      .pdf-footer-image {
        display: block;
        position: running(footerImage);
        width: 210mm;
        height: 22mm;
        object-fit: cover;
        margin: 0;
      }
    }
    @media (max-width: 900px) { .metric-grid, .columns { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 640px) { body { padding: 12px; } .page { border-radius: 16px; } .hero, .section { padding-left: 18px; padding-right: 18px; } .metric-grid, .columns, .teacher-priority-layout { grid-template-columns: 1fr; } }
    """

    return f"""<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>{styles}</style>
  </head>
  <body>
    {f'<img class="pdf-header-logo" src="{logo_uri}" alt="Logo">' if logo_uri else ''}
    {f'<img class="pdf-footer-image" src="{bottom_uri}" alt="Bottom">' if bottom_uri else ''}
    <main class="page">

        <header class="hero">
  <h1>{html.escape(str(summary.get('title', title)))}</h1>
  <p>{html.escape(str(summary.get('overview', '')))}</p>
  <p><strong>Tiempo estimado de lectura del material:</strong> {html.escape(str(estimated_read_time_human))}</p>
</header>
      </header>

      <section class="section">
        <div class="section-kicker">Resumen ejecutivo</div>
        <h2>Informe para profesorado</h2>
        <div class="card decision-card">
          <h3>Resultado para docencia: {html.escape(str(decision.get('label', '-')))}</h3>
          <p class="executive-lead"><strong>Decisión rápida:</strong> {html.escape(str(decision.get('decision', '-')))}</p>
          <p>{html.escape(str(decision.get('summary', '-')))}</p>
          <p><strong>Foco principal:</strong> {html.escape(str(decision.get('focus', '-')))}</p>
        </div>
      </section>

      <section class="section">
        <h2>Qué conviene corregir primero</h2>
        {build_teacher_priorities_html(priorities)}
      </section>

      <section class="section">
        <h2>Resumen rápido por categorías</h2>
        <div class="metric-grid">{build_teacher_summary_cards_html(categories)}</div>
      </section>

      <section class="section">
        <h2>Qué ya funciona bien</h2>
        <div class="card teacher-note"><ul>{''.join(f'<li>{html.escape(str(item))}</li>' for item in strengths) or '<li>El material presenta una base general utilizable, aunque conviene revisar algunos detalles antes de clase.</li>'}</ul></div>
      </section>

      <section class="section">
        <h2>Recomendaciones prácticas</h2>
        <div class="card"><ul>{teacher_recommendations_html}</ul></div>
        <div class="card teacher-note"><p>A continuación se incluye un anexo técnico con el detalle completo del análisis automático, para consulta y revisión más especializada.</p></div>
      </section>

      <section class="section section-break technical-annex">
        <h2>Anexo técnico</h2>
        <div class="card annex-intro">
          <p>La siguiente sección conserva el detalle técnico del análisis automático para consulta, trazabilidad y revisión más especializada.</p>
        </div>
      </section>

      <section class="section">
        <h2>Recomendaciones generales</h2>
        <div class="card"><ul>{recommendations_html}</ul></div>
      </section>


      <section class="section">
          <h2>Recomendaciones por Dimensión</h2>
          <div class="card teacher-note">
            <p>Abajo se detallan las recomendaciones organizadas por dimensión, junto con las diapositivas o páginas en que se sugiere verificar cada aspecto.</p>
          </div>
        </section>

        {build_dimension_recommendations_html(payload)}






      <section class="section">
        <h2>Métricas de contraste y accesibilidad visual</h2>
        <div class="columns">
          <div class="card">
            <h3>Contraste textual</h3>
            {text_summary_html}
            {text_metrics_html}
          </div>
          <div class="card">
            <h3>Figuras y riesgo CVD</h3>
            {figure_summary_html}
            {figure_metrics_html}
          </div>
        </div>
      </section>

      <section class="section">
        <h2>{html.escape(str(methodology.get('title', 'Metodología y referencias')))}</h2>
        <div class="card">
          <h3>Criterios de referencia</h3>
          <ul>{contrast_rules_html}</ul>
        </div>
        <div class="columns" style="margin-top:18px;">
          <div class="card">
            <h3>Limitaciones de la estimación</h3>
            <ul>{limitations_html or '<li>No se han registrado limitaciones adicionales.</li>'}</ul>
          </div>
          <div class="card">
            <h3>Referencias</h3>
            <ul>{reference_items}</ul>
          </div>
        </div>
      </section>
    </main>
  </body>
</html>
"""


def render_html_to_pdf_es_v2(html_content: str, pdf_path: Path, payload: Optional[dict] = None) -> None:
    try:
        from weasyprint import HTML  # type: ignore
        HTML(string=html_content, base_url=str(pdf_path.parent)).write_pdf(str(pdf_path))
        return
    except Exception:
        pass

    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.enums import TA_LEFT  # type: ignore
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore

        payload = payload or {}
        summary = payload.get("summary", {}) or {}
        visual_metrics = payload.get("visual_metrics", {}) or {}

        intro_message = _intro_message_v2(payload)
        summary_cards = _summary_dimensions_v2(payload)
        # color_summary = _color_findings_summary_v2(payload)
        methodology = payload.get("methodology", {}) or {}
        estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=PDF_PAGE_MARGIN_TOP_MM * mm,
            bottomMargin=PDF_PAGE_MARGIN_BOTTOM_MM * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "AltTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=10,
            alignment=TA_LEFT,
        )
        heading_style = ParagraphStyle(
            "AltHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=8,
            spaceBefore=12,
        )
        body_style = ParagraphStyle(
            "AltBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=4,
        )
        muted_style = ParagraphStyle(
            "AltMuted",
            parent=body_style,
            textColor=colors.HexColor("#536474"),
        )

        story: List[Any] = []
        story.append(Paragraph(html.escape(str(summary.get("title", "Informe de accesibilidad"))), title_style))
        overview_pdf = html.escape(str(summary.get("overview", ""))).replace("\n", "<br/>")
        story.append(Paragraph(overview_pdf, muted_style))
        story.append(
            Paragraph(f"<b>Tiempo estimado de lectura del material:</b> {html.escape(str(estimated_read_time_human))}",
                      body_style))
        story.append(Spacer(1, 8))

        # story.append(Paragraph("Informe de accesibilidad", heading_style))
        intro_message = _intro_message_v2(payload)
        story.append(Paragraph(html.escape(intro_message), body_style))
        story.append(Spacer(1, 4))

        for card in summary_cards:
            story.append(Paragraph(f"<b>{html.escape(str(card['title']))}</b>", body_style))
            story.append(Paragraph(html.escape(str(card["detail"])), muted_style))
            story.append(Spacer(1, 2))

        story.append(Spacer(1, 6))
        # story.append(Paragraph("Indicaciones sobre color y contraste", heading_style))
        # story.append(Paragraph(html.escape(color_summary["message"]), body_style))

        story.append(Paragraph("Recomendaciones por dimensión", heading_style))
        story.append(Paragraph(
            "Abajo se detallan las recomendaciones organizadas por dimensión, indicando junto con las diapositivas o páginas en que se sugiere verificar cada aspecto.",
            body_style
        ))

        for section in build_dimension_recommendations_v2(payload):
            story.append(Paragraph(section["dimension"], heading_style))
            story.append(Paragraph(html.escape(str(section["summary"])), muted_style))
            for item in section["items"]:
                story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                story.append(Paragraph(f"<b>Recomendación:</b> {html.escape(str(item['recommendation']))}", body_style))
                story.append(Paragraph(html.escape(_format_units_for_review(payload, item["units"])), muted_style))
                story.append(Spacer(1, 4))

        # story.append(Paragraph(methodology.get("title", "Metodología y referencias"), heading_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Resumen por diapositivas", heading_style))
        story.append(Paragraph(
            "Abajo se presenta, para cada diapositiva, el conjunto de recomendaciones aplicables identificadas en el análisis.",
            body_style
        ))

        for slide in build_slide_recommendations_summary(payload):
            story.append(Paragraph(slide["label"], heading_style))
            for item in slide["items"]:
                story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                story.append(Paragraph(
                    html.escape(str(item["dimension"])),
                    muted_style
                ))
                story.append(Paragraph(
                    f"<b>Recomendación:</b> {html.escape(str(item['recommendation']))}",
                    body_style
                ))
                story.append(Spacer(1, 4))

        story.append(Paragraph("Criterios y referencias utilizados", heading_style))
        story.append(Paragraph(
            "Las recomendaciones de este informe se basan en estándares internacionales de accesibilidad y en modelos de análisis reconocidos.",
            body_style
        ))

        # Accesibilidad visual y contraste
        story.append(Spacer(1, 4))
        story.append(Paragraph("Accesibilidad visual y contraste", heading_style))

        story.append(Paragraph(
            "W3C WCAG 2.1 — Criterio 1.4.3 (Contraste mínimo)",
            body_style
        ))
        story.append(Paragraph(
            "Referencia: relación de contraste 4.5:1 para texto normal y 3:1 para texto grande.",
            muted_style
        ))

        story.append(Paragraph(
            "W3C WCAG 2.1 — Criterio 1.4.11 (Contraste no textual)",
            body_style
        ))
        story.append(Paragraph(
            "Referencia: relación mínima de 3:1 para elementos visuales relevantes.",
            muted_style
        ))

        # Aplicación a documentos
        story.append(Spacer(1, 4))
        story.append(Paragraph("Aplicación a documentos", heading_style))

        story.append(Paragraph(
            "WCAG2ICT — Aplicación de WCAG a documentos y software no web",
            body_style
        ))
        story.append(Paragraph(
            "Base para el análisis en presentaciones (PDF, PPT, PPTX).",
            muted_style
        ))

        # Percepción del color
        story.append(Spacer(1, 4))
        story.append(Paragraph("Percepción del color", heading_style))

        story.append(Paragraph(
            "Brettel et al. (1997)",
            body_style
        ))
        story.append(Paragraph(
            "Modelo de simulación de visión del color (protanopia, deuteranopia, tritanopia).",
            muted_style
        ))

        story.append(Paragraph(
            "Machado et al. (2009)",
            body_style
        ))
        story.append(Paragraph(
            "Modelo para simulación de deficiencias en la percepción del color.",
            muted_style
        ))
        doc.build(
            story,
            onFirstPage=_draw_pdf_branding,
            onLaterPages=_draw_pdf_branding,
        )
        return

    except Exception as exc:
        raise RuntimeError(f"No se pudo generar el PDF alternativo del informe: {exc}")


def render_html_to_pdf(html_content: str, pdf_path: Path, payload: Optional[dict] = None) -> None:
    """Genera un PDF a partir del HTML del informe.

    Intenta usar WeasyPrint para conservar el estilo del HTML. Si no está
    disponible, recurre a un fallback estructurado con ReportLab para no romper
    el flujo del sistema y mantener mejor paginación que un volcado lineal.
    """
    try:
        from weasyprint import HTML  # type: ignore

        HTML(string=html_content, base_url=str(pdf_path.parent)).write_pdf(str(pdf_path))
        return
    except Exception:
        pass

    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.enums import TA_LEFT  # type: ignore
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, \
            TableStyle  # type: ignore

        payload = payload or {}
        summary = payload.get("summary", {}) or {}
        visual_metrics = payload.get("visual_metrics", {}) or {}
        estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")
        all_issues = payload.get("issues", []) or []
        issues = [issue for issue in all_issues if issue.get("category_code") != "processing_note"]
        recommendations = clean_list_items(payload.get("recommendations", []) or [])
        methodology = payload.get("methodology", {}) or {}

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=PDF_PAGE_MARGIN_TOP_MM * mm,
            bottomMargin=PDF_PAGE_MARGIN_BOTTOM_MM * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "AludaTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=10,
            alignment=TA_LEFT,
        )
        heading_style = ParagraphStyle(
            "AludaHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=8,
            spaceBefore=12,
        )
        body_style = ParagraphStyle(
            "AludaBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#12263A"),
            spaceAfter=4,
        )
        muted_style = ParagraphStyle("AludaMuted", parent=body_style, textColor=colors.HexColor("#536474"))

        story: List[Any] = []
        story.append(Paragraph(html.escape(str(summary.get("title", "Informe documental"))), title_style))
        story.append(Paragraph(html.escape(str(summary.get("overview", ""))), muted_style))
        story.append(
            Paragraph(f"<b>Tiempo estimado de lectura del material:</b> {html.escape(str(estimated_read_time_human))}",
                      body_style))
        story.append(Spacer(1, 6))

        teacher_issues = _filter_reportable_issues(payload)
        teacher_decision = _teacher_decision_block(payload, teacher_issues)
        teacher_priorities = _build_teacher_priorities(payload, teacher_issues, max_items=3)
        teacher_categories = _build_teacher_categories(payload, teacher_issues)
        teacher_strengths = _build_teacher_strengths(payload, teacher_categories)

        story.append(Paragraph("Informe de accessibilidad", heading_style))
        story.append(
            Paragraph(f"<b>Resultado para docencia:</b> {html.escape(str(teacher_decision.get('label', '-')))}",
                      body_style))
        story.append(
            Paragraph(f"<b>Decisión rápida:</b> {html.escape(str(teacher_decision.get('decision', '-')))}", body_style))
        story.append(Paragraph(html.escape(str(teacher_decision.get('summary', '-'))), body_style))
        story.append(
            Paragraph(f"<b>Foco principal:</b> {html.escape(str(teacher_decision.get('focus', '-')))}", body_style))

        story.append(Paragraph("Qué conviene corregir primero", heading_style))
        if teacher_priorities:
            for item in teacher_priorities:
                story.append(Paragraph(f"<b>{html.escape(str(item.get('location', '-')))}</b>", body_style))
                story.append(Paragraph(f"<b>Área:</b> {html.escape(str(item.get('area', '-')))}", muted_style))
                story.append(Paragraph(f"<b>Qué ocurre:</b> {html.escape(str(item.get('what', '-')))}", body_style))
                story.append(Paragraph(f"<b>Qué hacer:</b> {html.escape(str(item.get('action', '-')))}", body_style))
                preview_path = item.get("preview_image_path")
                if preview_path:
                    abs_preview = pdf_path.parent / str(preview_path)
                    if abs_preview.exists():
                        try:
                            img = RLImage(str(abs_preview))
                            max_w = 72 * mm
                            max_h = 48 * mm
                            scale = min(max_w / float(img.imageWidth or max_w), max_h / float(img.imageHeight or max_h),
                                        1.0)
                            img.drawWidth = float(img.imageWidth or max_w) * scale
                            img.drawHeight = float(img.imageHeight or max_h) * scale
                            story.append(Spacer(1, 2))
                            story.append(img)
                            if item.get("preview_caption"):
                                story.append(Paragraph(html.escape(str(item.get("preview_caption"))), muted_style))
                        except Exception:
                            pass
                story.append(Spacer(1, 4))
        else:
            story.append(
                Paragraph("No se detectaron incidencias prioritarias en este análisis automático.", body_style))

        story.append(Paragraph("Resumen rápido por categorías", heading_style))
        for category in teacher_categories:
            story.append(Paragraph(
                f"<b>{html.escape(str(category.get('title', '-')))}</b>: {html.escape(str(category.get('status', '-')))}",
                body_style))
            story.append(Paragraph(html.escape(str(category.get('detail', '-'))), muted_style))

        story.append(Paragraph("Qué ya funciona bien", heading_style))
        if teacher_strengths:
            for item in teacher_strengths:
                story.append(Paragraph(f"• {html.escape(str(item))}", body_style))
        else:
            story.append(Paragraph(
                "El material presenta una base general utilizable, aunque conviene revisar algunos detalles antes de clase.",
                muted_style))

        story.append(Paragraph("Recomendaciones prácticas", heading_style))
        for item in recommendations[:5]:
            story.append(Paragraph(f"• {html.escape(str(item))}", body_style))
        story.append(Paragraph(
            "A continuación se incluye un anexo técnico con el detalle completo del análisis automático, para consulta y revisión más especializada.",
            muted_style))
        story.append(Spacer(1, 8))

        totals = summary.get("totals", {}) or {}
        severity_totals = summary.get("severity_totals", {}) or {}
        story.append(Paragraph("Anexo técnico", heading_style))
        summary_table = Table(
            [
                ["Unidades", totals.get("units_analyzed", "-")],
                ["Alertas visuales", totals.get("reportable_issue_count", totals.get("issue_count", "-"))],
                ["Notas de procesamiento", totals.get("processing_note_count", 0)],
                ["Bloques textuales", totals.get("text_blocks_analyzed", "-")],
                ["Figuras analizadas", totals.get("figures_analyzed", "-")],
                ["Severidad alta/media/baja",
                 f"{severity_totals.get('alta', 0)}/{severity_totals.get('media', 0)}/{severity_totals.get('baja', 0)}"],
            ],
            colWidths=[54 * mm, 118 * mm],
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DDE6EE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE6EE")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#12263A")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(Paragraph("Resumen ejecutivo", heading_style))
        story.append(summary_table)

        """story.append(Paragraph("Incidencias prioritarias", heading_style))
        if issues:
            for issue in issues:
                lines = [
                    Paragraph(f"<b>{html.escape(str(issue.get('location', '-')))}</b>", body_style),
                    Paragraph(html.escape(" · ".join(str(x) for x in [issue.get("category", "-"), issue.get("severity", "-")] if x)), muted_style),
                    Paragraph(html.escape(str(issue.get("message", "-"))), body_style),
                    Paragraph(f"<b>Recomendación:</b> {html.escape(str(issue.get('recommendation', '-')))}", body_style),
                ]
                metric_parts = []
                if issue.get("ratio") is not None and issue.get("threshold") is not None:
                    metric_parts.append(f"Ratio {issue.get('ratio')}:1")
                    metric_parts.append(f"Umbral {issue.get('threshold')}:1")
                if issue.get("score_ratio") is not None:
                    metric_parts.append(f"Score CVD {issue.get('score_ratio')}")
                if issue.get("bbox_human"):
                    metric_parts.append(f"Zona {issue.get('bbox_human')}")
                if metric_parts:
                    lines.append(Paragraph(html.escape(" · ".join(metric_parts)), muted_style))
                if issue.get("excerpt"):
                    lines.append(Paragraph(f"<b>Extracto:</b> {html.escape(str(issue.get('excerpt')))}", muted_style))
                if issue.get("reference_code"):
                    lines.append(Paragraph(f"<b>Referencia:</b> {html.escape(str(issue.get('reference_code')))}", muted_style))
                issue_table = Table([[lines]], colWidths=[178 * mm])
                issue_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DDE6EE")),
                            ("PADDING", (0, 0), (-1, -1), 10),
                        ]
                    )
                )
                story.append(issue_table)
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("No se detectaron incidencias visuales prioritarias en este análisis automático.", body_style))"""
        story.append(Paragraph("Recomendaciones generales", heading_style))
        for item in recommendations:
            story.append(Paragraph(f"• {html.escape(str(item))}", body_style))

        story.append(Paragraph("Recomendaciones por Dimensión", heading_style))
        story.append(Paragraph(
            "Abajo se detallan las recomendaciones organizadas por dimensión, junto con las diapositivas o páginas en que se sugiere verificar cada aspecto.",
            body_style
        ))

        for section in build_dimension_recommendations(payload):
            story.append(Paragraph(section["dimension"], heading_style))

            for item in section["items"]:
                story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                story.append(Paragraph(
                    f"<b>Recomendación:</b> {html.escape(str(item['recommendation']))}",
                    body_style
                ))
                story.append(Paragraph(
                    html.escape(_format_units_for_review(payload, item["units"])),
                    muted_style
                ))
                story.append(Spacer(1, 4))

        story.append(Paragraph("Métricas visuales", heading_style))
        text_compact_note = build_text_metric_compact_note(visual_metrics)
        figure_compact_note = build_figure_metric_compact_note(visual_metrics)

        if text_compact_note:
            story.append(Paragraph(f"• Contraste textual: {html.escape(text_compact_note)}", body_style))
        else:
            for line in build_metric_summary_lines(visual_metrics.get("text_metrics_summary", {}) or {}, "text"):
                story.append(Paragraph(f"• Contraste textual: {html.escape(line)}", body_style))
            text_rows = _select_relevant_metric_rows(visual_metrics.get("text_metric_samples", []) or [])
            if text_rows:
                story.append(Paragraph("Muestras de contraste textual", heading_style))
                table = Table(
                    [["Ubicación", "Bloque", "Estado", "Ratio", "Umbral", "Zona"]] + [
                        [
                            str(row.get("location", "-")),
                            str(row.get("text_block_index", "-")),
                            str(row.get("status", "-")),
                            str(row.get("ratio", "-")),
                            str(row.get("threshold", "-")),
                            str(row.get("bbox_human", "-")),
                        ]
                        for row in text_rows
                    ],
                    colWidths=[48 * mm, 14 * mm, 28 * mm, 18 * mm, 18 * mm, 46 * mm],
                    repeatRows=1,
                )
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDE6EE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDE6EE")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(table)

        if figure_compact_note:
            story.append(Paragraph(f"• Figuras/CVD: {html.escape(figure_compact_note)}", body_style))
        else:
            for line in build_metric_summary_lines(visual_metrics.get("figure_metrics_summary", {}) or {}, "figure"):
                story.append(Paragraph(f"• Figuras/CVD: {html.escape(line)}", body_style))
            figure_rows = _select_relevant_metric_rows(visual_metrics.get("figure_metric_samples", []) or [])
            if figure_rows:
                story.append(Paragraph("Muestras de figuras y CVD", heading_style))
                table = Table(
                    [["Ubicación", "Figura", "Estado", "Ratio", "Peor CVD", "Zona"]] + [
                        [
                            str(row.get("location", "-")),
                            str(row.get("figure_index", "-")),
                            str(row.get("status", "-")),
                            str(row.get("ratio", "-")),
                            str(row.get("worst_cvd_ratio", "-")),
                            str(row.get("bbox_human", "-")),
                        ]
                        for row in figure_rows
                    ],
                    colWidths=[52 * mm, 14 * mm, 26 * mm, 18 * mm, 22 * mm, 40 * mm],
                    repeatRows=1,
                )
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDE6EE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDE6EE")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(table)

        processing_notes = clean_list_items(visual_metrics.get("processing_notes", []) or [])
        if processing_notes:
            story.append(Paragraph("Notas de procesamiento", heading_style))
            for note in processing_notes:
                story.append(Paragraph(f"• {html.escape(str(note))}", muted_style))

        story.append(Paragraph(methodology.get("title", "Metodología y referencias"), heading_style))
        for rule in methodology.get("contrast_rules", []) or []:
            rule_label = html.escape(str(rule.get("label", "-")))
            detail = html.escape(str(rule.get("details", "")))
            ref = html.escape(str(rule.get("reference_code", "-")))
            threshold = rule.get("threshold")
            threshold_text = f" Umbral: {threshold}:1." if threshold is not None else ""
            story.append(Paragraph(
                f"<b>{rule_label}</b> · {html.escape(str(rule.get('metric_type', '-')))} · {ref}.{threshold_text}",
                body_style))
            if detail:
                story.append(Paragraph(detail, muted_style))
        limitations = clean_list_items(methodology.get("limitations", []) or [])
        if limitations:
            story.append(Paragraph("Limitaciones de la estimación", heading_style))
            for item in limitations:
                story.append(Paragraph(f"• {html.escape(str(item))}", muted_style))
        refs = methodology.get("references", []) or []
        if refs:
            story.append(Paragraph("Referencias", heading_style))
            for ref in refs:
                story.append(Paragraph(f"• {html.escape(str(ref.get('title', '-')))}", body_style))
                if ref.get("details"):
                    story.append(Paragraph(html.escape(str(ref.get("details"))), muted_style))

        doc.build(
            story,
            onFirstPage=_draw_pdf_branding,
            onLaterPages=_draw_pdf_branding,
        )
        return
    except Exception as exc:
        raise RuntimeError(f"No se pudo generar el PDF del informe: {exc}")


# ---------------------------------------------------------
# PDF alternativo en español
# trecho añadido o modificado
# sección fija: Criterios y referencias utilizados
# ---------------------------------------------------------

def render_report_html_i18n(payload: dict, title: str, lang: str) -> str:
    summary = payload.get("summary", {}) or {}
    visual_metrics = payload.get("visual_metrics", {}) or {}
    methodology = payload.get("methodology", {}) or {}

    branding_assets = get_pdf_branding_assets()
    logo_uri = branding_assets["logo"].as_uri() if branding_assets["logo"] else ""
    bottom_uri = branding_assets["bottom"].as_uri() if branding_assets["bottom"] else ""

    reportable_count = (summary.get("totals", {}) or {}).get("reportable_issue_count", 0)
    intro_message = _ri(lang, "intro_with_issues") if reportable_count else _ri(lang, "intro_no_issues")
    estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")

    summary_cards = [
        {
            "title": _ui(lang, "dimension_legibility"),
            "detail": _ri(lang, "dimension_summaries", "legibility"),
        },
        {
            "title": _ui(lang, "dimension_contrast"),
            "detail": _ri(lang, "dimension_summaries", "contrast"),
        },
        {
            "title": _ui(lang, "dimension_organization"),
            "detail": _ri(lang, "dimension_summaries", "organization"),
        },
        {
            "title": _ui(lang, "dimension_images"),
            "detail": _ri(lang, "dimension_summaries", "images"),
        },
    ]

    summary_cards_html = "".join(
        f"""
        <div class="metric-card teacher-card">
          <div class="metric-label">{html.escape(str(card['title']))}</div>
          <div class="teacher-detail">{html.escape(str(card['detail']))}</div>
        </div>
        """
        for card in summary_cards
    )

    limitations_html = "".join(
        f"<li>{html.escape(str(item))}</li>"
        for item in clean_list_items(methodology.get("limitations", []) or [])
    )

    reference_items = "".join(
        f"<li><strong>{html.escape(str(ref.get('title', '-')))}</strong>"
        + (f"<div class='reference-detail'>{html.escape(str(ref.get('details', '')))}</div>" if ref.get("details") else "")
        + "</li>"
        for ref in (methodology.get("references", []) or [])
    )

    styles = """
    :root {
      --bg: #f4f7fa;
      --panel: #ffffff;
      --line: #dde6ee;
      --line-strong: #c9d6e1;
      --text: #12263a;
      --muted: #536474;
      --soft: #f8fafc;
      --teacher-soft: #f4f8fb;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 24px; background: var(--bg); color: var(--text); font-family: Arial, Helvetica, sans-serif; }
    .pdf-header-logo, .pdf-footer-image { display: none; }
    .page { max-width: 980px; margin: 0 auto; background: var(--panel); border: 1px solid var(--line); border-radius: 22px; overflow: hidden; box-shadow: 0 6px 24px rgba(18, 38, 58, 0.08); }
    .hero { padding: 30px 32px 18px 32px; border-bottom: 1px solid var(--line); background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%); }
    .hero h1 { margin: 0; font-size: 30px; line-height: 1.2; }
    .hero p { margin: 10px 0 0 0; color: var(--muted); font-size: 15px; line-height: 1.7; }
    .hero-overview { white-space: pre-line; }
    .section { padding: 24px 32px 0 32px; }
    .section:last-child { padding-bottom: 32px; }
    h2 { margin: 0 0 14px 0; font-size: 21px; line-height: 1.3; }
    h3 { margin: 0 0 12px 0; font-size: 17px; line-height: 1.3; }
    .section-kicker { color: var(--muted); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; font-weight: 700; }
    .metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    .metric-card { border: 1px solid var(--line); border-radius: 16px; background: var(--soft); padding: 14px 16px; min-height: 90px; }
    .teacher-card { background: var(--teacher-soft); }
    .metric-label { color: var(--text); font-size: 15px; font-weight: 700; line-height: 1.4; margin-bottom: 8px; }
    .teacher-detail { color: var(--muted); font-size: 14px; line-height: 1.7; }
    .card { border: 1px solid var(--line); border-radius: 16px; background: #fff; padding: 16px 18px; margin-bottom: 14px; }
    .decision-card { background: linear-gradient(180deg, #ffffff 0%, #f8fcff 100%); }
    .dimension-summary { color: var(--muted); font-size: 14px; line-height: 1.7; margin: 0 0 14px 0; }
    .slide-summary-card { border: 1px solid var(--line); border-radius: 18px; background: #fff; padding: 18px 20px; }
    .slide-rec-item { border: 1px solid var(--line); border-radius: 14px; background: var(--soft); padding: 14px 16px; margin-bottom: 12px; }
    .slide-rec-metric { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
    .slide-rec-dimension { color: var(--muted); font-size: 13px; line-height: 1.6; margin-bottom: 8px; }
    .slide-rec-text, .reference-detail, li { font-size: 14px; line-height: 1.7; }
    .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
    @media print {
      @page {
        size: A4;
        margin-top: 46mm;
        margin-right: 14mm;
        margin-bottom: 34mm;
        margin-left: 14mm;
        @top-left { content: element(headerLogo); }
        @bottom-center { content: element(footerImage); }
      }
      body { padding: 0; background: #fff; }
      .page { max-width: none; border: 0; box-shadow: none; border-radius: 0; }
      .card, .metric-card, .slide-summary-card, .slide-rec-item { break-inside: avoid; page-break-inside: avoid; }
      .pdf-header-logo {
        display: block;
        position: running(headerLogo);
        width: 30mm;
        height: 14mm;
        object-fit: contain;
        margin-top: 6mm;
        margin-left: 2mm;
      }
      .pdf-footer-image {
        display: block;
        position: running(footerImage);
        width: 210mm;
        height: 22mm;
        object-fit: cover;
        margin: 0;
      }
      .columns { display: block; }
      .columns > * { margin-bottom: 14px; }
      .section { padding-left: 0; padding-right: 0; }
    }
    """

    return f"""<!DOCTYPE html>
<html lang="{html.escape(lang)}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>{styles}</style>
  </head>
  <body>
    {f'<img class="pdf-header-logo" src="{logo_uri}" alt="Logo">' if logo_uri else ''}
    {f'<img class="pdf-footer-image" src="{bottom_uri}" alt="Bottom">' if bottom_uri else ''}

    <main class="page">
      <header class="hero">
        <h1>{html.escape(str(title))}</h1>
        <p class="hero-overview">{html.escape(str(summary.get('overview', '')))}</p>
        <p><strong>{html.escape(_ui(lang, "estimated_reading_time"))}</strong> {html.escape(str(estimated_read_time_human))}</p>
      </header>

      <section class="section">
        <div class="section-kicker">{html.escape(_ui(lang, "executive_summary"))}</div>
        <h2>{html.escape(_ui(lang, "teacher_report"))}</h2>
        <div class="card decision-card">
          <p>{html.escape(intro_message)}</p>
          <div class="metric-grid">{summary_cards_html}</div>
        </div>
      </section>

      <section class="section">
        <h2>{html.escape(_ui(lang, "recommendations_by_dimension"))}</h2>
        <div class="card">
          <p>{html.escape(_ui(lang, "recommendations_by_dimension_intro"))}</p>
        </div>
      </section>

      {build_dimension_recommendations_html_i18n(payload, lang=lang)}

      <section class="section">
        <h2>{html.escape(_ui(lang, "slide_summary"))}</h2>
        <div class="card">
          <p>{html.escape(_ui(lang, "slide_summary_intro"))}</p>
        </div>
      </section>

      {build_slide_recommendations_html_i18n(payload, lang=lang)}

      {build_fixed_criteria_section_html_i18n(lang)}

      <section class="section">
        <div class="columns" style="margin-top:18px;">
          <div class="card">
            <h3>{html.escape(_ui(lang, "limitations"))}</h3>
            <ul>{limitations_html or '<li>-</li>'}</ul>
          </div>
          <div class="card">
            <h3>{html.escape(_ui(lang, "references"))}</h3>
            <ul>{reference_items}</ul>
          </div>
        </div>
      </section>
    </main>
  </body>
</html>
"""

def render_html_to_pdf_i18n(html_content: str, pdf_path: Path, payload: Optional[dict] = None, lang: str = "es") -> None:
    try:
        from weasyprint import HTML  # type: ignore
        HTML(string=html_content, base_url=str(pdf_path.parent)).write_pdf(str(pdf_path))
        return
    except Exception:
        pass

    try:
        from reportlab.lib import colors  # type: ignore
        from reportlab.lib.enums import TA_LEFT  # type: ignore
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer  # type: ignore

        payload = payload or {}
        summary = payload.get("summary", {}) or {}
        visual_metrics = payload.get("visual_metrics", {}) or {}
        methodology = payload.get("methodology", {}) or {}

        reportable_count = (summary.get("totals", {}) or {}).get("reportable_issue_count", 0)
        intro_message = _ri(lang, "intro_with_issues") if reportable_count else _ri(lang, "intro_no_issues")
        estimated_read_time_human = visual_metrics.get("estimated_read_time_human", "unavailable")

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=PDF_PAGE_MARGIN_TOP_MM * mm,
            bottomMargin=PDF_PAGE_MARGIN_BOTTOM_MM * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("AltTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#12263A"), spaceAfter=10, alignment=TA_LEFT)
        heading_style = ParagraphStyle("AltHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#12263A"), spaceAfter=8, spaceBefore=12)
        body_style = ParagraphStyle("AltBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#12263A"), spaceAfter=4)
        muted_style = ParagraphStyle("AltMuted", parent=body_style, textColor=colors.HexColor("#536474"))

        story: List[Any] = []

        overview_pdf = html.escape(str(summary.get("overview", ""))).replace("\n", "<br/>")
        story.append(Paragraph(html.escape(str(_ri(lang, "title"))), title_style))
        story.append(Paragraph(overview_pdf, muted_style))
        story.append(Paragraph(f"<b>{html.escape(_ui(lang, 'estimated_reading_time'))}</b> {html.escape(str(estimated_read_time_human))}", body_style))
        story.append(Spacer(1, 8))

        story.append(Paragraph(_ui(lang, "teacher_report"), heading_style))
        story.append(Paragraph(html.escape(intro_message), body_style))
        story.append(Spacer(1, 4))

        for card in [
            (_ui(lang, "dimension_legibility"), _ri(lang, "dimension_summaries", "legibility")),
            (_ui(lang, "dimension_contrast"), _ri(lang, "dimension_summaries", "contrast")),
            (_ui(lang, "dimension_organization"), _ri(lang, "dimension_summaries", "organization")),
            (_ui(lang, "dimension_images"), _ri(lang, "dimension_summaries", "images")),
        ]:
            story.append(Paragraph(f"<b>{html.escape(card[0])}</b>", body_style))
            story.append(Paragraph(html.escape(card[1]), muted_style))

        story.append(Paragraph(_ui(lang, "recommendations_by_dimension"), heading_style))
        story.append(Paragraph(_ui(lang, "recommendations_by_dimension_intro"), body_style))

        for section in build_dimension_recommendations_i18n(payload, lang=lang):
            story.append(Paragraph(section["dimension"], heading_style))
            if section.get("summary"):
                story.append(Paragraph(html.escape(str(section["summary"])), muted_style))
            for item in section["items"]:
                story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                story.append(Paragraph(f"<b>{html.escape(_ui(lang, 'recommendation'))}</b> {html.escape(str(item['recommendation']))}", body_style))
                story.append(Paragraph(html.escape(_format_units_for_review_i18n(payload, item["units"], lang)), muted_style))
                story.append(Spacer(1, 4))

        story.append(Paragraph(_ui(lang, "slide_summary"), heading_style))
        story.append(Paragraph(_ui(lang, "slide_summary_intro"), body_style))

        for slide in build_slide_recommendations_summary_i18n(payload, lang=lang):
            story.append(Paragraph(slide["label"], heading_style))
            for item in slide["items"]:
                story.append(Paragraph(f"<b>{html.escape(str(item['metric']))}</b>", body_style))
                story.append(Paragraph(html.escape(str(item["dimension"])), muted_style))
                story.append(Paragraph(f"<b>{html.escape(_ui(lang, 'recommendation'))}</b> {html.escape(str(item['recommendation']))}", body_style))
                story.append(Spacer(1, 4))

        c = _ri(lang, "fixed_criteria")
        story.append(Paragraph(c["section_title"], heading_style))
        story.append(Paragraph(c["intro"], body_style))
        story.append(Paragraph(c["visual_contrast_title"], heading_style))
        story.append(Paragraph(f"<b>{html.escape(c['wcag_143_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["wcag_143_detail"]), muted_style))
        story.append(Paragraph(f"<b>{html.escape(c['wcag_1411_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["wcag_1411_detail"]), muted_style))
        story.append(Paragraph(c["documents_title"], heading_style))
        story.append(Paragraph(f"<b>{html.escape(c['wcag2ict_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["wcag2ict_detail"]), muted_style))
        story.append(Paragraph(c["color_title"], heading_style))
        story.append(Paragraph(f"<b>{html.escape(c['brettel_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["brettel_detail"]), muted_style))
        story.append(Paragraph(f"<b>{html.escape(c['machado_title'])}</b>", body_style))
        story.append(Paragraph(html.escape(c["machado_detail"]), muted_style))

        limitations = clean_list_items(methodology.get("limitations", []) or [])
        if limitations:
            story.append(Paragraph(_ui(lang, "limitations"), heading_style))
            for item in limitations:
                story.append(Paragraph(f"• {html.escape(str(item))}", muted_style))

        refs = methodology.get("references", []) or []
        if refs:
            story.append(Paragraph(_ui(lang, "references"), heading_style))
            for ref in refs:
                story.append(Paragraph(f"• {html.escape(str(ref.get('title', '-')))}", body_style))
                if ref.get("details"):
                    story.append(Paragraph(html.escape(str(ref.get("details"))), muted_style))

        doc.build(story, onFirstPage=_draw_pdf_branding, onLaterPages=_draw_pdf_branding)
        return

    except Exception as exc:
        raise RuntimeError(f"No se pudo generar el PDF del informe: {exc}")


def save_report_variants_i18n(
    payload: dict,
    stem: str,
    output_dir: Path,
    variant: str,
    lang: str,
) -> Dict[str, str]:
    txt_name = f"{stem}.{variant}.txt"
    json_name = f"{stem}.{variant}.json"
    html_name = f"{stem}.{variant}.html"
    pdf_name = f"{stem}.{variant}.pdf"

    txt_path = output_dir / txt_name
    json_path = output_dir / json_name
    html_path = output_dir / html_name
    pdf_path = output_dir / pdf_name

    html_content = render_report_html_i18n(
        payload,
        title=_ri(lang, "title"),
        lang=lang,
    )

    write_text(txt_path, render_report_text(payload))
    write_json(json_path, payload)
    write_text(html_path, html_content)
    render_html_to_pdf_i18n(html_content, pdf_path, payload=payload, lang=lang)

    return {
        "txt": txt_name,
        "json": json_name,
        "html": html_name,
        "pdf": pdf_name,
    }


# ---------------------------------------------------------
# MAIN PROCESS
# ---------------------------------------------------------

def process_document(
    input_file: Path,
    output_dir: Path,
    task_id: str,
    source_lang: Optional[str],
    target_langs: List[str],
    use_ocr: bool,
    max_translation_chars: int,
    preloaded_nllb=None,
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
        message="Inicializando tarea documental",
        extra={"input_file": str(input_file)},
    )

    logger.info("%s", APP_NAME)
    logger.info("Archivo de entrada: %s", input_file)
    logger.info("Directorio de salida: %s", output_dir)

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=20,
        stage="extraction",
        message="Extrayendo contenido del documento",
    )

    # ---------------------------------------------------------
    # Extracción documental
    # ---------------------------------------------------------
    document_type, units = extract_document_units(
        input_file,
        use_ocr=use_ocr,
        logger=logger,
    )

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=35,
        stage="structured_accessibility",
        message="Generando métricas estructuradas por diapositiva/página",
    )

    csv_outputs = save_accessibility_csv_outputs(
        input_file=input_file,
        analyzed_file=input_file,
        document_type=document_type,
        units=units,
        output_dir=output_dir,
    )
    logger.info("Archivos CSV estructurados generados: %s", csv_outputs)

    full_text = normalize_whitespace("\n\n".join(unit.get("text", "") for unit in units))
    detected_lang = detect_language_heuristic(full_text)
    manual_source_lang = normalize_lang_code(source_lang)
    used_source_lang = manual_source_lang or detected_lang or "es"

    logger.info("Idioma detectado/usado para metadatos: %s", used_source_lang)

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=50,
        stage="analysis",
        message="Analizando accesibilidad documental",
        extra={"source_language_used": used_source_lang},
    )

    # ---------------------------------------------------------
    # Análisis único del documento
    # ---------------------------------------------------------
    report_base = analyze_document(
        units,
        document_type=document_type,
        input_filename=input_file.name,
    )

    original_payload: Dict[str, Any] = {
        "task_id": task_id,
        "input_file": str(input_file),
        "input_filename": input_file.name,
        "document_type": document_type,
        "source_language_requested": manual_source_lang,
        "source_language_detected": detected_lang,
        "source_language_used": used_source_lang,
        "report_language": "es",
        **report_base,
    }

    report_generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    original_payload["report_generated_at"] = report_generated_at

    # Opcional: mantener por compatibilidad.
    # Si tus renders master no usan esto, podés eliminar este bloque.
    try:
        original_payload["teacher_priority_assets"] = _build_teacher_priority_assets(
            input_file=input_file,
            output_dir=output_dir,
            payload=original_payload,
            logger=logger,
            max_items=3,
        )
    except Exception as exc:
        logger.warning("No se pudieron generar teacher_priority_assets: %s", exc)

    # ---------------------------------------------------------
    # Selección de idiomas de salida
    # ---------------------------------------------------------
    requested_langs: List[str] = []

    for lang in target_langs:
        lang = normalize_lang_code(lang)
        if lang in ALLOWED_TARGETS and lang not in requested_langs:
            requested_langs.append(lang)

    if not requested_langs:
        requested_langs = ["es", "en", "pt", "gl"]

    write_status(
        output_dir,
        task_id=task_id,
        state="processing",
        progress=75,
        stage="translation",
        message="Generando informes multilingües",
        extra={"source_language_used": used_source_lang},
    )

    # ---------------------------------------------------------
    # Generación liviana de variantes por idioma
    # ---------------------------------------------------------
    original_payload_for_report = deepcopy(original_payload)
    original_payload_for_report["report_language"] = "es"
    original_payload_for_report["target_language"] = "es"
    original_payload_for_report["summary"]["overview"] = build_localized_overview(original_payload_for_report, "es")

    original_outputs = save_report_variants_master(
        payload=original_payload_for_report,
        stem=stem,
        output_dir=output_dir,
        variant="original",
        lang="es",
    )
    logger.info("Informe original generado.")

    outputs_by_lang: Dict[str, Dict[str, str]] = {}

    for idx, lang in enumerate(requested_langs, start=1):
        logger.info("Generando informe %s/%s: %s", idx, len(requested_langs), lang)

        localized_payload = deepcopy(original_payload)
        localized_payload["report_language"] = lang
        localized_payload["target_language"] = lang
        localized_payload["summary"]["overview"] = build_localized_overview(localized_payload, lang)

        outputs_by_lang[lang] = save_report_variants_master(
            payload=localized_payload,
            stem=stem,
            output_dir=output_dir,
            variant=lang,
            lang=lang,
        )

    # Mantiene el contrato del código base y conserva el nuevo índice liviano.
    translated_outputs = outputs_by_lang

    # ---------------------------------------------------------
    # Resultado final
    # ---------------------------------------------------------
    success_message = "Procesamiento documental completado correctamente."

    result_payload = {
        "ok": True,
        "task_id": task_id,
        "status": "finished",
        "message": success_message,
        "error": None,
        "input_file": str(input_file),
        "document_type": document_type,
        "source_language_requested": manual_source_lang,
        "source_language_detected": detected_lang,
        "source_language_used": used_source_lang,
        "target_languages_requested": requested_langs,
        "outputs": collect_output_filenames(output_dir),
        "original": original_outputs,
        "translations": translated_outputs,
        "reports_by_language": outputs_by_lang,
        "accessibility_csv": csv_outputs,
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

    logger.info("Proceso documental completado correctamente.")
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
        return process_document(
            input_file=input_file,
            output_dir=output_dir,
            task_id=args.task_id,
            source_lang=args.source_lang,
            target_langs=args.translate_to,
            use_ocr=bool(args.ocr),
            max_translation_chars=args.max_translation_chars,
        )
    except Exception as exc:
        ensure_dir(output_dir)
        error_message = f"Error al procesar el documento: {exc}"
        write_json(
            output_dir / "result.json",
            {
                "ok": False,
                "task_id": args.task_id,
                "status": "error",
                "message": error_message,
                "error": str(exc),
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
                "error": str(exc),
                "result_file": "result.json",
            },
        )
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
