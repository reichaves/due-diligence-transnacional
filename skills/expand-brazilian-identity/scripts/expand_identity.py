#!/usr/bin/env python3
"""
Purpose: Generate name variations for a target of any nationality for use in US database searches.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-04-30
Dependencies: click>=8.1 (see pyproject.toml)

Usage:
    python expand_identity.py --name "Carlos Eduardo Ferreira"
    python expand_identity.py --name "João Silva" --alias "John Silva" --approved
    python expand_identity.py --name "Pablo Vargas Mendoza" --origin-country PE
    python expand_identity.py --name "Maria Souza" \
        --relatives '[{"nome": "Pedro Souza", "relacao": "conjuge"}]' \
        --output variations.json
"""
import json
import logging
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Any

import click

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def remove_diacritics(text: str) -> str:
    """Remove diacritical marks from a string.

    Args:
        text: Input string, possibly containing Unicode diacritics.

    Returns:
        ASCII-safe string with combining characters stripped.

    Examples:
        >>> remove_diacritics("João")
        'Joao'
        >>> remove_diacritics("Ângelo")
        'Angelo'
        >>> remove_diacritics("Souça")
        'Souca'
    """
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def parse_name_parts(full_name: str) -> tuple[str, str, list[str]]:
    """Split a full name into first, last, and middle parts.

    Args:
        full_name: Full name string (may include diacritics).

    Returns:
        Tuple of (first_name, last_name, middle_parts).
        last_name is empty string for single-word names.
    """
    parts = full_name.strip().split()
    if not parts:
        return ("", "", [])
    first = parts[0]
    if len(parts) == 1:
        return (first, "", [])
    last = parts[-1]
    middles = parts[1:-1]
    return (first, last, middles)


