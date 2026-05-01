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
        --output examples/case-fictional/dossier.pdf
"""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


# ---------------------------------------------------------------------------
# Helper: safe string truncation for table cells
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 120) -> str:
    """Truncate long strings for table display."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


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

def _on_page(canvas: Any, doc: Any, target_name: str, page_label: str) -> None:
    """Draw page header and footer on each page."""
    canvas.saveState()
    styles = _tpl.build_styles()

    # Footer: page number + pipeline label
    footer_text = f"Due Diligence Transnacional  |  Pagina {doc.page}  |  {page_label}"
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_tpl.COLOR_MID_GRAY)
    canvas.drawCentredString(PAGE_WIDTH / 2, MARGIN * 0.5, footer_text)

    # Top hairline
    canvas.setStrokeColor(_tpl.COLOR_BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, PAGE_HEIGHT - MARGIN * 0.7, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN * 0.7)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _make_cover(styles: dict, target_name: str, consolidated: dict, generated_at: str) -> list:
    """Build cover page story elements."""
    story: list = []
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("DOSSIE DE DUE DILIGENCE", styles["cover_title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(target_name.upper(), styles["cover_target"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(
        Paragraph(
            f"Data de geracao: {_format_date(generated_at)}", styles["cover_meta"]
        )
    )
    story.append(
        Paragraph(
            f"Bases consultadas: {consolidated.get('sources_count', 0)}", styles["cover_meta"]
        )
    )
    story.append(
        Paragraph(
            f"Total de achados: {consolidated.get('total_hits', 0)}", styles["cover_meta"]
        )
    )
    story.append(Spacer(1, 1.5 * cm))
    story.append(
        HRFlowable(width=INNER_WIDTH * 0.6, thickness=1, color=_tpl.COLOR_DARK_BLUE)
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "DOCUMENTO CONFIDENCIAL -- USO JORNALISTICO", styles["cover_warning"]
        )
    )
    story.append(
        Paragraph(
            "Toda afirmacao neste dossie tem fonte explicita e nivel de confianca.",
            styles["cover_meta"],
        )
    )
    story.append(Spacer(1, 2 * cm))
    story.append(
        Paragraph(
            "Gerado por due-diligence-transnacional pipeline | github.com/reichaves",
            styles["cover_meta"],
        )
    )
    story.append(PageBreak())
    return story


def _make_executive_summary(styles: dict, consolidated: dict) -> list:
    """Build executive summary section."""
    story: list = []
    story.append(Paragraph("1. Resumo Executivo", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    flags = consolidated.get("high_confidence_flags", [])
    if flags:
        story.append(
            Paragraph(
                "Os achados de maior confianca identificados pelo pipeline sao:", styles["body"]
            )
        )
        for flag in flags:
            story.append(Paragraph(f"  -  {flag}", styles["bullet"]))
    else:
        story.append(
            Paragraph(
                "Nenhum achado de alta confianca foi identificado — "
                "ver secao de Lacunas para proximas frentes.",
                styles["no_hits"],
            )
        )

    gap_count = len(consolidated.get("gaps", []))
    triangulations_count = len(consolidated.get("triangulations", []))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            f"O pipeline executou buscas em {consolidated.get('sources_count', 0)} bases, "
            f"identificou {consolidated.get('total_hits', 0)} registros relevantes, "
            f"{triangulations_count} triangulacoes e {gap_count} lacunas documentadas.",
            styles["body"],
        )
    )
    story.append(PageBreak())
    return story


