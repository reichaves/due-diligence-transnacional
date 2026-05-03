"""
OpenCorporates officer search script.

Purpose: Search OpenCorporates for a person appearing as officer/director in
         companies across 140+ jurisdictions. Requires OPENCORPORATES_API_KEY
         environment variable (free tier: 500 req/month).
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-04-30
Dependencies: requests, click, python-dotenv
Usage:   python opencorporates_search.py --variations identity-variations.json [--output findings/opencorporates.json]
         python opencorporates_search.py --name "Carlos Ferreira" [--jurisdiction us_fl]
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional — env var can be set directly

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("opencorporates_search")

OC_BASE_URL = "https://api.opencorporates.com/v0.4"
RATE_LIMIT_SECONDS = 1.2  # Free tier limit; increase for paid plans
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0

# Offshore jurisdictions that warrant elevated attention
OFFSHORE_JURISDICTIONS = {
    "ky": "Cayman Islands",
    "vg": "British Virgin Islands",
    "bm": "Bermuda",
    "pa": "Panama",
    "us_de": "Delaware (offshore-equivalent)",
    "gg": "Guernsey",
    "je": "Jersey",
    "im": "Isle of Man",
    "bs": "Bahamas",
    "lc": "Saint Lucia",
}


def _build_session(api_key: str | None) -> requests.Session:
    """Build a requests Session with retry and API key header."""
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
    session.headers["User-Agent"] = (
        "due-diligence-transnacional/0.1 (investigative journalism; reichaves@gmail.com)"
    )
    if api_key:
        session.headers["Authorization"] = f"Token token={api_key}"
    return session


def _search_officers(
    session: requests.Session,
    name: str,
    jurisdiction_code: str | None,
    max_results: int,
    api_key: str | None,
) -> list[dict[str, Any]]:
    """Search OpenCorporates officers endpoint for a name."""
    logger.info("Searching OpenCorporates officers for: %s", name)
    params: dict[str, Any] = {
        "q": name,
        "per_page": min(max_results, 100),
        "order": "score",
    }
    if api_key and "Authorization" not in session.headers:
        params["api_token"] = api_key
    if jurisdiction_code:
        params["jurisdiction_code"] = jurisdiction_code

    url = f"{OC_BASE_URL}/officers/search"
    results: list[dict[str, Any]] = []
    page = 1

    while len(results) < max_results:
        params["page"] = page
        time.sleep(RATE_LIMIT_SECONDS)
        try:
            response = session.get(url, params=params, timeout=30)
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed: %s", exc)
            break

        if response.status_code == 429:
            logger.warning("Rate limited by OpenCorporates — waiting 60s")
            time.sleep(60)
            continue

        if response.status_code == 401:
            logger.error("OpenCorporates: invalid or missing API key")
            break

        if not response.ok:
            logger.warning("OpenCorporates returned %d for '%s'", response.status_code, name)
            break

        data = response.json()
        officers = (
            data.get("results", {})
            .get("officers", [])
        )
        if not officers:
            break

        for officer_wrapper in officers:
            officer = officer_wrapper.get("officer", officer_wrapper)
            results.append(officer)

        # Check pagination
        total_pages = (
            data.get("results", {})
            .get("total_pages", 1)
        )
        if page >= total_pages or len(results) >= max_results:
            break
        page += 1

    return results[:max_results]


def _get_company_detail(
    session: requests.Session,
    jurisdiction: str,
    company_number: str,
    api_key: str | None,
) -> dict[str, Any]:
    """Fetch company details from OpenCorporates."""
    url = f"{OC_BASE_URL}/companies/{jurisdiction}/{company_number}"
    params: dict[str, Any] = {}
    if api_key and "Authorization" not in session.headers:
        params["api_token"] = api_key

    time.sleep(RATE_LIMIT_SECONDS)
    try:
        response = session.get(url, params=params, timeout=30)
        if response.ok:
            return response.json().get("results", {}).get("company", {})
    except requests.exceptions.RequestException as exc:
        logger.warning("Failed to get company detail for %s/%s: %s", jurisdiction, company_number, exc)
    return {}


def _normalize_officer_hit(
    officer: dict[str, Any],
    variation: str,
    company_detail: dict[str, Any],
) -> dict[str, Any]:
    """Normalize an OpenCorporates officer record into findings schema format."""
    company = officer.get("company", company_detail)
    jurisdiction_code = company.get("jurisdiction_code", "")
    company_number = company.get("company_number", "")
    company_name = company.get("name", "")
    opencorporates_url = company.get("opencorporates_url", "")

    # Determine match type
    officer_name = officer.get("name", "")
    variation_words = set(variation.upper().split())
    officer_words = set(officer_name.upper().split())
    match_type = "exact" if variation_words.issubset(officer_words) else "fuzzy"

    # Flag offshore jurisdictions
    is_offshore = jurisdiction_code in OFFSHORE_JURISDICTIONS
    confidence = "provavel" if match_type == "exact" else "indicio"

    return {
        "variation_matched": variation,
        "match_type": match_type,
        "source_id": f"{jurisdiction_code}/{company_number}",
        "source_url": opencorporates_url or f"https://opencorporates.com/companies/{jurisdiction_code}/{company_number}",
        "confidence": confidence,
        "raw_record": {
            **officer,
            "_company_detail": company_detail,
            "_is_offshore_jurisdiction": is_offshore,
            "_offshore_jurisdiction_name": OFFSHORE_JURISDICTIONS.get(jurisdiction_code, ""),
        },
        "normalized": {
            "full_name": officer_name,
            "entity_name": company_name,
            "entity_type": company.get("company_type", ""),
            "role": officer.get("position", ""),
            "state": jurisdiction_code,
            "date": officer.get("start_date", ""),
        },
    }


def run_search(
    variations: list[str],
    jurisdiction_code: str | None = None,
    max_results_per_variation: int = 20,
    fetch_company_details: bool = False,
) -> dict[str, Any]:
    """Run OpenCorporates officer search for all name variations."""
    api_key = os.getenv("OPENCORPORATES_API_KEY")
    if not api_key:
        logger.warning(
            "OPENCORPORATES_API_KEY not set — running without key (strict rate limits apply)"
        )

    session = _build_session(api_key)
    hits: list[dict[str, Any]] = []
    no_hits: list[str] = []
    queries_executed = 0
    status = "ok"
    error_message = None
    offshore_flags: list[str] = []

    for variation in variations:
        found_something = False
        try:
            officers = _search_officers(
                session, variation, jurisdiction_code, max_results_per_variation, api_key
            )
            queries_executed += 1

            for officer in officers:
                company = officer.get("company", {})
                company_detail: dict[str, Any] = {}

                if fetch_company_details and company.get("jurisdiction_code") and company.get("company_number"):
                    company_detail = _get_company_detail(
                        session,
                        company["jurisdiction_code"],
                        company["company_number"],
                        api_key,
                    )

                hit = _normalize_officer_hit(officer, variation, company_detail)
                hits.append(hit)
                found_something = True

                # Track offshore hits separately for next_frontiers
                if hit["raw_record"].get("_is_offshore_jurisdiction"):
                    jur_name = hit["raw_record"].get("_offshore_jurisdiction_name", "")
                    offshore_flags.append(
                        f"{hit['normalized']['entity_name']} ({jur_name})"
                    )

        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error for '%s': %s", variation, exc)
            status = "partial"
            error_message = str(exc)

        if not found_something:
            no_hits.append(variation)

    next_frontiers = [
        "Para cada empresa ativa: verificar lista de officers completa no OpenCorporates",
        "Para empresas ativas no Brasil: verificar Junta Comercial (Receita Federal / CNPJ)",
    ]
    if offshore_flags:
        next_frontiers.insert(
            0,
            f"ALERTA OFFSHORE: empresas em jurisdições de baixa transparência detectadas: "
            + "; ".join(offshore_flags[:5]),
        )
        next_frontiers.append(
            "Verificar ICIJ Offshore Leaks Database (offshoreleaks.icij.org) para as empresas offshore"
        )
        next_frontiers.append(
            "Para empresas americanas pós-2024: verificar FinCEN Beneficial Ownership "
            "Information (BOI) — acesso restrito a autoridades"
        )

    return {
        "base": "OPENCORPORATES",
        "consulted_at": datetime.now(tz=timezone.utc).isoformat(),
        "queries_executed": queries_executed,
        "status": status,
        "error_message": error_message,
        "hits": hits,
        "no_hits": no_hits,
        "legal_context": [
            (
                "OpenCorporates agrega dados de registros corporativos públicos de 140+ "
                "jurisdições. Dados têm atraso variável (1 dia a vários meses) em relação "
                "aos registros primários. Sempre confirmar no registro primário antes de "
                "publicar."
            ),
        ],
        "next_frontiers": next_frontiers,
        "methodology_note": (
            f"Busca realizada via OpenCorporates API v0.4 endpoint /officers/search. "
            f"API key configurada: {'sim' if api_key else 'não (limite estrito)'}. "
            f"Jurisdição filtrada: {jurisdiction_code or 'todas'}. "
            f"Max resultados por variação: {max_results_per_variation}. "
            "Dados podem ter atraso em relação ao registro primário."
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
    "--jurisdiction",
    "jurisdiction_code",
    default=None,
    help="Filter by jurisdiction code (e.g. us_fl, ky, vg)",
)
@click.option(
    "--max-results",
    "max_results",
    default=20,
    show_default=True,
    help="Max results per name variation",
)
@click.option(
    "--fetch-details",
    "fetch_details",
    is_flag=True,
    default=False,
    help="Fetch full company detail for each hit (uses more API quota)",
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
    jurisdiction_code: str | None,
    max_results: int,
    fetch_details: bool,
    output_path: Path | None,
) -> None:
    """Search OpenCorporates for a person as company officer across 140+ jurisdictions."""
    if not variations_path and not single_name:
        raise click.UsageError("Provide --variations or --name")

    if variations_path:
        data = json.loads(variations_path.read_text(encoding="utf-8"))
        variations: list[str] = [v["name_string"] for v in data.get("variations", [])]
    else:
        variations = [single_name]  # type: ignore[list-item]

    logger.info("Starting OpenCorporates search for %d variations", len(variations))
    findings = run_search(
        variations,
        jurisdiction_code=jurisdiction_code,
        max_results_per_variation=max_results,
        fetch_company_details=fetch_details,
    )

    output_json = json.dumps(findings, ensure_ascii=False, indent=2)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json, encoding="utf-8")
        logger.info("Findings written to %s", output_path)
    else:
        click.echo(output_json)


if __name__ == "__main__":
    main()
