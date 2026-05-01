"""
LDA Lobbying Disclosure Act search script.

Purpose: Search the Senate LDA Disclosure Database for a person (as lobbyist
         or client) and return structured JSON findings.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-04-30
Dependencies: requests, click, python-dotenv
Usage:   python lda_search.py --variations identity-variations.json [--output findings/lda.json]
         python lda_search.py --name "Ricardo Magro"
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
logger = logging.getLogger("lda_search")

LDA_BASE_URL = "https://lda.senate.gov/api/v1"
DEFAULT_HEADERS = {
    "User-Agent": (
        "due-diligence-transnacional/0.1 "
        "(investigative journalism tool; contact: reichaves@gmail.com)"
    ),
    "Accept": "application/json",
}
RATE_LIMIT_SECONDS = 1.5  # Senate API is lenient but be respectful
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


def _get_paginated(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fetch all pages of a paginated LDA API endpoint."""
    results: list[dict[str, Any]] = []
    params = {**params, "page_size": 25}
    while url:
        time.sleep(RATE_LIMIT_SECONDS)
        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            logger.warning("HTTP error fetching %s: %s", url, exc)
            break
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed for %s: %s", url, exc)
            break

        data = response.json()
        results.extend(data.get("results", []))

        # LDA API uses cursor-based pagination via 'next'
        url = data.get("next")
        params = {}  # next URL already includes all params

    return results


def search_lobbyists(session: requests.Session, name: str) -> list[dict[str, Any]]:
    """Search for a person as an individual lobbyist."""
    logger.info("Searching LDA lobbyists for: %s", name)
    url = f"{LDA_BASE_URL}/lobbyists/"
    return _get_paginated(session, url, {"name": name})


def search_filings_by_lobbyist(
    session: requests.Session, name: str
) -> list[dict[str, Any]]:
    """Search filings where the person appears as a lobbyist."""
    logger.info("Searching LDA filings (lobbyist) for: %s", name)
    url = f"{LDA_BASE_URL}/filings/"
    return _get_paginated(session, url, {"lobbyist_name": name})


def search_filings_by_client(
    session: requests.Session, name: str
) -> list[dict[str, Any]]:
    """Search filings where the person/org appears as a client."""
    logger.info("Searching LDA filings (client) for: %s", name)
    url = f"{LDA_BASE_URL}/filings/"
    return _get_paginated(session, url, {"client_name": name})


def _normalize_filing(
    filing: dict[str, Any], variation: str, role: str
) -> dict[str, Any]:
    """Normalize a raw LDA filing into the findings schema format."""
    filing_uuid = filing.get("filing_uuid", "")
    filing_url = f"https://lda.senate.gov/filings/public/filing/{filing_uuid}/print/"
    return {
        "variation_matched": variation,
        "match_type": "exact",
        "source_id": filing_uuid,
        "source_url": filing_url,
        "confidence": "confirmado",
        "raw_record": {
            **filing,
            "_role_context": role,
        },
        "normalized": {
            "full_name": variation,
            "entity_name": filing.get("registrant", {}).get("name", ""),
            "role": role,
            "date": filing.get("dt_posted", ""),
            "amount_usd": filing.get("income"),
        },
    }


def run_search(
    variations: list[str],
) -> dict[str, Any]:
    """Run LDA search for all name variations and return findings dict."""
    session = _build_session()
    hits: list[dict[str, Any]] = []
    no_hits: list[str] = []
    queries_executed = 0
    status = "ok"
    error_message = None

    for variation in variations:
        found_something = False

        try:
            # Search as lobbyist name in filings
            filings = search_filings_by_lobbyist(session, variation)
            queries_executed += 1
            for filing in filings:
                hits.append(_normalize_filing(filing, variation, "lobbyist"))
                found_something = True

            # Search as client name in filings
            client_filings = search_filings_by_client(session, variation)
            queries_executed += 1
            for filing in client_filings:
                hits.append(_normalize_filing(filing, variation, "client"))
                found_something = True

        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error for variation '%s': %s", variation, exc)
            status = "partial"
            error_message = str(exc)

        if not found_something:
            no_hits.append(variation)

    return {
        "base": "LDA",
        "consulted_at": datetime.now(tz=timezone.utc).isoformat(),
        "queries_executed": queries_executed,
        "status": status,
        "error_message": error_message,
        "hits": hits,
        "no_hits": no_hits,
        "legal_context": [
            (
                "LDA (2 U.S.C. § 1601 et seq.) registra lobbistas que fazem contato "
                "com funcionários do Congresso ou Executivo federal em nome de cliente. "
                "Limiar: ≥ 2 contatos em 3 meses E ≥ 20% do tempo E ≥ USD 3.000 "
                "em honorários trimestrais."
            ),
            (
                "Ausência no LDA não exclui atividade de lobby abaixo dos limiares "
                "de registro, ou lobby estadual (que usa registros estaduais)."
            ),
        ],
        "next_frontiers": [
            "Verificar FARA se o alvo atuou em nome de governo ou entidade estrangeira",
            "Verificar registros de lobby estadual (FL, TX) se atividade foi subnacional",
            "Verificar OpenSecrets para análise de padrões de contribuição do client",
        ],
        "methodology_note": (
            "Busca realizada via API REST Senate LDA Disclosure (lda.senate.gov/api/v1). "
            "Cobre filings desde 1999. Campos pesquisados: lobbyist_name e client_name. "
            "Resultados são case-insensitive mas dependem do nome exato inserido no sistema."
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
    """Search LDA Lobby Disclosure Act database for a Brazilian person."""
    if not variations_path and not single_name:
        raise click.UsageError("Provide --variations or --name")

    if variations_path:
        data = json.loads(variations_path.read_text(encoding="utf-8"))
        variations: list[str] = [v["name_string"] for v in data.get("variations", [])]
    else:
        variations = [single_name]  # type: ignore[list-item]

    logger.info("Starting LDA search for %d variations", len(variations))
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