def _make_methodology(styles: dict, consolidated: dict) -> list:
    """Build methodology section."""
    story: list = []
    story.append(Paragraph("2. Metodologia", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    story.append(
        Paragraph(
            "Este dossie foi produzido pelo pipeline due-diligence-transnacional, "
            "desenvolvido para investigacao jornalistica de brasileiros em bases publicas americanas. "
            "Cada afirmacao tem fonte explicita (base de dados + ID do registro + data de consulta) "
            "e nivel de confianca conforme escala documentada em "
            "skills/due-diligence-transnacional/references/confidence-levels.md.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Bases consultadas:", styles["subsection_heading"]))
    for f in consolidated.get("findings", []):
        base = f.get("base", "")
        qe = f.get("queries_executed", 0)
        ts = _format_date(f.get("consulted_at", ""))
        status = f.get("status", "ok")
        url = _base_url(base)
        story.append(
            Paragraph(
                f"  -  <b>{base}</b> — {qe} queries em {ts} (status: {status}) | {url}",
                styles["bullet"],
            )
        )

    note_texts = [
        f.get("methodology_note", "") for f in consolidated.get("findings", []) if f.get("methodology_note")
    ]
    if note_texts:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Notas metodologicas por base:", styles["subsection_heading"]))
        for note in note_texts:
            story.append(Paragraph(f"  -  {note}", styles["bullet"]))

    story.append(PageBreak())
    return story


def _make_identity_section(styles: dict, consolidated: dict) -> list:
    """Build identity variations section (aggregated from no_hits)."""
    story: list = []
    story.append(Paragraph("3. Variacoes de Identidade Buscadas", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    # Collect unique variations from all no_hits + variation_matched from hits
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
        story.append(Paragraph("Variacoes nao listadas no arquivo consolidado.", styles["no_hits"]))

    story.append(PageBreak())
    return story


def _make_findings_section(styles: dict, consolidated: dict) -> list:
    """Build per-base findings section."""
    story: list = []
    story.append(Paragraph("4. Achados por Base", styles["section_heading"]))
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
                conf_label = _tpl.confidence_label(confidence)
                story.append(
                    Paragraph(
                        f"Registro #{idx} — "
                        f'<font color="{conf_color.hexval()}" name="Helvetica-Bold">'
                        f"{conf_label}</font>",
                        styles["body"],
                    )
                )

                # Build key-value table from raw_record
                raw = hit.get("raw_record", {})
                if raw:
                    table_data = [["Campo", "Valor"]]
                    for k, v in raw.items():
                        if isinstance(v, list):
                            v_str = "; ".join(str(i) for i in v)
                        elif isinstance(v, dict):
                            v_str = json.dumps(v, ensure_ascii=False)[:100]
                        else:
                            v_str = str(v) if v is not None else ""
                        table_data.append([k, _truncate(v_str)])

                    col_widths = [INNER_WIDTH * 0.3, INNER_WIDTH * 0.7]
                    t = Table(table_data, colWidths=col_widths)
                    t.setStyle(_tpl.hits_table_style())
                    story.append(t)

                source_id = hit.get("source_id", "")
                source_url = hit.get("source_url", "")
                story.append(
                    Paragraph(
                        f"(Fonte: {base}, ID {source_id}, consultado em {consulted}"
                        + (f" | {source_url}" if source_url else "")
                        + ")",
                        styles["citation"],
                    )
                )
                story.append(Spacer(1, 0.3 * cm))
        else:
            no_hits_str = ", ".join(no_hits[:6]) + ("..." if len(no_hits) > 6 else "")
            story.append(
                Paragraph(
                    f"Nao encontrado — variacoes testadas: {no_hits_str}",
                    styles["no_hits"],
                )
            )

        # Legal context per base
        for ctx in f.get("legal_context", []):
            story.append(Paragraph(f"Contexto legal: {ctx}", styles["body_small"]))

        story.append(Spacer(1, 0.4 * cm))

    story.append(PageBreak())
    return story


def _make_triangulation_section(styles: dict, consolidated: dict) -> list:
    """Build triangulations section."""
    story: list = []
    story.append(Paragraph("5. Triangulacoes", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    triangulations = consolidated.get("triangulations", [])
    if not triangulations:
        story.append(
            Paragraph(
                "Nenhuma triangulacao detectada com os achados disponíveis.",
                styles["no_hits"],
            )
        )
        story.append(PageBreak())
        return story

    table_data = [["Tipo", "Fontes", "Detalhe", "Confianca"]]
    for t in triangulations:
        ttype = t.get("type", "").replace("_", " ")
        sources = ", ".join(t.get("sources", []))
        detail = _truncate(t.get("detail", ""), 100)
        confidence = t.get("confidence", "")
        table_data.append([ttype, sources, detail, confidence.upper()])

    col_widths = [
        INNER_WIDTH * 0.15,
        INNER_WIDTH * 0.20,
        INNER_WIDTH * 0.50,
        INNER_WIDTH * 0.15,
    ]
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(_tpl.triangulation_table_style())
    story.append(tbl)
    story.append(PageBreak())
    return story


def _make_gaps_section(styles: dict, consolidated: dict) -> list:
    """Build gaps and next frontiers section."""
    story: list = []
    story.append(Paragraph("6. Lacunas e Proximas Frentes", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    gaps = consolidated.get("gaps", [])
    if gaps:
        story.append(Paragraph("Lacunas documentadas:", styles["subsection_heading"]))
        for gap in gaps:
            story.append(
                Paragraph(
                    f"  <b>{gap.get('base', '')}</b> — {gap.get('reason', '')}",
                    styles["bullet"],
                )
            )
            if gap.get("detail"):
                story.append(Paragraph(f"    {gap['detail']}", styles["body_small"]))
            if gap.get("suggested_action"):
                story.append(
                    Paragraph(
                        f"    Acao sugerida: {gap['suggested_action']}",
                        styles["body_small"],
                    )
                )
        story.append(Spacer(1, 0.3 * cm))

    frontiers = consolidated.get("next_frontiers", [])
    if frontiers:
        story.append(Paragraph("Proximas frentes de investigacao:", styles["subsection_heading"]))
        for frontier in frontiers:
            story.append(Paragraph(f"  -  {frontier}", styles["bullet"]))

    story.append(PageBreak())
    return story


def _make_legal_context_section(styles: dict, consolidated: dict) -> list:
    """Build legal context section."""
    story: list = []
    story.append(Paragraph("7. Contexto Legal Aplicavel", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    contexts = consolidated.get("legal_contexts", [])
    if contexts:
        for ctx in contexts:
            story.append(Paragraph(f"  -  {ctx}", styles["bullet"]))
    else:
        story.append(Paragraph("Nenhum contexto legal especifico registrado.", styles["no_hits"]))

    story.append(PageBreak())
    return story


def _make_appendix(styles: dict, consolidated: dict) -> list:
    """Build timestamps appendix."""
    story: list = []
    story.append(Paragraph("Apendice — Timestamps de Consulta", styles["section_heading"]))
    story.append(HRFlowable(width=INNER_WIDTH, thickness=0.5, color=_tpl.COLOR_BORDER))
    story.append(Spacer(1, 0.3 * cm))

    table_data = [["Base", "Data/Hora", "Queries", "Status", "Hits"]]
    for f in consolidated.get("findings", []):
        table_data.append(
            [
                f.get("base", ""),
                f.get("consulted_at", "")[:19],
                str(f.get("queries_executed", 0)),
                f.get("status", "ok"),
                str(len(f.get("hits", []))),
            ]
        )

    col_widths = [
        INNER_WIDTH * 0.18,
        INNER_WIDTH * 0.32,
        INNER_WIDTH * 0.15,
        INNER_WIDTH * 0.15,
        INNER_WIDTH * 0.10,
    ]
    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(_tpl.appendix_table_style())
    story.append(tbl)

    story.append(Spacer(1, 0.5 * cm))
    generated = datetime.now(timezone.utc).isoformat()
    story.append(
        Paragraph(
            f"Dossie gerado em: {generated}  |  Pipeline: due-diligence-transnacional v0.1.0",
            styles["body_small"],
        )
    )
    return story


# ---------------------------------------------------------------------------
# Main PDF builder
# ---------------------------------------------------------------------------

def build_dossier(
    consolidated: dict[str, Any],
    target: dict[str, Any],
    output_path: Path,
) -> None:
    """Assemble and write the full dossier PDF.

    Args:
        consolidated: Parsed findings-consolidated JSON.
        target: Parsed target YAML.
        output_path: Destination path for the PDF file.
    """
    target_name = consolidated.get("target_name") or target.get("nome_completo", "Alvo Desconhecido")
    generated_at = consolidated.get("consolidated_at", datetime.now(timezone.utc).isoformat())

    logger.info("Building dossier for: %s", target_name)

    styles = _tpl.build_styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN * 1.2,
        title=f"Dossie Due Diligence — {target_name}",
        author="due-diligence-transnacional pipeline",
        subject="Investigacao jornalistica transnacional",
    )

    page_label = _format_date(generated_at)

    def _page_footer(canvas: Any, doc: Any) -> None:
        _on_page(canvas, doc, target_name, page_label)

    story: list = []
    story.extend(_make_cover(styles, target_name, consolidated, generated_at))
    story.extend(_make_executive_summary(styles, consolidated))
    story.extend(_make_methodology(styles, consolidated))
    story.extend(_make_identity_section(styles, consolidated))
    story.extend(_make_findings_section(styles, consolidated))
    story.extend(_make_triangulation_section(styles, consolidated))
    story.extend(_make_gaps_section(styles, consolidated))
    story.extend(_make_legal_context_section(styles, consolidated))
    story.extend(_make_appendix(styles, consolidated))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    logger.info("PDF written to %s", output_path)


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
def main(consolidated: Path, target_path: Path, output: Path) -> None:
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

    output.parent.mkdir(parents=True, exist_ok=True)
    build_dossier(consolidated_data, target_data, output)


if __name__ == "__main__":
    main()