def build_variations(
    full_name: str,
    relatives: list[dict[str, str]] | None = None,
    aliases: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Generate a list of name variations for US database searches.

    Produces at least 5 variation types for any multi-part name:
    full_name, first_last, last_first, initials_last, surname_only.
    Adds no_accents when the name contains diacritics.

    Args:
        full_name: Complete name of the target (Portuguese, may have accents).
        relatives: List of dicts with 'nome' and 'relacao' keys.
        aliases: Known alternate spellings or nicknames.

    Returns:
        List of variation dicts, each with 'variation', 'type', and 'note'.
    """
    first, last, middles = parse_name_parts(full_name)
    no_acc_full = remove_diacritics(full_name)
    first_no = remove_diacritics(first)
    last_no = remove_diacritics(last) if last else ""
    parts_no_acc = no_acc_full.split()

    variations: list[dict[str, Any]] = []

    # 1. Full name as provided
    variations.append(
        {
            "variation": full_name,
            "type": "full_name",
            "note": "Nome completo conforme fornecido",
        }
    )

    # 2. Full name without diacritics (only when different)
    if no_acc_full != full_name:
        variations.append(
            {
                "variation": no_acc_full,
                "type": "no_accents",
                "note": "Nome completo sem acentuação",
            }
        )

    if last:
        # 3. First name + last name only (no accents)
        first_last = f"{first_no} {last_no}"
        if first_last != no_acc_full:
            variations.append(
                {
                    "variation": first_last,
                    "type": "first_last",
                    "note": "Primeiro nome + último sobrenome, sem acentos",
                }
            )

        # 4. Inverted order: last + first (common in US forms)
        variations.append(
            {
                "variation": f"{last_no} {first_no}",
                "type": "last_first",
                "note": "Ordem invertida (sobrenome, nome) — comum em formulários americanos",
            }
        )

        # 5. Initials + last name
        if len(parts_no_acc) > 2:
            # All initials except last part: "C. E. Ferreira"
            initials_all = ". ".join(p[0] for p in parts_no_acc[:-1]) + "."
            variations.append(
                {
                    "variation": f"{initials_all} {last_no}",
                    "type": "initials_last",
                    "note": "Todas as iniciais + último sobrenome",
                }
            )

        # First initial + last name only: "C. Ferreira"
        variations.append(
            {
                "variation": f"{first_no[0]}. {last_no}",
                "type": "initials_last",
                "note": "Primeira inicial + último sobrenome",
            }
        )

        # 6. Surname only (broad search — high noise)
        variations.append(
            {
                "variation": last_no,
                "type": "surname_only",
                "note": "Sobrenome isolado — busca ampla, alto ruído; verificar manualmente",
            }
        )

    # 7. Aliases
    for alias in aliases or []:
        alias_clean = alias.strip()
        if alias_clean:
            variations.append(
                {
                    "variation": alias_clean,
                    "type": "alias",
                    "note": "Apelido ou nome alternativo fornecido pelo usuário",
                }
            )

    # 8. Relatives
    for rel in relatives or []:
        rel_name: str = rel.get("nome", "").strip()
        rel_rel: str = rel.get("relacao", "outro")
        if not rel_name:
            continue
        rel_no = remove_diacritics(rel_name)
        _, rel_last, _ = parse_name_parts(rel_name)
        rel_last_no = remove_diacritics(rel_last) if rel_last else ""

        variations.append(
            {
                "variation": rel_no,
                "type": "relative",
                "note": f"{rel_rel.capitalize()}: {rel_name}",
            }
        )
        if rel_last_no and rel_last_no != rel_no:
            variations.append(
                {
                    "variation": rel_last_no,
                    "type": "relative",
                    "note": f"{rel_rel.capitalize()} sobrenome isolado: {rel_last}",
                }
            )

    return variations


def build_output(
    full_name: str,
    variations: list[dict[str, Any]],
    approved: bool = False,
) -> dict[str, Any]:
    """Assemble the identity-variations.json payload.

    Args:
        full_name: Original target name.
        variations: List of variation dicts from build_variations().
        approved: Whether a human has reviewed and approved this list.

    Returns:
        Dict matching schemas/identity-variations.schema.json.
    """
    payload: dict[str, Any] = {
        "target_name": full_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "approved_by_human": approved,
        "variations": variations,
    }
    if approved:
        payload["approved_at"] = datetime.now(timezone.utc).isoformat()
    return payload


@click.command()
@click.option(
    "--name",
    required=True,
    help="Nome completo do alvo (ex: 'Carlos Eduardo Ferreira')",
)
@click.option(
    "--alias",
    "aliases",
    multiple=True,
    help="Apelido ou variação conhecida (pode repetir a flag)",
)
@click.option(
    "--relatives",
    default=None,
    help='JSON com parentes: \'[{"nome": "Carla Ferreira", "relacao": "conjuge"}]\'',
)
@click.option(
    "--origin-country",
    "origin_country",
    default="BR",
    show_default=True,
    help="País de origem do alvo (ISO 3166-1 alpha-2, ex: BR, PE, CO, AR, MX). "
    "Afeta apenas mensagens de log — o algoritmo de variações é genérico.",
)
@click.option(
    "--output",
    default="-",
    show_default=True,
    help="Arquivo de saída. Use '-' para stdout.",
)
@click.option(
    "--approved",
    is_flag=True,
    default=False,
    help="Marcar como aprovado por humano (para testes — normalmente feito interativamente)",
)
def main(
    name: str,
    aliases: tuple[str, ...],
    relatives: str | None,
    origin_country: str,
    output: str,
    approved: bool,
) -> None:
    """Generate name variations for a target of any nationality for US database searches.

    Output is a JSON document matching schemas/identity-variations.schema.json.
    Pipe to a file or use --output to persist.
    """
    logger.info("Expanding identity for: %s (origin: %s)", name, origin_country.upper())

    relatives_list: list[dict[str, str]] = []
    if relatives:
        try:
            relatives_list = json.loads(relatives)
        except json.JSONDecodeError as exc:
            raise click.BadParameter(
                f"--relatives must be valid JSON array: {exc}", param_hint="--relatives"
            ) from exc
        if not isinstance(relatives_list, list):
            raise click.BadParameter(
                "--relatives must be a JSON array of objects", param_hint="--relatives"
            )

    variations = build_variations(name, relatives=relatives_list, aliases=list(aliases))
    result = build_output(name, variations, approved=approved)

    json_output = json.dumps(result, ensure_ascii=False, indent=2)

    if output == "-":
        print(json_output)
    else:
        try:
            with open(output, "w", encoding="utf-8") as fh:
                fh.write(json_output)
            logger.info("Output written to %s", output)
        except OSError as exc:
            logger.error("Failed to write output file: %s", exc)
            sys.exit(1)

    logger.info("Generated %d variations for '%s'", len(variations), name)


if __name__ == "__main__":
    main()
