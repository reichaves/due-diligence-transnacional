"""
FEC Schedule A contributor search — Level 3 fallback.

Purpose  : Query the FEC REST API for campaign contributions by name variations.
Author   : Reinaldo Chaves / due-diligence-transnacional
Date     : 2026-05-06
Dependencies: requests (stdlib only except requests; install via pip install requests)

Usage:
  python skills/search-fec/scripts/fec_search.py \
      --variations identity-variations.json \
      --output findings/fec.json

Environment:
  FEC_API_KEY — read from .env at project root, then os.environ, then DEMO_KEY.
  DEMO_KEY is the FEC public demo key (1,000 req/day; not suitable for production).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# .env loader — must run before any os.environ access
# ---------------------------------------------------------------------------

def _load_dotenv(start: Path) -> None:
    """Walk up from *start* looking for a .env file; load it into os.environ."""
    candidate = start
    for _ in range(5):  # search up to 5 levels up
        env_file = candidate / ".env"
        if env_file.exists():
            logger.debug("Loading .env from %s", env_file)
            for raw_line in env_file.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
            return
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    logger.warning(".env not found — using system environment variables only")


_load_dotenv(Path(__file__).resolve().parent.parent.parent.parent)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEC_API_KEY = os.environ.get("FEC_API_KEY", "DEMO_KEY")
FEC_BASE_URL = "https://api.open.fec.gov/v1"
RATE_LIMIT_SLEEP = 1.1  # seconds between requests (conservative)
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry

LEGAL_CONTEXT = (
    "52 U.S.C. § 30121 proíbe nacionais estrangeiros (que não sejam green card holders) "
    "de fazer contribuições ou gastos em eleições federais, estaduais ou locais americanas. "
    "Ausência de hits em FEC para cidadão brasileiro sem residência permanente nos EUA é o "
    "resultado esperado e legalmente coerente — não é um achado negativo em si."
)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _get(endpoint: str, params: dict) -> dict:
    """GET with retry/backoff. Raises on unrecoverable error."""
    url = f"{FEC_BASE_URL}{endpoint}"
    params = {**params, "api_key": FEC_API_KEY}
    delay = RETRY_BACKOFF
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 429:
                logger.warning("Rate limited (attempt %d/%d) — sleeping %ss", attempt, MAX_RETRIES, delay)
                time.sleep(delay)
                delay *= 2
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("Request failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"FEC API unreachable after {MAX_RETRIES} attempts") from last_exc


def search_contributions(contributor_name: str) -> list[dict]:
    """Return raw Schedule A hits for *contributor_name*."""
    try:
        data = _get(
            "/schedules/schedule_a/",
            {"contributor_name": contributor_name, "per_page": 20, "sort": "-contribution_receipt_date"},
        )
        return data.get("results", [])
    except RuntimeError as exc:
        logger.error("search_contributions(%r) failed: %s", contributor_name, exc)
        return []


# ---------------------------------------------------------------------------
# Result processing
# ---------------------------------------------------------------------------

def _match_type(query: str, returned_name: str) -> str:
    return "exact" if query.lower() == returned_name.lower() else "fuzzy"


def _normalize_hit(raw: dict, query: str) -> dict:
    name = raw.get("contributor_name", "")
    return {
        "match_type": _match_type(query, name),
        "source_id": raw.get("transaction_id", ""),
        "source_url": (
            f"https://www.fec.gov/data/receipts/?transaction_id={raw.get('transaction_id', '')}"
        ),
        "raw_record": {
            "contributor_name": name,
            "contributor_employer": raw.get("contributor_employer"),
            "contributor_occupation": raw.get("contributor_occupation"),
            "contributor_city": raw.get("contributor_city"),
            "contributor_state": raw.get("contributor_state"),
            "date": raw.get("contribution_receipt_date"),
            "amount_usd": raw.get("contribution_receipt_amount"),
            "committee_id": raw.get("committee_id"),
            "committee_name": raw.get("committee_name"),
        },
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(variations_path: Path, output_path: Path) -> None:
    logger.info("FEC search — Level 3 (script). API key: %s", "DEMO_KEY" if FEC_API_KEY == "DEMO_KEY" else "***set***")
    if FEC_API_KEY == "DEMO_KEY":
        logger.warning("Using DEMO_KEY (1,000 req/day limit). Set FEC_API_KEY in .env for higher limits.")

    # Load name variations
    variations_data = json.loads(variations_path.read_text(encoding="utf-8"))
    variations: list[str] = [v["name_string"] for v in variations_data.get("variations", [])]
    if not variations:
        logger.error("No variations found in %s", variations_path)
        sys.exit(1)

    hits: list[dict] = []
    no_hits: list[str] = []
    queries_executed = 0

    for name in variations:
        logger.info("Querying FEC for: %r", name)
        results = search_contributions(name)
        queries_executed += 1
        time.sleep(RATE_LIMIT_SLEEP)

        if results:
            for raw in results:
                hits.append(_normalize_hit(raw, name))
            logger.info("  → %d result(s)", len(results))
        else:
            no_hits.append(name)
            logger.info("  → no results")

    api_key_label = "DEMO_KEY" if FEC_API_KEY == "DEMO_KEY" else "FEC_API_KEY (from .env)"
    findings = {
        "base": "FEC",
        "consulted_at": datetime.now(timezone.utc).isoformat(),
        "queries_executed": queries_executed,
        "status": "ok",
        "hits": hits,
        "no_hits": no_hits,
        "legal_context": [LEGAL_CONTEXT],
        "next_frontiers": [
            "Verificar se o alvo possui green card ou cidadania americana",
            "Verificar 501(c)(4)s e dark money groups",
            "Verificar PACs estaduais em Florida e Texas",
        ],
        "methodology_note": (
            f"Busca executada via script Python fec_search.py com API REST da FEC "
            f"(/schedules/schedule_a/). Chave usada: {api_key_label}. "
            f"fec-mcp-server não disponível nesta sessão (Level 3 fallback). "
            f"Cobre registros digitalizados 1980–presente."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Findings saved to %s (%d hits, %d no-hits)", output_path, len(hits), len(no_hits))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FEC Schedule A contributor search (Level 3 fallback)")
    parser.add_argument("--variations", required=True, type=Path, help="Path to identity-variations.json")
    parser.add_argument("--output", required=True, type=Path, help="Output path for findings JSON")
    args = parser.parse_args()
    run(args.variations, args.output)
