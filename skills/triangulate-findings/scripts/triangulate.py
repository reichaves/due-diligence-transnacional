#!/usr/bin/env python3
"""
Purpose: Cross-reference findings from multiple database searches and produce
         a consolidated JSON with triangulations, high-confidence flags and gaps.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-05-01
Dependencies: click>=8.1 (see pyproject.toml)

Usage:
    python triangulate.py --findings-dir examples/case-fictional/findings/ \
        --output examples/case-fictional/findings.json
    python triangulate.py --findings-dir cases/fontana/findings/ \
        --target cases/fontana/target.yaml \
        --output cases/fontana/findings.json
"""

from __future__ import annotations

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Bases considered primary sources for confidence scoring
_PRIMARY_BASES = frozenset(
    ["FEC", "LDA", "FARA", "FL-SUNBIZ", "DE-CORPS", "TX-COMPTROLLER", "OPENCORPORATES"]
)
# Maximum day difference to consider two dates as coincident for the same entity
_DATE_MATCH_DAYS = 30

# Suffix tokens stripped when normalizing entity names for comparison
_ENTITY_SUFFIXES = frozenset(
    ["LLC", "INC", "CORP", "LTD", "LP", "LLP", "PLLC", "CO", "COMPANY", "INCORPORATED"]
)


def _normalize_entity(name: str) -> str:
    """Strip legal suffixes and lowercase an entity name for comparison."""
    parts = [p for p in name.upper().split() if p not in _ENTITY_SUFFIXES]
    return " ".join(parts).strip()


def _normalize_address(address: str) -> str:
    """Lowercase and strip address for prefix comparison."""
    return address.lower().strip()


def _normalize_name(name: str) -> str:
    """Lowercase a person name for comparison."""
    return name.lower().strip()


