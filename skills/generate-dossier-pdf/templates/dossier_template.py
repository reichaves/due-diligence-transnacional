#!/usr/bin/env python3
"""
Purpose: ReportLab styles and layout utilities for the due-diligence dossier PDF.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-05-01
Dependencies: reportlab>=4.1

This module is imported by generate_report.py — not run directly.
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import TableStyle

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2.5 * cm

# ---------------------------------------------------------------------------
# Colour palette (journalistic — minimal, no bright colours)
# ---------------------------------------------------------------------------

COLOR_DARK_BLUE = colors.HexColor("#1a2e4a")
COLOR_MID_GRAY = colors.HexColor("#555555")
COLOR_LIGHT_GRAY = colors.HexColor("#eeeeee")
COLOR_BORDER = colors.HexColor("#cccccc")
COLOR_CONFIRMED = colors.HexColor("#1a7a3c")       # green — confirmado
COLOR_PROBABLE = colors.HexColor("#7a5a00")         # amber — provavel
COLOR_INDICATION = colors.HexColor("#7a1a1a")       # dark red — indicio
COLOR_NOT_FOUND = colors.HexColor("#444444")        # gray — nao-encontrado
COLOR_DISCLAIMER_BG = colors.HexColor("#fff8e1")    # warm yellow — disclaimer box bg
COLOR_DISCLAIMER_BORDER = colors.HexColor("#e65100") # deep orange — disclaimer box border
COLOR_DISCLAIMER_TITLE = colors.HexColor("#bf360c")  # dark red-orange — disclaimer heading


def confidence_color(level: str) -> colors.Color:
    """Return display color for a confidence level string."""
    return {
        "confirmado": COLOR_CONFIRMED,
        "provavel": COLOR_PROBABLE,
        "indicio": COLOR_INDICATION,
        "nao-encontrado": COLOR_NOT_FOUND,
    }.get(level, COLOR_NOT_FOUND)


def confidence_label(level: str, lang: str = "pt-BR") -> str:
    """Return display label for a confidence level in the given language."""
    labels: dict[str, dict[str, str]] = {
        "pt-BR": {
            "confirmado": "CONFIRMADO",
            "provavel": "PROVAVEL",
            "indicio": "INDICIO",
            "nao-encontrado": "NAO ENCONTRADO",
        },
        "en-US": {
            "confirmado": "CONFIRMED",
            "provavel": "PROBABLE",
            "indicio": "INDICATION",
            "nao-encontrado": "NOT FOUND",
        },
    }
    return labels.get(lang, labels["pt-BR"]).get(level, level.upper())


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------

_base = getSampleStyleSheet()


def build_styles() -> dict[str, ParagraphStyle]:
    """Return all custom paragraph styles used in the dossier."""
    return {
        "cell_key": ParagraphStyle(
            "cell_key",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1a2e4a"),
            alignment=TA_LEFT,
            wordWrap="LTR",
        ),
        "cell_body": ParagraphStyle(
            "cell_body",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            wordWrap="LTR",
        ),
        "cell_conf": ParagraphStyle(
            "cell_conf",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.black,
            alignment=TA_CENTER,
            wordWrap="LTR",
        ),
        "disclaimer_title": ParagraphStyle(
            "disclaimer_title",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=COLOR_DISCLAIMER_TITLE,
            alignment=TA_CENTER,
            spaceAfter=0.3 * cm,
        ),
        "disclaimer_body": ParagraphStyle(
            "disclaimer_body",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#3e2723"),
            alignment=TA_LEFT,
            leftIndent=0.4 * cm,
            spaceAfter=0.15 * cm,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            textColor=COLOR_DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=0.3 * cm,
        ),
        "cover_target": ParagraphStyle(
            "cover_target",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=24,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=0.5 * cm,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=COLOR_MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=0.2 * cm,
        ),
        "cover_warning": ParagraphStyle(
            "cover_warning",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=COLOR_DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=COLOR_DARK_BLUE,
            spaceBefore=0.6 * cm,
            spaceAfter=0.2 * cm,
            borderPad=(0, 0, 2, 0),
        ),
        "subsection_heading": ParagraphStyle(
            "subsection_heading",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.black,
            spaceBefore=0.4 * cm,
            spaceAfter=0.15 * cm,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=0.2 * cm,
        ),
        "body_small": ParagraphStyle(
            "body_small",
            fontName="Times-Roman",
            fontSize=9,
            leading=13,
            textColor=COLOR_MID_GRAY,
            alignment=TA_LEFT,
            spaceAfter=0.1 * cm,
        ),
        "citation": ParagraphStyle(
            "citation",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_MID_GRAY,
            alignment=TA_RIGHT,
            spaceAfter=0.1 * cm,
        ),
        "no_hits": ParagraphStyle(
            "no_hits",
            fontName="Times-Italic",
            fontSize=10,
            leading=14,
            textColor=COLOR_MID_GRAY,
            spaceAfter=0.2 * cm,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            textColor=colors.black,
            leftIndent=0.5 * cm,
            spaceAfter=0.1 * cm,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=COLOR_MID_GRAY,
            alignment=TA_CENTER,
        ),
    }


# ---------------------------------------------------------------------------
# Table styles
# ---------------------------------------------------------------------------

def hits_table_style() -> TableStyle:
    """Style for the findings table (field | value rows). Cells use Paragraph for wrapping."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_GRAY]),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def triangulation_table_style() -> TableStyle:
    """Style for the triangulations table. Cells use Paragraph for wrapping."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_GRAY]),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def appendix_table_style() -> TableStyle:
    """Style for the timestamps appendix table."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_MID_GRAY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_GRAY]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
        ]
    )


def disclaimer_box_style() -> TableStyle:
    """Style for the prominent disclaimer box."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_DISCLAIMER_BG),
            ("BOX", (0, 0), (-1, -1), 2, COLOR_DISCLAIMER_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )
