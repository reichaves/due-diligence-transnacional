#!/usr/bin/env python3
"""
Purpose: Full due-diligence pipeline CLI — reads target.yaml, expands identity,
         orchestrates search sub-skills, triangulates findings and generates PDF.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-05-01
Dependencies: click>=8.1, pyyaml>=6.0, (see pyproject.toml)

Usage:
    python scripts/run_pipeline.py --target examples/case-fictional/target.yaml
    python scripts/run_pipeline.py --target cases/fontana/target.yaml --output-dir cases/fontana/
    python scripts/run_pipeline.py --target target.yaml --skip-search --findings-dir findings/
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_pipeline")

ROOT = Path(__file__).parent.parent

_EXPAND_SCRIPT = ROOT / "skills" / "expand-brazilian-identity" / "scripts" / "expand_identity.py"
_TRIANGULATE_SCRIPT = ROOT / "skills" / "triangulate-findings" / "scripts" / "triangulate.py"
_GENERATE_SCRIPT = ROOT / "skills" / "generate-dossier-pdf" / "scripts" / "generate_report.py"

_SEARCH_SCRIPTS: dict[str, Path] = {
    "fec": ROOT / "skills" / "search-fec" / "scripts" / "fec_search.py",
    "lda": ROOT / "skills" / "search-lobby-fara" / "scripts" / "lda_search.py",
    "fara": ROOT / "skills" / "search-lobby-fara" / "scripts" / "fara_search.py",
    "fl-sunbiz": ROOT / "skills" / "search-state-corps" / "scripts" / "florida_sunbiz.py",
    "de-corps": ROOT / "skills" / "search-state-corps" / "scripts" / "delaware_corp.py",
    "tx-comptroller": ROOT / "skills" / "search-state-corps" / "scripts" / "texas_comptroller.py",
    "opencorporates": ROOT / "skills" / "search-opencorporates" / "scripts" / "opencorporates_search.py",
}


def _load_target(target_path: Path) -> dict[str, Any]:
    """Load and validate target.yaml."""
    try:
        data = yaml.safe_load(target_path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError) as exc:
        logger.error("Cannot read target YAML: %s", exc)
        sys.exit(1)
    if "nome_completo" not in data:
        logger.error("target.yaml missing required field: nome_completo")
        sys.exit(1)
    return data


def _slug(name: str) -> str:
    """Produce a filesystem-safe slug from a full name.

    Only [a-z0-9-] characters are kept, preventing path traversal via
    names that contain '..' or other filesystem metacharacters.
    """
    raw = name.lower().replace(" ", "-").replace(".", "")[:40]
    slug = re.sub(r"[^a-z0-9\-]", "", raw)
    if not slug:
        raise ValueError(f"Invalid target name produces empty slug: {name!r}")
    return slug


def _run_script(script: Path, args: list[str]) -> subprocess.CompletedProcess:
    """Run a Python script as a subprocess and log stdout/stderr."""
    cmd = [sys.executable, str(script)] + args
    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            logger.debug("[stdout] %s", line)
    if result.returncode != 0:
        logger.error("[stderr] %s", result.stderr.strip())
    return result


def stage_expand_identity(
    target: dict[str, Any],
    output_dir: Path,
) -> Path:
    """Stage 2 — generate identity variations.

    Args:
        target: Parsed target YAML.
        output_dir: Case output directory.

    Returns:
        Path to identity-variations.json written.
    """
    logger.info("--- Stage 2: Expanding identity for '%s'", target["nome_completo"])
    out_path = output_dir / "identity-variations.json"

    relatives_arg = json.dumps(target.get("parentes", []), ensure_ascii=False)
    aliases = target.get("apelidos", [])
    alias_args: list[str] = []
    for a in aliases:
        alias_args += ["--alias", a]

    result = _run_script(
        _EXPAND_SCRIPT,
        [
            "--name", target["nome_completo"],
            "--relatives", relatives_arg,
            "--output", str(out_path),
            "--approved",
        ]
        + alias_args,
    )
    if result.returncode != 0:
        logger.error("expand_identity.py failed — check logs above")
        sys.exit(1)

    logger.info("Identity variations written to %s", out_path)
    return out_path


def stage_search(
    target: dict[str, Any],
    variations_path: Path,
    findings_dir: Path,
    skip_bases: list[str],
) -> None:
    """Stage 3 — run available search scripts in sequence.

    Scripts that are missing or fail are noted as gaps — the pipeline
    continues rather than aborting.

    Args:
        target: Parsed target YAML.
        variations_path: Path to identity-variations.json.
        findings_dir: Directory to write per-base findings JSON files.
        skip_bases: Bases to skip (e.g. when testing with pre-existing findings).
    """
    logger.info("--- Stage 3: Running search sub-skills")
    bases = target.get("bases_prioritarias", list(_SEARCH_SCRIPTS.keys()))
    findings_dir.mkdir(parents=True, exist_ok=True)

    for base in bases:
        if base in skip_bases:
            logger.info("Skipping %s (--skip-base flag)", base)
            continue
        script = _SEARCH_SCRIPTS.get(base)
        if not script or not script.exists():
            logger.warning(
                "No search script for base '%s' — will appear as gap in triangulation", base
            )
            continue

        out_file = findings_dir / f"{base.replace('-', '_')}.json"
        result = _run_script(
            script,
            [
                "--variations", str(variations_path),
                "--output", str(out_file),
            ],
        )
        if result.returncode != 0:
            logger.warning("Search script for %s returned non-zero — gap will be recorded", base)


def stage_triangulate(
    target: dict[str, Any],
    findings_dir: Path,
    output_dir: Path,
) -> Path:
    """Stage 4 — triangulate findings.

    Args:
        target: Parsed target YAML.
        findings_dir: Directory with per-base findings JSON files.
        output_dir: Case output directory.

    Returns:
        Path to findings.json (consolidated) written.
    """
    logger.info("--- Stage 4: Triangulating findings")
    consolidated_path = output_dir / "findings.json"

    result = _run_script(
        _TRIANGULATE_SCRIPT,
        [
            "--findings-dir", str(findings_dir),
            "--target-name", target["nome_completo"],
            "--output", str(consolidated_path),
        ],
    )
    if result.returncode != 0:
        logger.error("triangulate.py failed — check logs above")
        sys.exit(1)

    logger.info("Consolidated findings written to %s", consolidated_path)
    return consolidated_path


def stage_generate_pdf(
    consolidated_path: Path,
    target_path: Path,
    output_dir: Path,
) -> Path:
    """Stage 5 — generate dossier PDF.

    Args:
        consolidated_path: Path to findings.json consolidated.
        target_path: Path to target.yaml.
        output_dir: Case output directory.

    Returns:
        Path to dossier.pdf written.
    """
    logger.info("--- Stage 5: Generating dossier PDF")
    pdf_path = output_dir / "dossier.pdf"

    result = _run_script(
        _GENERATE_SCRIPT,
        [
            "--consolidated", str(consolidated_path),
            "--target", str(target_path),
            "--output", str(pdf_path),
        ],
    )
    if result.returncode != 0:
        logger.error("generate_report.py failed — check logs above")
        sys.exit(1)

    logger.info("Dossier PDF written to %s", pdf_path)
    return pdf_path


@click.command()
@click.option(
    "--target",
    "target_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to target.yaml",
)
@click.option(
    "--output-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Output directory (default: cases/<slug-do-alvo>/)",
)
@click.option(
    "--skip-search",
    is_flag=True,
    default=False,
    help="Skip Stage 3 (search) — use pre-existing findings in --findings-dir",
)
@click.option(
    "--findings-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Pre-existing findings directory (required when --skip-search is set)",
)
@click.option(
    "--skip-base",
    "skip_bases",
    multiple=True,
    help="Skip a specific base in Stage 3 (repeatable)",
)
@click.option(
    "--skip-pdf",
    is_flag=True,
    default=False,
    help="Skip Stage 5 (PDF generation) — produce only findings.json",
)
def main(
    target_path: Path,
    output_dir: Path | None,
    skip_search: bool,
    findings_dir: Path | None,
    skip_bases: tuple[str, ...],
    skip_pdf: bool,
) -> None:
    """Run the full due-diligence pipeline from target.yaml to dossier.pdf.

    The pipeline has 5 stages:
      1. Load target.yaml
      2. Expand Brazilian identity variations
      3. Run search sub-skills (one per database)
      4. Triangulate cross-base findings
      5. Generate PDF dossier

    Stages 2->3 and 4->5 have mandatory human review points in interactive
    mode (Claude Code). When running standalone, reviews are logged but
    not enforced — the journalist must validate outputs at each stage.
    """
    target = _load_target(target_path)
    logger.info("=== Due Diligence Pipeline: %s ===", target["nome_completo"])

    slug = _slug(target["nome_completo"])
    case_dir = output_dir or (ROOT / "cases" / slug)
    case_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Case output directory: %s", case_dir)

    # Stage 2 — expand identity
    variations_path = stage_expand_identity(target, case_dir)

    logger.info(
        "HUMAN REVIEW REQUIRED: check %s and confirm variations before proceeding.",
        variations_path,
    )

    # Stage 3 — search
    effective_findings_dir: Path
    if skip_search:
        if findings_dir is None:
            logger.error("--findings-dir required when --skip-search is set")
            sys.exit(1)
        effective_findings_dir = findings_dir
        logger.info("Skipping search — using findings from %s", effective_findings_dir)
    else:
        effective_findings_dir = case_dir / "findings"
        stage_search(target, variations_path, effective_findings_dir, list(skip_bases))

    # Stage 4 — triangulate
    consolidated_path = stage_triangulate(target, effective_findings_dir, case_dir)

    logger.info(
        "HUMAN REVIEW REQUIRED: check %s before generating PDF.", consolidated_path
    )

    # Stage 5 — generate PDF
    if skip_pdf:
        logger.info("Skipping PDF generation (--skip-pdf flag)")
    else:
        pdf_path = stage_generate_pdf(consolidated_path, target_path, case_dir)
        logger.info("=== Pipeline complete. Dossier: %s ===", pdf_path)


if __name__ == "__main__":
    main()