def load_findings(findings_dir: Path) -> list[dict[str, Any]]:
    """Load all JSON files from findings_dir.

    Args:
        findings_dir: Directory containing per-base findings JSON files.

    Returns:
        List of findings dicts, one per file successfully loaded.
    """
    results: list[dict[str, Any]] = []
    for path in sorted(findings_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if "base" not in data:
                logger.warning("Skipping %s — missing 'base' field", path.name)
                continue
            results.append(data)
            logger.info("Loaded %s (%d hits)", path.name, len(data.get("hits", [])))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load %s: %s", path.name, exc)
    return results


def _extract_normalized_hits(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten all hits into a list with base annotation.

    Each item: {base, source_id, norm_entity, norm_address, norm_name, date_str}
    """
    flat: list[dict[str, Any]] = []
    for f in findings:
        base = f.get("base", "UNKNOWN")
        for hit in f.get("hits", []):
            norm = hit.get("normalized", {})
            flat.append(
                {
                    "base": base,
                    "source_id": hit.get("source_id", ""),
                    "confidence_raw": hit.get("confidence", "indicio"),
                    "norm_entity": _normalize_entity(norm.get("entity_name", "")),
                    "norm_address": _normalize_address(norm.get("address", "")),
                    "norm_name": _normalize_name(norm.get("full_name", "")),
                    "date_str": norm.get("date", ""),
                    "raw_entity": norm.get("entity_name", ""),
                    "raw_address": norm.get("address", ""),
                    "raw_name": norm.get("full_name", ""),
                }
            )
    return flat


def _compute_confidence(sources: list[str]) -> str:
    """Determine confidence level based on how many distinct primary bases agree.

    Args:
        sources: List of base identifiers involved in the triangulation.

    Returns:
        'confirmado', 'provavel', or 'indicio'.
    """
    primary_count = sum(1 for s in sources if s in _PRIMARY_BASES)
    if primary_count >= 3:
        return "confirmado"
    if primary_count == 2:
        return "provavel"
    return "indicio"


def find_entity_matches(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group hits by normalized entity name and flag cross-base matches.

    Returns:
        List of entity_match triangulation dicts.
    """
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        if hit["norm_entity"]:
            index[hit["norm_entity"]].append(hit)

    triangulations: list[dict[str, Any]] = []
    for norm_entity, group in index.items():
        bases_seen = list({h["base"] for h in group})
        if len(bases_seen) < 2:
            continue
        raw_entity = next(h["raw_entity"] for h in group if h["raw_entity"])
        triangulations.append(
            {
                "type": "entity_match",
                "sources": bases_seen,
                "detail": (
                    f"Entidade '{raw_entity}' aparece em {len(bases_seen)} bases distintas: "
                    + ", ".join(bases_seen)
                ),
                "matched_value": raw_entity,
                "confidence": _compute_confidence(bases_seen),
                "source_ids": [h["source_id"] for h in group if h["source_id"]],
            }
        )
    return triangulations


def find_address_matches(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group hits by normalized address prefix and flag cross-base matches.

    Uses first 20 characters of normalized address to tolerate minor variations.

    Returns:
        List of address_match triangulation dicts.
    """
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    prefix_len = 20
    for hit in hits:
        if len(hit["norm_address"]) >= prefix_len:
            prefix = hit["norm_address"][:prefix_len]
            index[prefix].append(hit)

    triangulations: list[dict[str, Any]] = []
    for _prefix, group in index.items():
        bases_seen = list({h["base"] for h in group})
        if len(bases_seen) < 2:
            continue
        raw_address = next(h["raw_address"] for h in group if h["raw_address"])
        triangulations.append(
            {
                "type": "address_match",
                "sources": bases_seen,
                "detail": (
                    f"Endereço '{raw_address}' (ou variação) aparece em "
                    f"{len(bases_seen)} bases: " + ", ".join(bases_seen)
                ),
                "matched_value": raw_address,
                "confidence": _compute_confidence(bases_seen),
                "source_ids": [h["source_id"] for h in group if h["source_id"]],
            }
        )
    return triangulations


def find_person_matches(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group hits by normalized person name and flag cross-base matches.

    Returns:
        List of person_match triangulation dicts.
    """
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        if hit["norm_name"]:
            index[hit["norm_name"]].append(hit)

    triangulations: list[dict[str, Any]] = []
    for _norm_name, group in index.items():
        bases_seen = list({h["base"] for h in group})
        if len(bases_seen) < 2:
            continue
        raw_name = next(h["raw_name"] for h in group if h["raw_name"])
        triangulations.append(
            {
                "type": "person_match",
                "sources": bases_seen,
                "detail": (
                    f"Pessoa '{raw_name}' aparece em {len(bases_seen)} bases: "
                    + ", ".join(bases_seen)
                ),
                "matched_value": raw_name,
                "confidence": _compute_confidence(bases_seen),
                "source_ids": [h["source_id"] for h in group if h["source_id"]],
            }
        )
    return triangulations


def find_date_matches(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find cases where the same entity has dates within _DATE_MATCH_DAYS across bases.

    Only runs when an entity appears in ≥2 bases and has parseable dates.

    Returns:
        List of date_match triangulation dicts.
    """
    from datetime import date

    # Group by entity, then check dates
    entity_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        if hit["norm_entity"] and hit["date_str"]:
            entity_index[hit["norm_entity"]].append(hit)

    triangulations: list[dict[str, Any]] = []
    for norm_entity, group in entity_index.items():
        if len({h["base"] for h in group}) < 2:
            continue
        parsed: list[tuple[date, dict[str, Any]]] = []
        for h in group:
            try:
                parsed.append((date.fromisoformat(h["date_str"][:10]), h))
            except ValueError:
                continue
        if len(parsed) < 2:
            continue

        # Check all pairs
        for i, (d1, h1) in enumerate(parsed):
            for d2, h2 in parsed[i + 1 :]:
                if h1["base"] == h2["base"]:
                    continue
                diff = abs((d1 - d2).days)
                if diff <= _DATE_MATCH_DAYS:
                    raw_entity = h1["raw_entity"] or h2["raw_entity"]
                    triangulations.append(
                        {
                            "type": "date_match",
                            "sources": [h1["base"], h2["base"]],
                            "detail": (
                                f"Entidade '{raw_entity}' tem datas de registro/incorporação "
                                f"próximas: {d1} ({h1['base']}) e {d2} ({h2['base']}) "
                                f"— diferença de {diff} dias"
                            ),
                            "matched_value": str(d1),
                            "confidence": _compute_confidence([h1["base"], h2["base"]]),
                            "source_ids": [h1["source_id"], h2["source_id"]],
                        }
                    )
    return triangulations


def identify_gaps(
    findings: list[dict[str, Any]],
    expected_bases: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Build gap list: error findings, empty findings, and missing expected bases.

    Args:
        findings: All loaded findings dicts.
        expected_bases: Bases expected per target.yaml; if None, uses default set.

    Returns:
        List of gap dicts.
    """
    if expected_bases is None:
        expected_bases = list(
            _PRIMARY_BASES | {"NEWS-BR", "NEWS-US"}
        )

    found_bases = {f["base"] for f in findings}
    gaps: list[dict[str, Any]] = []

    # Error or partial findings
    for f in findings:
        status = f.get("status", "ok")
        if status in ("error", "partial"):
            gaps.append(
                {
                    "base": f["base"],
                    "reason": status,
                    "detail": f.get("error_message", "Script returned error/partial status"),
                    "suggested_action": f"Re-executar a sub-skill {f['base']} após corrigir o erro",
                }
            )
            continue
        # All variations in no_hits and zero hits
        if not f.get("hits") and f.get("no_hits"):
            gaps.append(
                {
                    "base": f["base"],
                    "reason": "no_hits",
                    "detail": (
                        f"{len(f['no_hits'])} variações testadas sem resultado: "
                        + ", ".join(f["no_hits"][:5])
                        + ("..." if len(f["no_hits"]) > 5 else "")
                    ),
                    "suggested_action": f"Verificar manualmente a base {f['base']} com variações adicionais",
                }
            )

    # Missing expected bases
    for base in expected_bases:
        if base not in found_bases:
            gaps.append(
                {
                    "base": base,
                    "reason": "not_searched",
                    "detail": f"Nenhum arquivo de findings encontrado para {base}",
                    "suggested_action": f"Executar a sub-skill correspondente a {base}",
                }
            )

    return gaps


def build_high_confidence_flags(triangulations: list[dict[str, Any]]) -> list[str]:
    """Derive plain-language high-confidence flags from triangulations.

    Returns:
        List of descriptive strings for the executive summary.
    """
    flags: list[str] = []
    for t in triangulations:
        if t["confidence"] in ("confirmado", "provavel"):
            sources_str = ", ".join(t["sources"])
            flags.append(
                f"{t['detail']} ({t['confidence']}, {len(t['sources'])} fontes: {sources_str})"
            )
    return flags


def aggregate_legal_contexts(findings: list[dict[str, Any]]) -> list[str]:
    """Collect unique legal context strings from all findings."""
    seen: set[str] = set()
    result: list[str] = []
    for f in findings:
        for ctx in f.get("legal_context", []):
            if ctx not in seen:
                seen.add(ctx)
                result.append(ctx)
    return result


def aggregate_next_frontiers(findings: list[dict[str, Any]]) -> list[str]:
    """Collect unique next-frontier strings from all findings."""
    seen: set[str] = set()
    result: list[str] = []
    for f in findings:
        for frontier in f.get("next_frontiers", []):
            if frontier not in seen:
                seen.add(frontier)
                result.append(frontier)
    return result


def triangulate(
    findings: list[dict[str, Any]],
    target_name: str,
    expected_bases: list[str] | None = None,
) -> dict[str, Any]:
    """Main triangulation logic.

    Args:
        findings: List of per-base findings dicts.
        target_name: Display name of the investigation target.
        expected_bases: Expected bases for gap detection.

    Returns:
        findings-consolidated dict matching findings-consolidated.schema.json.
    """
    hits = _extract_normalized_hits(findings)
    logger.info("Extracted %d normalized hits from %d bases", len(hits), len(findings))

    all_triangulations: list[dict[str, Any]] = []
    all_triangulations.extend(find_entity_matches(hits))
    all_triangulations.extend(find_address_matches(hits))
    all_triangulations.extend(find_person_matches(hits))
    all_triangulations.extend(find_date_matches(hits))

    logger.info("Found %d triangulations", len(all_triangulations))

    total_hits = sum(len(f.get("hits", [])) for f in findings)
    gaps = identify_gaps(findings, expected_bases)
    flags = build_high_confidence_flags(all_triangulations)

    return {
        "target_name": target_name,
        "consolidated_at": datetime.now(timezone.utc).isoformat(),
        "sources_count": len(findings),
        "total_hits": total_hits,
        "findings": findings,
        "triangulations": all_triangulations,
        "high_confidence_flags": flags,
        "gaps": gaps,
        "legal_contexts": aggregate_legal_contexts(findings),
        "next_frontiers": aggregate_next_frontiers(findings),
    }


@click.command()
@click.option(
    "--findings-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory containing per-base findings JSON files",
)
@click.option(
    "--target-name",
    default="",
    help="Target display name (falls back to directory basename if omitted)",
)
@click.option(
    "--output",
    default="-",
    show_default=True,
    help="Output file path. Use '-' for stdout.",
)
def main(findings_dir: Path, target_name: str, output: str) -> None:
    """Cross-reference per-base findings and output a consolidated JSON.

    Output matches schemas/findings-consolidated.schema.json.
    """
    findings = load_findings(findings_dir)
    if not findings:
        logger.error("No valid findings files found in %s", findings_dir)
        sys.exit(1)

    name = target_name.strip() or findings_dir.parent.name
    result = triangulate(findings, name)

    json_output = json.dumps(result, ensure_ascii=False, indent=2)

    if output == "-":
        print(json_output)
    else:
        try:
            Path(output).write_text(json_output, encoding="utf-8")
            logger.info("Consolidated findings written to %s", output)
        except OSError as exc:
            logger.error("Failed to write output: %s", exc)
            sys.exit(1)

    logger.info(
        "Triangulation complete: %d findings, %d triangulations, %d gaps",
        len(findings),
        len(result["triangulations"]),
        len(result["gaps"]),
    )


if __name__ == "__main__":
    main()
