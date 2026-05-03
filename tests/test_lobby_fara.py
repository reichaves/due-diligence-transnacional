"""
Tests for LDA, FARA and state-corps search scripts.

Strategy:
- Smoke tests via py_compile (syntax only) for all scripts.
- Unit tests via importlib.util (avoids hyphen-in-dirname import issue).
- Schema structure tests against findings.schema.json.
"""

from __future__ import annotations

import importlib.util
import json
import py_compile
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = ROOT / "schemas"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_module(relative_path: str) -> ModuleType:
    """Load a Python module from a path that may contain hyphens."""
    full_path = ROOT / relative_path
    module_name = full_path.stem  # e.g. "lda_search"
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    assert spec is not None, f"Could not create spec for {full_path}"
    assert spec.loader is not None, f"No loader for {full_path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Smoke tests — py_compile (syntax only)
# ---------------------------------------------------------------------------

SCRIPTS = [
    "skills/search-lobby-fara/scripts/lda_search.py",
    "skills/search-lobby-fara/scripts/fara_search.py",
    "skills/search-state-corps/scripts/florida_sunbiz.py",
    "skills/search-state-corps/scripts/delaware_corp.py",
    "skills/search-state-corps/scripts/texas_comptroller.py",
    "skills/search-opencorporates/scripts/opencorporates_search.py",
]


@pytest.mark.parametrize("script_path", SCRIPTS)
def test_script_syntax(script_path: str) -> None:
    """All M3 scripts must compile without syntax errors."""
    full_path = ROOT / script_path
    assert full_path.exists(), f"Script not found: {full_path}"
    py_compile.compile(str(full_path), doraise=True)


# ---------------------------------------------------------------------------
# Schema structure tests
# ---------------------------------------------------------------------------


class TestFindingsSchema:
    """Validate findings.schema.json structure and enums."""

    def test_schema_loads_as_valid_json(self) -> None:
        schema = _load_schema("findings.schema.json")
        assert isinstance(schema, dict)

    def test_required_top_level_fields(self) -> None:
        schema = _load_schema("findings.schema.json")
        required = schema.get("required", [])
        for field in ["base", "consulted_at", "queries_executed", "hits", "no_hits"]:
            assert field in required, f"'{field}' missing from required"

    def test_base_enum_has_all_registries(self) -> None:
        schema = _load_schema("findings.schema.json")
        base_enum = schema["properties"]["base"]["enum"]
        expected = [
            "FEC", "LDA", "FARA",
            "FL-SUNBIZ", "DE-CORPS", "TX-COMPTROLLER",
            "OPENCORPORATES", "NEWS-BR", "NEWS-US",
        ]
        for registry in expected:
            assert registry in base_enum, f"Missing registry '{registry}' in base enum"

    def test_confidence_enum_in_hit_items(self) -> None:
        schema = _load_schema("findings.schema.json")
        hit_schema = schema["properties"]["hits"]["items"]
        confidence_enum = hit_schema["properties"]["confidence"]["enum"]
        for level in ["confirmado", "provavel", "indicio", "nao-encontrado"]:
            assert level in confidence_enum, f"Missing confidence level '{level}'"

    def test_hit_items_have_required_fields(self) -> None:
        schema = _load_schema("findings.schema.json")
        hit_required = schema["properties"]["hits"]["items"].get("required", [])
        for field in ["variation_matched", "source_id", "confidence", "raw_record"]:
            assert field in hit_required, f"Hit required field '{field}' missing"

    def test_status_enum_present(self) -> None:
        schema = _load_schema("findings.schema.json")
        status_enum = schema["properties"]["status"]["enum"]
        assert "ok" in status_enum
        assert "error" in status_enum
        assert "partial" in status_enum


# ---------------------------------------------------------------------------
# LDA run_search output structure tests
# ---------------------------------------------------------------------------


