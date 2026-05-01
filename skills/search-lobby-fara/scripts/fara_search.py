"""
FARA Foreign Agents Registration Act search script.

Purpose: Search the DOJ eFile FARA database for a person or entity appearing
         as a registrant or foreign principal, and return structured JSON findings.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-04-30
Dependencies: requests, click
Usage:   python fara_search.py --variations identity-variations.json [--output findings/fara.json]
         python fara_search.py --name "Ricardo Magro"
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fara_search")

FARA_BASE_URL = "https://efile.fara.gov/api/v1"
DEFAULT_HEADERS = {
    "User-Agent": (
        "due-diligence-transnacional/0.1 "
        "(investigative journalism tool; contact: reichaves@gmail.com)"
    ),
    "Accept": "application/json",
}
RATE_LIMIT_SECONDS = 2.0  # FARA API is rate-limited
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0


def _build_session() -> requests.Session:
    """Build a requests Session with retry and backoff configured."""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


def search_registrants(
    session: requests.Session, name: str
) -> list[dict[str, Any]]:
    """Search FARA for registrants matching the name."""
    logger.info("Searching FARA registrants for: %s", name)
    url = f"{FARA_BASE_URL}/Registrant/json/"
    time.sleep(RATE_LIMIT_SECONDS)
    try:
        response = session.get(url, params={"name": name, "page_size": 50}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("REGISTRANT_SEARCH", {}).get("SEARCH_RESULT", {}).get("REGISTRANT", [])
    except requests.exceptions.RequestException as exc:
        logger.error("FARA registrant search failed for '%s': %s", name, exc)
        return []


def search_foreign_principals(
    session: requests.Session, name: str
) -> list[dict[str, Any]]:
    """Search FARA for foreign principals matching the name."""
    logger.info("Searching FARA foreign principals for: %s", name)
    url = f"{FARA_BASE_URL}/ForeignPrincipal/json/"
    time.sleep(RATE_LIMIT_SECONDS)
    try:
        response = session.get(url, params={"name": name, "page_size": 50}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("FOREIGN_PRINCIPAL_SEARCH", {}).get("SEARCH_RESULT", {}).get("FOREIGN_PRINCIPAL", [])
    except requests.exceptions.RequestException as exc:
        logger.error("FARA foreign principal search failed for '%s': %s", name, exc)
        return []


def search_active_principals(
    session: requests.Session, name: str
) -> list[dict[str, Any]]:
    """Search FARA for active foreign principals matching the name."""
    logger.info("Searching FARA active foreign principals for: %s", name)
    url = f"{FARA_BASE_URL}/ActivePrincipal/json/"
    time.sleep(RATE_LIMIT_SECONDS)
    try:
        response = session.get(url, params={"name": name, "page_size": 50}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return (
            data.get("ACTIVE_FOREIGN_PRINCIPAL_SEARCH", {})
            .get("SEARCH_RESULT", {})
            .get("FOREIGN_PRINCIPAL", [])
        )
    except requests.exceptions.RequestException as exc:
        logger.error("FARA active principal search failed for '%s': %s", name, exc)
        return []


def _normalize_registrant(
    registrant: dict[str, Any], variation: str
) -> dict[str, Any]:
    """Normalize a FARA registrant record into findings schema format."""
    reg_number = str(registrant.get("Registration_Number", ""))
    return {
        "variation_matched": variation,
        "match_type": "exact",
        "source_id": reg_number,
        "source_url": f"https://efile.fara.gov/docs/{reg_number}/",
        "confidence": "confirmado",
        "raw_record": {
            **registrant,
            "_record_type": "registrant",
        },
        "normalized": {
            "full_name": registrant.get("Name", ""),
            "entity_name": registrant.get("Name", ""),
            "role": "registrant",
            "date": registrant.get("Registration_Date", ""),
        },
    }


def _normalize_foreign_principal(
    principal: dict[str, Any], variation: str, active: bool = False
) -> dict[str, Any]:
    """Normalize a FARA foreign principal record into findings schema format."""
    reg_number = str(principal.get("Registration_Number", ""))
    return {
        "variation_matched": variation,
        "match_type": "exact",
        "source_id": f"{reg_number}-fp",
        "source_url": f"https://efile.fara.gov/docs/{reg_number}/",
        "confidence": "confirmado" if active else "provavel",
        "raw_record": {
            **principal,
            "_record_type": "foreign_principal",
            "_active": active,
        },
        "normalized": {
            "full_name": principal.get("Foreign_Principal", ""),
            "entity_name": principal.get("Foreign_Principal", ""),
            "role": "foreign_principal",
            "date": principal.get("Date_Stamped", ""),
            "state": principal.get("Country", ""),
        },
    }


def run_search(variations: list[str]) -> dict[str, Any]:
    """Run FARA search for all name variations and return findings dict."""
    session = _build_session()
    hits: list[dict[str, Any]] = []
    no_hits: list[str] = []
    queries_executed = 0
    status = "ok"
    error_message = None

    for variation in variations:
        found_something = False

        try:
            registrants = search_registrants(session, variation)
            queries_executed += 1
            for r in registrants:
                hits.append(_normalize_registrant(r, variation))
                found_something = True

            foreign_principals = search_foreign_principals(session, variation)
            queries_executed += 1
            for fp in foreign_principals:
                hits.append(_normalize_foreign_principal(fp, variation, active=False))
                found_something = True

            active_principals = search_active_principals(session, variation)
            queries_executed += 1
            for ap in active_principals:
                # Avoid duplicating hits already found above
                ap_reg = str(ap.get("Registration_Number", ""))
                already_found = any(
                    h["source_id"] == f"{ap_reg}-fp" for h in hits
                )
                if not already_found:
                    hits.append(_normalize_foreign_principal(ap, variation, active=True))
                    found_something = True

        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error for variation '%s': %s", variation, exc)
            status = "partial"
            error_message = str(exc)

        if not found_something:
            no_hits.append(variation)

    return {
        "base": "FARA",
        "consulted_at": datetime.now(tz=timezone.utc).isoformat(),
        "queries_executed": queries_executed,
        "status": status,
        "error_message": error_message,
        "hits": hits,
        "no_hits": no_hits,
        "legal_context": [
            (
                "FARA (22 U.S.C. § 611 et seq.) exige registro de agentes que atuam "
                "em nome de entidade ou governo estrangeiro em atividades políticas, "
                "de relações públicas ou de lobby nos EUA. Penalidade criminal: até "
                "5 anos de prisão."
            ),
            (
                "FARA tem atraso histórico de até 90 dias entre o início da atividade "
                "e a disponibilização pública no eFile. Ausência no banco digital não "
                "exclui registros físicos pré-2008 nem registros tardios."
            ),
            (
                "Isenção LDA: agentes já registrados no LDA podem ser isentos de FARA, "
                "mas o DOJ tem restringido essa isenção desde 2017 (caso Manafort)."
            ),
        ],
        "next_frontiers": [
            "Verificar registros físicos pré-2008 via FOIA ao DOJ se alvo tiver atividade anterior",
            "Verificar se há Supplemental Statement (relatório semestral de atividades)",
            "Cruzar com LDA: a mesma atividade pode estar registrada em ambos",
            "Verificar se o principal estrangeiro é governo ou empresa do governo brasileiro",
        ],
        "methodology_note": (
            "Busca realizada via API eFile FARA (efile.fara.gov/api/v1). "
            "Campos pesquisados: Registrant/name, ForeignPrincipal/name, "
            "ActivePrincipal/name. Cobertura digital: 2008–presente. "
            "Registros anteriores requerem FOIA."
        ),
    }


@click.command()
@click.option(
    "--variations",
    "variations_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to identity-variations.json",
)
@click.option(
    "--name",
    "single_name",
    default=None,
    help="Single name to search (alternative to --variations)",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for findings JSON (default: stdout)",
)
def main(
    variations_path: Path | None,
    single_name: str | None,
    output_path: Path | None,
) -> None:
    """Search FARA (Foreign Agents Registration Act) database for a Brazilian person."""
    if not variations_path and not single_name:
        raise click.UsageError("Provide --variations or --name")

    if variations_path:
        data = json.loads(variations_path.read_text(encoding="utf-8"))
        variations: list[str] = [v["name_string"] for v in data.get("variations", [])]
    else:
        variations = [single_name]  # type: ignore[list-item]

    logger.info("Starting FARA search for %d variations", len(variations))
    findings = run_search(variations)

    output_json = json.dumps(findings, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding="utf-8")
        logger.info("Findings written to %s", output_path)
    else:
        click.echo(output_json)


if __name__ == "__main__":
    main()
