"""
Tests for triangulate-findings script.

Strategy:
- Smoke test via py_compile (syntax only).
- Unit tests via importlib.util (avoids hyphen-in-dirname import issue).
- Tests cover: entity_match, address_match, person_match, date_match,
  gap detection, confidence scoring, and consolidation output shape.
"""

from __future__ import annotations

import importlib.util
import json
import py_compile
import sys
from datetime import date, timezone, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = ROOT / "schemas"
CASE_DIR = ROOT / "examples" / "case-fictional"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_module(relative_path: str) -> ModuleType:
    """Load a Python module from a path that may contain hyphens."""
    full_path = ROOT / relative_path
    module_name = full_path.stem
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    assert spec is not None, f"Could not create spec for {full_path}"
    assert spec.loader is not None, f"No loader for {full_path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def _make_finding(
    base: str,
    hits: list[dict] | None = None,
    no_hits: list[str] | None = None,
    status: str = "ok",
    queries: int = 5,
) -> dict[str, Any]:
    return {
        "base": base,
        "consulted_at": "2026-05-01T10:00:00+00:00",
        "queries_executed": queries,
        "status": status,
        "hits": hits or [],
        "no_hits": no_hits or ["Carlos Ferreira", "C. Ferreira"],
    }


def _make_hit(
    variation: str,
    source_id: str,
    confidence: str = "confirmado",
    entity_name: str = "",
    address: str = "",
    full_name: str = "",
    date_str: str = "",
) -> dict[str, Any]:
    return {
        "variation_matched": variation,
        "match_type": "exact",
        "source_id": source_id,
        "confidence": confidence,
        "raw_record": {"entity_name": entity_name, "address": address},
        "normalized": {
            "entity_name": entity_name,
            "address": address,
            "full_name": full_name,
            "date": date_str,
        },
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

SCRIPTS = [
    "skills/triangulate-findings/scripts/triangulate.py",
    "skills/generate-dossier-pdf/templates/dossier_template.py",
    "skills/generate-dossier-pdf/scripts/generate_report.py",
    "scripts/run_pipeline.py",
]


@pytest.mark.parametrize("script_path", SCRIPTS)
def test_syntax_ok(script_path: str) -> None:
    """All new M4 scripts must have valid Python syntax."""
    py_compile.compile(str(ROOT / script_path), doraise=True)


# ---------------------------------------------------------------------------
# Load the module under test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def tri() -> ModuleType:
    return _load_module("skills/triangulate-findings/scripts/triangulate.py")


# ---------------------------------------------------------------------------
# _normalize_entity
# ---------------------------------------------------------------------------

class TestNormalizeEntity:
    def test_strips_llc(self, tri: ModuleType) -> None:
        assert tri._normalize_entity("Fontana Energy Partners LLC") == "FONTANA ENERGY PARTNERS"

    def test_strips_inc(self, tri: ModuleType) -> None:
        assert tri._normalize_entity("BrightPath Inc") == "BRIGHTPATH"

    def test_empty(self, tri: ModuleType) -> None:
        assert tri._normalize_entity("") == ""

    def test_already_clean(self, tri: ModuleType) -> None:
        assert tri._normalize_entity("Fontana") == "FONTANA"


# ---------------------------------------------------------------------------
# _compute_confidence
# ---------------------------------------------------------------------------

class TestComputeConfidence:
    def test_three_primary_is_confirmado(self, tri: ModuleType) -> None:
        assert tri._compute_confidence(["FEC", "FL-SUNBIZ", "DE-CORPS"]) == "confirmado"

    def test_two_primary_is_provavel(self, tri: ModuleType) -> None:
        assert tri._compute_confidence(["FL-SUNBIZ", "DE-CORPS"]) == "provavel"

    def test_one_primary_one_news_is_indicio(self, tri: ModuleType) -> None:
        assert tri._compute_confidence(["FL-SUNBIZ", "NEWS-BR"]) == "indicio"

    def test_two_news_is_indicio(self, tri: ModuleType) -> None:
        assert tri._compute_confidence(["NEWS-BR", "NEWS-US"]) == "indicio"


# ---------------------------------------------------------------------------
# find_entity_matches
# ---------------------------------------------------------------------------

class TestEntityMatches:
    def test_same_entity_two_bases(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA ENERGY PARTNERS",
                "norm_address": "", "norm_name": "", "date_str": "",
                "raw_entity": "Fontana Energy Partners LLC",
                "raw_address": "", "raw_name": "",
            },
            {
                "base": "DE-CORPS", "source_id": "DE-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA ENERGY PARTNERS",
                "norm_address": "", "norm_name": "", "date_str": "",
                "raw_entity": "Fontana Energy Partners LLC",
                "raw_address": "", "raw_name": "",
            },
        ]
        result = tri.find_entity_matches(hits)
        assert len(result) == 1
        assert result[0]["type"] == "entity_match"
        assert set(result[0]["sources"]) == {"FL-SUNBIZ", "DE-CORPS"}
        assert result[0]["confidence"] == "provavel"

    def test_same_entity_one_base_no_match(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA",
                "norm_address": "", "norm_name": "", "date_str": "",
                "raw_entity": "Fontana LLC",
                "raw_address": "", "raw_name": "",
            }
        ]
        result = tri.find_entity_matches(hits)
        assert result == []

    def test_three_bases_is_confirmado(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": b, "source_id": b + "-001", "confidence_raw": "confirmado",
                "norm_entity": "ACME", "norm_address": "", "norm_name": "", "date_str": "",
                "raw_entity": "Acme LLC", "raw_address": "", "raw_name": "",
            }
            for b in ["FL-SUNBIZ", "DE-CORPS", "TX-COMPTROLLER"]
        ]
        result = tri.find_entity_matches(hits)
        assert result[0]["confidence"] == "confirmado"