class TestLdaRunSearch:
    """Unit tests for lda_search.run_search() output structure."""

    @pytest.fixture(scope="class")
    def lda_module(self) -> ModuleType:
        return _load_module("skills/search-lobby-fara/scripts/lda_search.py")

    def test_empty_result_required_keys(self, lda_module: ModuleType) -> None:
        with patch.object(lda_module, "_get_paginated", return_value=[]):
            with patch.object(lda_module, "_build_session", return_value=MagicMock()):
                result = lda_module.run_search(["Test Name"])
        for key in ["base", "consulted_at", "queries_executed", "hits", "no_hits", "legal_context"]:
            assert key in result, f"Missing key '{key}' in LDA result"

    def test_base_is_lda(self, lda_module: ModuleType) -> None:
        with patch.object(lda_module, "_get_paginated", return_value=[]):
            with patch.object(lda_module, "_build_session", return_value=MagicMock()):
                result = lda_module.run_search(["X"])
        assert result["base"] == "LDA"

    def test_no_hits_populated_when_empty(self, lda_module: ModuleType) -> None:
        variations = ["Carlos Ferreira", "C. Ferreira"]
        with patch.object(lda_module, "_get_paginated", return_value=[]):
            with patch.object(lda_module, "_build_session", return_value=MagicMock()):
                result = lda_module.run_search(variations)
        for v in variations:
            assert v in result["no_hits"]

    def test_hit_structure_with_mock_filing(self, lda_module: ModuleType) -> None:
        mock_filing = {
            "filing_uuid": "abc-123-def",
            "registrant": {"name": "Lobby Corp Inc"},
            "income": 75000,
            "dt_posted": "2024-06-01",
        }
        with patch.object(lda_module, "_get_paginated", side_effect=[[mock_filing], []]):
            with patch.object(lda_module, "_build_session", return_value=MagicMock()):
                result = lda_module.run_search(["Carlos Ferreira"])
        assert len(result["hits"]) == 1
        hit = result["hits"][0]
        assert hit["source_id"] == "abc-123-def"
        assert hit["variation_matched"] == "Carlos Ferreira"
        assert "source_url" in hit

    def test_legal_context_is_non_empty(self, lda_module: ModuleType) -> None:
        with patch.object(lda_module, "_get_paginated", return_value=[]):
            with patch.object(lda_module, "_build_session", return_value=MagicMock()):
                result = lda_module.run_search(["X"])
        assert len(result["legal_context"]) > 0


# ---------------------------------------------------------------------------
# FARA run_search output structure tests
# ---------------------------------------------------------------------------


class TestFaraRunSearch:
    """Unit tests for fara_search.run_search() output structure."""

    @pytest.fixture(scope="class")
    def fara_module(self) -> ModuleType:
        return _load_module("skills/search-lobby-fara/scripts/fara_search.py")

    def _run(
        self,
        fara_module: ModuleType,
        variations: list[str],
        registrants: list | None = None,
        principals: list | None = None,
    ) -> dict:
        with (
            patch.object(fara_module, "search_registrants", return_value=registrants or []),
            patch.object(fara_module, "search_foreign_principals", return_value=principals or []),
            patch.object(fara_module, "search_active_principals", return_value=[]),
            patch.object(fara_module, "_build_session", return_value=MagicMock()),
        ):
            return fara_module.run_search(variations)

    def test_base_is_fara(self, fara_module: ModuleType) -> None:
        result = self._run(fara_module, ["Test"])
        assert result["base"] == "FARA"

    def test_no_hits_populated_when_empty(self, fara_module: ModuleType) -> None:
        result = self._run(fara_module, ["Name A", "Name B"])
        assert "Name A" in result["no_hits"]
        assert "Name B" in result["no_hits"]

    def test_registrant_hit_source_id(self, fara_module: ModuleType) -> None:
        mock_registrant = {
            "Registration_Number": "5678",
            "Name": "FONTANA LLC",
            "Registration_Date": "2022-03-10",
        }
        result = self._run(fara_module, ["Fontana"], registrants=[mock_registrant])
        assert len(result["hits"]) > 0
        assert result["hits"][0]["source_id"] == "5678"

    def test_legal_context_mentions_fara_statute(self, fara_module: ModuleType) -> None:
        result = self._run(fara_module, ["Test"])
        combined = " ".join(result["legal_context"])
        assert "FARA" in combined or "22 U.S.C." in combined

    def test_methodology_note_non_empty(self, fara_module: ModuleType) -> None:
        result = self._run(fara_module, ["Test"])
        assert len(result.get("methodology_note", "")) > 20


# ---------------------------------------------------------------------------
# OpenCorporates run_search output structure tests
# ---------------------------------------------------------------------------


class TestOpenCorporatesRunSearch:
    """Unit tests for opencorporates_search.run_search() output structure."""

    @pytest.fixture(scope="class")
    def oc_module(self) -> ModuleType:
        return _load_module("skills/search-opencorporates/scripts/opencorporates_search.py")

    def test_base_is_opencorporates(self, oc_module: ModuleType) -> None:
        with patch.object(oc_module, "_search_officers", return_value=[]):
            with patch.object(oc_module, "_build_session", return_value=MagicMock()):
                result = oc_module.run_search(["Test"])
        assert result["base"] == "OPENCORPORATES"

    def test_offshore_flag_added_to_next_frontiers(self, oc_module: ModuleType) -> None:
        mock_officer = {
            "name": "CARLOS FERREIRA",
            "position": "director",
            "start_date": "2020-01-01",
            "end_date": None,
            "company": {
                "jurisdiction_code": "ky",  # Cayman Islands
                "company_number": "12345",
                "name": "CAYMAN HOLDING CO",
                "opencorporates_url": "https://opencorporates.com/companies/ky/12345",
            },
        }
        with patch.object(oc_module, "_search_officers", return_value=[mock_officer]):
            with patch.object(oc_module, "_build_session", return_value=MagicMock()):
                result = oc_module.run_search(["Carlos Ferreira"])

        frontiers_text = " ".join(result["next_frontiers"])
        assert "offshore" in frontiers_text.lower() or "ALERTA" in frontiers_text
