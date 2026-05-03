#!/usr/bin/env python3
"""
Purpose: Generate a structured PDF dossier from findings-consolidated.json and target.yaml.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-05-01
Dependencies: reportlab>=4.1, click>=8.1, pyyaml>=6.0 (see pyproject.toml)

Usage:
    python generate_report.py \
        --consolidated examples/case-fictional/findings.json \
        --target examples/case-fictional/target.yaml \
        --output examples/case-fictional/dossier.pdf \
        --lang pt-BR

    # English dossier:
    python generate_report.py \
        --consolidated cases/target/findings-consolidated.json \
        --target cases/target/target.yaml \
        --output cases/target/dossier-en.pdf \
        --lang en-US
"""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

import click
import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
)

# ---------------------------------------------------------------------------
# Load dossier_template.py via importlib (hyphen-safe sibling import)
# ---------------------------------------------------------------------------

_TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "dossier_template.py"


def _load_template() -> Any:
    spec = importlib.util.spec_from_file_location("dossier_template", _TEMPLATE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


_tpl = _load_template()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2.5 * cm
INNER_WIDTH = PAGE_WIDTH - 2 * MARGIN

PROJECT_URL = "https://github.com/reichaves/due-diligence-transnacional"

# ---------------------------------------------------------------------------
# Bilingual strings
# ---------------------------------------------------------------------------

STRINGS: dict[str, dict[str, str]] = {
    "pt-BR": {
        "doc_title": "DOSSIE DE DUE DILIGENCE",
        "confidential": "DOCUMENTO CONFIDENCIAL -- USO JORNALISTICO",
        "all_claims_sourced": "Toda afirmacao neste dossie tem fonte explicita e nivel de confianca.",
        "generated_by": f"Gerado por due-diligence-transnacional pipeline | {PROJECT_URL}",
        "meta_date": "Data de geracao",
        "meta_sources": "Bases consultadas",
        "meta_hits": "Total de achados",
        "sec1": "1. Resumo Executivo",
        "sec2": "2. Metodologia",
        "sec3": "3. Variacoes de Identidade Buscadas",
        "sec4": "4. Achados por Base",
        "sec5": "5. Triangulacoes",
        "sec6": "6. Lacunas e Proximas Frentes",
        "sec7": "7. Contexto Legal Aplicavel",
        "sec8": "8. Aviso Legal e Etico",
        "sec_appendix": "Apendice — Timestamps de Consulta",
        "high_conf_intro": "Os achados de maior confianca identificados pelo pipeline sao:",
        "no_high_conf": "Nenhum achado de alta confianca foi identificado — ver secao de Lacunas para proximas frentes.",
        "pipeline_summary": "O pipeline executou buscas em {sc} bases, identificou {th} registros relevantes, {tc} triangulacoes e {gc} lacunas documentadas.",
        "bases_consulted": "Bases consultadas:",
        "method_notes": "Notas metodologicas por base:",
        "no_vars": "Variacoes nao listadas no arquivo consolidado.",
        "no_triang": "Nenhuma triangulacao detectada com os achados disponiveis.",
        "no_legal": "Nenhum contexto legal especifico registrado.",
        "not_found": "Nao encontrado — variacoes testadas: {vars}",
        "source_cite": "(Fonte: {base}, ID {sid}, consultado em {date}{url})",
        "legal_ctx": "Contexto legal: {ctx}",
        "gaps_header": "Lacunas documentadas:",
        "frontiers_header": "Proximas frentes de investigacao:",
        "suggested_action": "Acao sugerida: {action}",
        "appendix_cols": ["Base", "Data/Hora", "Queries", "Status", "Hits"],
        "triang_cols": ["Tipo", "Fontes", "Detalhe", "Confianca"],
        "hits_cols": ["Campo", "Valor"],
        "footer": "Due Diligence Transnacional  |  Pagina {page}  |  {date}",
        "generated_at": "Dossie gerado em: {ts}  |  Pipeline: due-diligence-transnacional v0.1.0",
        "disclaimer_title": "AVISO IMPORTANTE — LEIA ANTES DE USAR ESTE DOCUMENTO",
        "disclaimer_lines": [
            f"Este dossie foi gerado automaticamente por Inteligencia Artificial como parte do projeto due-diligence-transnacional, disponivel em {PROJECT_URL}",
            "",
            "  FINALIDADE EXCLUSIVAMENTE JORNALISTICA. Este projeto destina-se a transparencia e ao jornalismo de dados de interesse publico. O uso para qualquer outra finalidade e de responsabilidade exclusiva do usuario.",
            "",
            "  GERADO POR IA A PARTIR DE FONTES PUBLICAS. Todas as informacoes foram produzidas por modelos de IA com base em dados publicamente disponiveis. Todo e qualquer dado deve ser verificado nos documentos originais antes de qualquer publicacao ou uso.",
            "",
            "  PRESUNCAO DE INOCENCIA. Indicios de condutas ilicitas exigem apuracao adicional com fontes e documentos. O fato de uma pessoa ou empresa ser investigada nao implica culpa ou condenacao.",
            "",
            "  ATENCAO A HOMONIMOS. Sempre verifique se a pessoa ou empresa encontrada e de fato o alvo pesquisado. Nomes comuns podem gerar falsos positivos.",
            "",
            "  SEM GARANTIA DE COMPLETUDE. Os dados publicos consultados podem conter erros, desatualizacoes ou omissoes. Nao nos responsabilizamos por defeitos ou vicios nas fontes de dados publicas.",
            "",
            "  O USUARIO E RESPONSAVEL pela correta utilizacao das informacoes deste documento.",
        ],
        "disclaimer_short": f"Gerado por IA | {PROJECT_URL} | Uso jornalistico | Verifique nos documentos originais | O investigado nao e culpado por ser investigado",
    },
    "en-US": {
        "doc_title": "DUE DILIGENCE DOSSIER",
        "confidential": "CONFIDENTIAL DOCUMENT -- JOURNALISTIC USE ONLY",
        "all_claims_sourced": "Every claim in this dossier has an explicit source and confidence level.",
        "generated_by": f"Generated by due-diligence-transnacional pipeline | {PROJECT_URL}",
        "meta_date": "Generated on",
        "meta_sources": "Databases queried",
        "meta_hits": "Total records found",
        "sec1": "1. Executive Summary",
        "sec2": "2. Methodology",
        "sec3": "3. Identity Variations Searched",
        "sec4": "4. Findings by Database",
        "sec5": "5. Triangulations",
        "sec6": "6. Gaps and Next Steps",
        "sec7": "7. Applicable Legal Context",
        "sec8": "8. Legal and Ethical Notice",
        "sec_appendix": "Appendix — Query Timestamps",
        "high_conf_intro": "The highest-confidence findings identified by the pipeline are:",
        "no_high_conf": "No high-confidence findings identified — see Gaps section for next steps.",
        "pipeline_summary": "The pipeline queried {sc} databases, identified {th} relevant records, {tc} triangulations and {gc} documented gaps.",
        "bases_consulted": "Databases queried:",
        "method_notes": "Methodology notes per database:",
        "no_vars": "Variations not listed in the consolidated file.",
        "no_triang": "No triangulations detected with the available findings.",
        "no_legal": "No specific legal context recorded.",
        "not_found": "Not found — variations tested: {vars}",
        "source_cite": "(Source: {base}, ID {sid}, retrieved on {date}{url})",
        "legal_ctx": "Legal context: {ctx}",
        "gaps_header": "Documented gaps:",
        "frontiers_header": "Next investigative steps:",
        "suggested_action": "Suggested action: {action}",
        "appendix_cols": ["Database", "Date/Time", "Queries", "Status", "Hits"],
        "triang_cols": ["Type", "Sources", "Detail", "Confidence"],
        "hits_cols": ["Field", "Value"],
        "footer": "Transnational Due Diligence  |  Page {page}  |  {date}",
        "generated_at": "Dossier generated: {ts}  |  Pipeline: due-diligence-transnacional v0.1.0",
        "disclaimer_title": "IMPORTANT NOTICE — READ BEFORE USING THIS DOCUMENT",
        "disclaimer_lines": [
            f"This dossier was automatically generated by Artificial Intelligence as part of the due-diligence-transnacional project, available at {PROJECT_URL}",
            "",
            "  JOURNALISTIC USE ONLY. This project is designed for data journalism and public-interest transparency. Any other use is the sole responsibility of the user.",
            "",
            "  AI-GENERATED FROM PUBLIC DATA. All information was produced by AI models based on publicly available data. Every item must be verified against original source documents before publication or any other use.",
            "",
            "  PRESUMPTION OF INNOCENCE. Evidence of potential misconduct requires further investigation with additional sources and documents. The fact that a person or company is under investigation does not imply guilt or wrongdoing.",
            "",
            "  BEWARE OF HOMONYMS. Always verify that the person or company found is indeed the intended research subject. Common names may produce false positives.",
            "",
            "  NO GUARANTEE OF COMPLETENESS. Public data sources may contain errors, outdated information or omissions. We are not responsible for defects or inaccuracies in public data sources.",
            "",
            "  THE USER BEARS SOLE RESPONSIBILITY for the correct use of the information in this document.",
        ],
        "disclaimer_short": f"AI-generated | {PROJECT_URL} | Journalistic use | Verify in original documents | Being investigated does not imply guilt",
    },
}


# ---------------------------------------------------------------------------
# Helper: table cell utilities
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 80) -> str:
    """Truncate long strings for display (used for IDs and citations, not table cells)."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _cell(text: str, style: Any) -> Paragraph:
    """Wrap text in a Paragraph for table cell use — enables word wrapping.

    Escapes XML special characters so ReportLab's XML parser doesn't fail
    on raw data containing &, <, or >.
    """
    safe = _xml_escape(str(text) if text else "")
    return Paragraph(safe, style)


def _format_date(iso: str) -> str:
    """Convert ISO date-time to DD/MM/AAAA for display."""
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso[:19])
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return iso[:10]


def _base_url(base: str) -> str:
    """Return the official URL for a known base."""
    urls = {
        "FEC": "https://www.fec.gov",
        "LDA": "https://lda.senate.gov",
        "FARA": "https://efile.fara.gov",
        "FL-SUNBIZ": "https://search.sunbiz.org",
        "DE-CORPS": "https://icis.corp.delaware.gov",
        "TX-COMPTROLLER": "https://mycpa.cpa.state.tx.us",
        "OPENCORPORATES": "https://opencorporates.com",
        "NEWS-BR": "Imprensa brasileira (vide outlets em trusted-outlets.md)",
        "NEWS-US": "Imprensa americana (vide outlets em trusted-outlets.md)",
    }
    return urls.get(base, base)


# ---------------------------------------------------------------------------
# Page template (header / footer)
# ---------------------------------------------------------------------------

def _on_page(canvas: Any, doc: Any, target_name: str, page_label: str, lang: str = "pt-BR") -> None:
    """Draw page header and footer on each page."""
    canvas.saveState()

    footer_text = STRINGS[lang]["footer"].format(page=doc.page, date=page_label)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_tpl.COLOR_MID_GRAY)
    canvas.drawCentredString(PAGE_WIDTH / 2, MARGIN * 0.5, footer_text)

    canvas.setStrokeColor(_tpl.COLOR_BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, PAGE_HEIGHT - MARGIN * 0.7, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN * 0.7)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _make_cover(styles: dict, target_name: str, consolidated: dict, generated_at: str, lang: str = "pt-BR") -> list:
    """Build cover page story elements."""
    s = STRINGS[lang]
    story: list = []
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph(s["doc_title"], styles["cover_title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(target_name.upper(), styles["cover_target"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"{s['meta_date']}: {_format_date(generated_at)}", styles["cover_meta"]))
    story.append(Paragraph(f"{s['meta_sources']}: {consolidated.get('sources_count', 0)}", styles["cover_meta"]))
    story.append(Paragraph(f"{s['meta_hits']}: {consolidated.get('total_hits', 0)}", styles["cover_meta"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(width=INNER_WIDTH * 0.6, thickness=1, color=_tpl.COLOR_DARK_BLUE))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(s["confidential"], styles["cover_warning"]))
    story.append(Paragraph(s["all_claims_sourced"], styles["cover_meta"]))
    story.append(Spacer(1, 0.8 * cm))
    # Short disclaimer on cover
    story.append(HRFlowable(width=INNER_WIDTH * 0.6, thickness=0.5, color=_tpl.COLOR_DISCLAIMER_BORDER))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(s["disclaimer_short"], styles["cover_meta"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph(s["generated_by"], styles["cover_meta"]))
    story.append(PageBreak())
    return story


def _make_executive_summary(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build executive summary section."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec1"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    flags = consolidated.get("high_confidence_flags", [])
    if flags:
        story.append(Paragraph(s["high_conf_intro"], styles["body"]))
        for flag in flags:
            story.append(Paragraph(f"  -  {flag}", styles["bullet"]))
    else:
        story.append(Paragraph(s["no_high_conf"], styles["no_hits"]))

    gap_count = len(consolidated.get("gaps", []))
    triangulations_count = len(consolidated.get("triangulations", []))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            s["pipeline_summary"].format(
                sc=consolidated.get("sources_count", 0),
                th=consolidated.get("total_hits", 0),
                tc=triangulations_count,
                gc=gap_count,
            ),
            styles["body"],
        )
    )
    story.append(PageBreak())
    return story


def _make_methodology(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build methodology section."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec2"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    if lang == "en-US":
        intro = (
            "This dossier was produced by the due-diligence-transnacional pipeline, "
            "developed for investigative journalism of persons with U.S. ties using public American databases. "
            "Each claim has an explicit source (database + record ID + retrieval date) "
            "and a confidence level per the scale documented in "
            "skills/due-diligence-transnacional/references/confidence-levels.md."
        )
    else:
        intro = (
            "Este dossie foi produzido pelo pipeline due-diligence-transnacional, "
            "desenvolvido para investigacao jornalistica de pessoas com vinculo americano em bases publicas dos EUA. "
            "Cada afirmacao tem fonte explicita (base de dados + ID do registro + data de consulta) "
            "e nivel de confianca conforme escala documentada em "
            "skills/due-diligence-transnacional/references/confidence-levels.md."
        )
    story.append(Paragraph(intro, styles["body"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(s["bases_consulted"], styles["subsection_heading"]))
    for f in consolidated.get("findings", []):
        base = f.get("base", "")
        qe = f.get("queries_executed", 0)
        ts = _format_date(f.get("consulted_at", ""))
        status = f.get("status", "ok")
        url = _base_url(base)
        story.append(Paragraph(f"  -  <b>{base}</b> — {qe} queries em {ts} (status: {status}) | {url}", styles["bullet"]))

    note_texts = [f.get("methodology_note", "") for f in consolidated.get("findings", []) if f.get("methodology_note")]
    if note_texts:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(s["method_notes"], styles["subsection_heading"]))
        for note in note_texts:
            story.append(Paragraph(f"  -  {note}", styles["bullet"]))

    story.append(PageBreak())
    return story


def _make_identity_section(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build identity variations section (aggregated from no_hits)."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec3"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    variations: set[str] = set()
    for f in consolidated.get("findings", []):
        for v in f.get("no_hits", []):
            variations.add(v)
        for hit in f.get("hits", []):
            vm = hit.get("variation_matched", "")
            if vm:
                variations.add(vm)

    if variations:
        for v in sorted(variations):
            story.append(Paragraph(f"  -  {v}", styles["bullet"]))
    else:
        story.append(Paragraph(s["no_vars"], styles["no_hits"]))

    story.append(PageBreak())
    return story


def _make_findings_section(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build per-base findings section."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec4"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))

    for f in consolidated.get("findings", []):
        base = f.get("base", "")
        consulted = _format_date(f.get("consulted_at", ""))
        hits = f.get("hits", [])
        no_hits = f.get("no_hits", [])

        story.append(Paragraph(f"Base: {base}", styles["subsection_heading"]))
        story.append(
            Paragraph(
                f"Consulta em: {consulted} | URL oficial: {_base_url(base)} | "
                f"Status: {f.get('status', 'ok')} | Queries: {f.get('queries_executed', 0)}",
                styles["body_small"],
            )
        )

        if hits:
            for idx, hit in enumerate(hits, 1):
                confidence = hit.get("confidence", "indicio")
                conf_color = _tpl.confidence_color(confidence)
                conf_label = _tpl.confidence_label(confidence, lang)
                story.append(
                    Paragraph(
                        f"#{idx} — "
                        f'<font color="{conf_color.hexval()}"><b>{conf_label}</b></font>',
                        styles["body"],
                    )
                )

                raw = hit.get("raw_record", {})
                if raw:
                    h_cols = s["hits_cols"]
                    # Header row: plain strings (short, no overflow risk)
                    table_data: list = [h_cols]
                    for k, v in raw.items():
                        if isinstance(v, list):
                            v_str = "; ".join(str(i) for i in v)
                        elif isinstance(v, dict):
                            # Render nested dicts as indented key: value lines
                            v_str = "\n".join(f"{dk}: {dv}" for dk, dv in v.items())
                        else:
                            v_str = str(v) if v is not None else ""
                        # Use Paragraph cells — they wrap; no manual truncation needed
                        table_data.append([
                            _cell(k, styles["cell_key"]),
                            _cell(v_str, styles["cell_body"]),
                        ])

                    # Key col narrower; value col takes remaining space
                    col_widths = [INNER_WIDTH * 0.28, INNER_WIDTH * 0.72]
                    t = Table(table_data, colWidths=col_widths, repeatRows=1)
                    t.setStyle(_tpl.hits_table_style())
                    story.append(t)

                source_id = hit.get("source_id", "")
                source_url = hit.get("source_url", "")
                # Truncate only the ID/URL for the citation line (not the full text)
                sid_display = _truncate(source_id, 70)
                url_part = f" | {_truncate(source_url, 60)}" if source_url else ""
                story.append(
                    Paragraph(
                        s["source_cite"].format(base=base, sid=sid_display, date=consulted, url=url_part),
                        styles["citation"],
                    )
                )
                story.append(Spacer(1, 0.4 * cm))
        else:
            no_hits_str = ", ".join(no_hits[:6]) + ("..." if len(no_hits) > 6 else "")
            story.append(Paragraph(s["not_found"].format(vars=no_hits_str), styles["no_hits"]))

        for ctx in f.get("legal_context", []):
            story.append(Paragraph(s["legal_ctx"].format(ctx=ctx), styles["body_small"]))

        story.append(Spacer(1, 0.4 * cm))

    story.append(PageBreak())
    return story


def _make_triangulation_section(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build triangulations section."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec5"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    triangulations = consolidated.get("triangulations", [])
    if not triangulations:
        story.append(Paragraph(s["no_triang"], styles["no_hits"]))
        story.append(PageBreak())
        return story

    cols = s["triang_cols"]
    # Header: plain strings (white-on-dark-blue, short labels)
    table_data: list = [cols]
    for tri in triangulations:
        ttype = tri.get("type", "").replace("_", " ")
        # Each source on its own line for readability
        sources_list = tri.get("sources", [])
        sources_str = "\n".join(f"- {src}" for src in sources_list) if sources_list else ""
        detail = tri.get("detail", "")
        confidence = _tpl.confidence_label(tri.get("confidence", ""), lang)
        conf_color = _tpl.confidence_color(tri.get("confidence", ""))
        table_data.append([
            _cell(ttype, styles["cell_key"]),
            _cell(sources_str, styles["cell_body"]),
            _cell(detail, styles["cell_body"]),
            # Confidence in colour
            Paragraph(
                f'<font color="{conf_color.hexval()}"><b>{_xml_escape(confidence)}</b></font>',
                styles["cell_conf"],
            ),
        ])

    # Rebalanced widths: type 16%, sources 24%, detail 44%, confidence 16%
    col_widths = [INNER_WIDTH * 0.16, INNER_WIDTH * 0.24, INNER_WIDTH * 0.44, INNER_WIDTH * 0.16]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_tpl.triangulation_table_style())
    story.append(tbl)
    story.append(PageBreak())
    return story


def _make_gaps_section(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build gaps and next frontiers section."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec6"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    gaps = consolidated.get("gaps", [])
    if gaps:
        story.append(Paragraph(s["gaps_header"], styles["subsection_heading"]))
        for gap in gaps:
            story.append(Paragraph(f"  <b>{gap.get('base', '')}</b> — {gap.get('reason', '')}", styles["bullet"]))
            if gap.get("detail"):
                story.append(Paragraph(f"    {gap['detail']}", styles["body_small"]))
            if gap.get("suggested_action"):
                story.append(Paragraph(f"    {s['suggested_action'].format(action=gap['suggested_action'])}", styles["body_small"]))
        story.append(Spacer(1, 0.3 * cm))

    frontiers = consolidated.get("next_frontiers", [])
    if frontiers:
        story.append(Paragraph(s["frontiers_header"], styles["subsection_heading"]))
        for frontier in frontiers:
            story.append(Paragraph(f"  -  {frontier}", styles["bullet"]))

    story.append(PageBreak())
    return story


def _make_legal_context_section(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build legal context section."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec7"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    contexts = consolidated.get("legal_contexts", [])
    if contexts:
        for ctx in contexts:
            story.append(Paragraph(f"  -  {ctx}", styles["bullet"]))
    else:
        story.append(Paragraph(s["no_legal"], styles["no_hits"]))

    story.append(PageBreak())
    return story


def _make_disclaimer_section(styles: dict, lang: str = "pt-BR") -> list:
    """Build full-page prominent disclaimer section."""
    from reportlab.platypus import Table as RLTable

    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec8"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=2, color=_tpl.COLOR_DISCLAIMER_BORDER))
    story.append(Spacer(1, 0.4 * cm))

    inner: list = []
    inner.append(Paragraph(s["disclaimer_title"], styles["disclaimer_title"]))
    inner.append(Spacer(1, 0.3 * cm))
    for line in s["disclaimer_lines"]:
        if line == "":
            inner.append(Spacer(1, 0.2 * cm))
        else:
            inner.append(Paragraph(line, styles["disclaimer_body"]))

    box = RLTable([[inner]], colWidths=[INNER_WIDTH])
    box.setStyle(_tpl.disclaimer_box_style())
    story.append(box)
    story.append(PageBreak())
    return story


def _make_appendix(styles: dict, consolidated: dict, lang: str = "pt-BR") -> list:
    """Build timestamps appendix."""
    s = STRINGS[lang]
    story: list = []
    story.append(Paragraph(s["sec_appendix"], styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    cell_s = styles["cell_body"]
    table_data: list = [s["appendix_cols"]]
    for f in consolidated.get("findings", []):
        table_data.append([
            _cell(f.get("base", ""), cell_s),
            _cell(f.get("consulted_at", "")[:19], cell_s),
            _cell(str(f.get("queries_executed", 0)), cell_s),
            _cell(_truncate(f.get("status", "ok"), 20), cell_s),
            _cell(str(len(f.get("hits", []))), cell_s),
        ])

    col_widths = [INNER_WIDTH * 0.16, INNER_WIDTH * 0.32, INNER_WIDTH * 0.12, INNER_WIDTH * 0.28, INNER_WIDTH * 0.12]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(_tpl.appendix_table_style())
    story.append(tbl)

    story.append(Spacer(1, 0.5 * cm))
    generated = datetime.now(timezone.utc).isoformat()
    story.append(Paragraph(s["generated_at"].format(ts=generated), styles["body_small"]))
    return story


# ---------------------------------------------------------------------------
# Main PDF builder
# ---------------------------------------------------------------------------

def build_dossier(
    consolidated: dict[str, Any],
    target: dict[str, Any],
    output_path: Path,
    lang: str = "pt-BR",
) -> None:
    """Assemble and write the full dossier PDF.

    Args:
        consolidated: Parsed findings-consolidated JSON.
        target: Parsed target YAML.
        output_path: Destination path for the PDF file.
        lang: Output language — 'pt-BR' or 'en-US'.
    """
    # Normalise lang: accept 'en', 'en-US', 'pt', 'pt-BR'
    if lang.startswith("en"):
        lang = "en-US"
    else:
        lang = "pt-BR"

    target_name = consolidated.get("target_name") or target.get("nome_completo", "Alvo Desconhecido")
    generated_at = consolidated.get("consolidated_at", datetime.now(timezone.utc).isoformat())

    logger.info("Building dossier for: %s (lang: %s)", target_name, lang)

    styles = _tpl.build_styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN * 1.2,
        title=f"Due Diligence Dossier — {target_name}",
        author="due-diligence-transnacional pipeline",
        subject="Transnational investigative journalism",
    )

    page_label = _format_date(generated_at)

    def _page_footer(canvas: Any, doc: Any) -> None:
        _on_page(canvas, doc, target_name, page_label, lang)

    story: list = []
    story.extend(_make_cover(styles, target_name, consolidated, generated_at, lang))
    story.extend(_make_executive_summary(styles, consolidated, lang))
    story.extend(_make_methodology(styles, consolidated, lang))
    story.extend(_make_identity_section(styles, consolidated, lang))
    story.extend(_make_findings_section(styles, consolidated, lang))
    story.extend(_make_triangulation_section(styles, consolidated, lang))
    story.extend(_make_gaps_section(styles, consolidated, lang))
    story.extend(_make_legal_context_section(styles, consolidated, lang))
    story.extend(_make_disclaimer_section(styles, lang))
    story.extend(_make_appendix(styles, consolidated, lang))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    logger.info("PDF written to %s", output_path)
    _print_terminal_disclaimer(lang)


# ---------------------------------------------------------------------------
# Terminal disclaimer
# ---------------------------------------------------------------------------

def _print_terminal_disclaimer(lang: str = "pt-BR") -> None:
    """Print the mandatory disclaimer to stdout after dossier generation."""
    border = "=" * 72
    if lang == "en-US":
        lines = [
            border,
            "  IMPORTANT NOTICE",
            border,
            f"  AI-generated research | {PROJECT_URL}",
            "  JOURNALISTIC USE ONLY.",
            "  All data must be verified in original source documents.",
            "  Being investigated does NOT imply guilt.",
            "  Always check for homonymous persons/companies.",
            "  The user bears sole responsibility for correct use of this data.",
            "  We are not responsible for defects in public data sources.",
            border,
        ]
    else:
        lines = [
            border,
            "  AVISO IMPORTANTE",
            border,
            f"  Pesquisa gerada por IA | {PROJECT_URL}",
            "  USO EXCLUSIVAMENTE JORNALISTICO.",
            "  Todos os dados devem ser checados nos documentos originais.",
            "  Ser investigado NAO significa ser culpado.",
            "  Atencao a pessoas e empresas homonimas.",
            "  O usuario e responsavel pela correta utilizacao das informacoes.",
            "  Nao nos responsabilizamos por vicios nas fontes de dados publicas.",
            border,
        ]
    print("\n" + "\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--consolidated",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to findings-consolidated.json",
)
@click.option(
    "--target",
    "target_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to target.yaml",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output PDF path",
)
@click.option(
    "--lang",
    default=None,
    type=click.Choice(["pt-BR", "en-US"], case_sensitive=False),
    help="Dossier language. Defaults to investigation_language in target.yaml, or pt-BR.",
)
def main(consolidated: Path, target_path: Path, output: Path, lang: str | None) -> None:
    """Generate a structured dossier PDF from consolidated findings and target YAML."""
    try:
        consolidated_data: dict[str, Any] = json.loads(
            consolidated.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read consolidated JSON: %s", exc)
        sys.exit(1)

    try:
        target_data: dict[str, Any] = yaml.safe_load(
            target_path.read_text(encoding="utf-8")
        ) or {}
    except (yaml.YAMLError, OSError) as exc:
        logger.error("Failed to read target YAML: %s", exc)
        sys.exit(1)

    # Language precedence: --lang flag > target.yaml > default pt-BR
    resolved_lang = lang or target_data.get("investigation_language", "pt-BR")

    output.parent.mkdir(parents=True, exist_ok=True)
    build_dossier(consolidated_data, target_data, output, lang=resolved_lang)


if __name__ == "__main__":
    main()