# ---------------------------------------------------------------------------
# find_address_matches
# ---------------------------------------------------------------------------

class TestAddressMatches:
    def test_same_address_prefix_two_bases(self, tri: ModuleType) -> None:
        addr = "1200 brickell ave ste 500, miami, fl 33131"
        hits = [
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "", "norm_address": addr, "norm_name": "", "date_str": "",
                "raw_entity": "", "raw_address": "1200 Brickell Ave Ste 500, Miami, FL 33131",
                "raw_name": "",
            },
            {
                "base": "OPENCORPORATES", "source_id": "OC-001", "confidence_raw": "confirmado",
                "norm_entity": "", "norm_address": addr, "norm_name": "", "date_str": "",
                "raw_entity": "", "raw_address": "1200 Brickell Ave Ste 500, Miami, FL 33131",
                "raw_name": "",
            },
        ]
        result = tri.find_address_matches(hits)
        assert len(result) == 1
        assert result[0]["type"] == "address_match"

    def test_short_address_skipped(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "", "norm_address": "miami fl",  # < 20 chars
                "norm_name": "", "date_str": "",
                "raw_entity": "", "raw_address": "Miami FL", "raw_name": "",
            }
        ]
        result = tri.find_address_matches(hits)
        assert result == []


# ---------------------------------------------------------------------------
# find_person_matches
# ---------------------------------------------------------------------------

class TestPersonMatches:
    def test_same_person_two_bases(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "", "norm_address": "",
                "norm_name": "carlos eduardo fontana", "date_str": "",
                "raw_entity": "", "raw_address": "",
                "raw_name": "Carlos Eduardo Fontana",
            },
            {
                "base": "OPENCORPORATES", "source_id": "OC-001", "confidence_raw": "provavel",
                "norm_entity": "", "norm_address": "",
                "norm_name": "carlos eduardo fontana", "date_str": "",
                "raw_entity": "", "raw_address": "",
                "raw_name": "Carlos Eduardo Fontana",
            },
        ]
        result = tri.find_person_matches(hits)
        assert len(result) == 1
        assert result[0]["type"] == "person_match"

    def test_empty_name_skipped(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "", "norm_address": "", "norm_name": "",
                "date_str": "", "raw_entity": "", "raw_address": "", "raw_name": "",
            }
        ]
        result = tri.find_person_matches(hits)
        assert result == []


# ---------------------------------------------------------------------------
# find_date_matches
# ---------------------------------------------------------------------------

class TestDateMatches:
    def test_dates_within_30_days(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "DE-CORPS", "source_id": "DE-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA", "norm_address": "", "norm_name": "",
                "date_str": "2021-02-28",
                "raw_entity": "Fontana LLC", "raw_address": "", "raw_name": "",
            },
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA", "norm_address": "", "norm_name": "",
                "date_str": "2021-03-15",
                "raw_entity": "Fontana LLC", "raw_address": "", "raw_name": "",
            },
        ]
        result = tri.find_date_matches(hits)
        assert len(result) == 1
        diff = abs((date(2021, 3, 15) - date(2021, 2, 28)).days)
        assert diff == 15
        assert result[0]["type"] == "date_match"

    def test_dates_beyond_30_days_no_match(self, tri: ModuleType) -> None:
        hits = [
            {
                "base": "DE-CORPS", "source_id": "DE-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA", "norm_address": "", "norm_name": "",
                "date_str": "2021-01-01",
                "raw_entity": "Fontana LLC", "raw_address": "", "raw_name": "",
            },
            {
                "base": "FL-SUNBIZ", "source_id": "FL-001", "confidence_raw": "confirmado",
                "norm_entity": "FONTANA", "norm_address": "", "norm_name": "",
                "date_str": "2021-06-15",
                "raw_entity": "Fontana LLC", "raw_address": "", "raw_name": "",
            },
        ]
        result = tri.find_date_matches(hits)
        assert result == []


# ---------------------------------------------------------------------------
# identify_gaps
# ---------------------------------------------------------------------------

class TestIdentifyGaps:
    def test_error_finding_is_gap(self, tri: ModuleType) -> None:
        findings = [_make_finding("FEC", status="error")]
        gaps = tri.identify_gaps(findings, expected_bases=["FEC"])
        assert any(g["base"] == "FEC" and g["reason"] == "error" for g in gaps)

    def test_no_hits_is_gap(self, tri: ModuleType) -> None:
        findings = [_make_finding("FARA", hits=[], no_hits=["Carlos Ferreira"])]
        gaps = tri.identify_gaps(findings, expected_bases=["FARA"])
        assert any(g["base"] == "FARA" and g["reason"] == "no_hits" for g in gaps)

    def test_missing_expected_base_is_gap(self, tri: ModuleType) -> None:
        findings = [_make_finding("FEC")]
        gaps = tri.identify_gaps(findings, expected_bases=["FEC", "LDA"])
        assert any(g["base"] == "LDA" and g["reason"] == "not_searched" for g in gaps)

    def test_hit_finding_not_in_gaps(self, tri: ModuleType) -> None:
        hit = _make_hit("Carlos Fontana", "FL-001", entity_name="Fontana LLC")
        findings = [_make_finding("FL-SUNBIZ", hits=[hit])]
        gaps = tri.identify_gaps(findings, expected_bases=["FL-SUNBIZ"])
        assert not any(g["base"] == "FL-SUNBIZ" for g in gaps)


# ---------------------------------------------------------------------------
# triangulate (integration)
# ---------------------------------------------------------------------------

class TestTriangulate:
    def test_output_keys_present(self, tri: ModuleType) -> None:
        finding_a = _make_finding(
            "FL-SUNBIZ",
            hits=[_make_hit("Carlos Fontana", "FL-001", entity_name="Fontana LLC", address="1200 Brickell Ave Ste 500, Miami, FL 33131")],
        )
        finding_b = _make_finding(
            "DE-CORPS",
            hits=[_make_hit("Fontana", "DE-001", entity_name="Fontana LLC", date_str="2021-02-28")],
        )
        finding_c = _make_finding("FEC", hits=[], no_hits=["Carlos Fontana"])
        result = tri.triangulate([finding_a, finding_b, finding_c], "Carlos Fontana")
        assert result["target_name"] == "Carlos Fontana"
        assert "consolidated_at" in result
        assert "findings" in result
        assert "triangulations" in result
        assert "high_confidence_flags" in result
        assert "gaps" in result
        assert "legal_contexts" in result
        assert "next_frontiers" in result
        assert result["sources_count"] == 3

    def test_entity_match_detected(self, tri: ModuleType) -> None:
        f1 = _make_finding("FL-SUNBIZ", hits=[_make_hit("Fontana", "FL-001", entity_name="Fontana LLC")])
        f2 = _make_finding("DE-CORPS", hits=[_make_hit("Fontana", "DE-001", entity_name="Fontana LLC")])
        result = tri.triangulate([f1, f2], "Fontana")
        entity_matches = [t for t in result["triangulations"] if t["type"] == "entity_match"]
        assert len(entity_matches) >= 1

    def test_gap_for_no_hits(self, tri: ModuleType) -> None:
        f1 = _make_finding("FEC", hits=[], no_hits=["Carlos Fontana"])
        result = tri.triangulate([f1], "Carlos Fontana", expected_bases=["FEC"])
        assert any(g["reason"] == "no_hits" for g in result["gaps"])

    def test_empty_findings_raises(self, tri: ModuleType) -> None:
        # triangulate itself does not raise — gap list will be full
        result = tri.triangulate([], "Nobody", expected_bases=["FEC"])
        assert result["sources_count"] == 0
        assert len(result["gaps"]) > 0


# ---------------------------------------------------------------------------
# Integration with example fixtures
# ---------------------------------------------------------------------------

class TestFixtureIntegration:
    @pytest.mark.skipif(
        not (CASE_DIR / "findings").exists(),
        reason="case-fictional/findings/ not present",
    )
    def test_load_case_fictional_findings(self, tri: ModuleType) -> None:
        findings = tri.load_findings(CASE_DIR / "findings")
        assert len(findings) > 0
        for f in findings:
            assert "base" in f
            assert "hits" in f
            assert "no_hits" in f

    @pytest.mark.skipif(
        not (CASE_DIR / "findings").exists(),
        reason="case-fictional/findings/ not present",
    )
    def test_triangulate_case_fictional(self, tri: ModuleType) -> None:
        findings = tri.load_findings(CASE_DIR / "findings")
        result = tri.triangulate(findings, "Carlos Eduardo Fontana")
        assert result["target_name"] == "Carlos Eduardo Fontana"
        # Expect entity_match across FL-SUNBIZ, DE-CORPS, OPENCORPORATES, TX-COMPTROLLER
        entity_matches = [t for t in result["triangulations"] if t["type"] == "entity_match"]
        assert len(entity_matches) >= 1


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchemaPresent:
    def test_findings_consolidated_schema_valid(self) -> None:
        schema = _load_schema("findings-consolidated.schema.json")
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert "triangulations" in schema["properties"]
        assert "gaps" in schema["properties"]
        assert "findings" in schema["properties"]
