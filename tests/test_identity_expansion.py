"""
Tests for skills/expand-brazilian-identity/scripts/expand_identity.py

Covers:
- Unit tests for remove_diacritics(), parse_name_parts(), build_variations()
- Output structure via build_output()
- CLI smoke test via subprocess
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Resolve script path regardless of working directory
SCRIPT = (
    Path(__file__).parent.parent
    / "skills"
    / "expand-brazilian-identity"
    / "scripts"
    / "expand_identity.py"
)

# Add script directory to sys.path so we can import functions directly
sys.path.insert(0, str(SCRIPT.parent))
from expand_identity import (  # noqa: E402
    build_output,
    build_variations,
    parse_name_parts,
    remove_diacritics,
)


# ---------------------------------------------------------------------------
# remove_diacritics
# ---------------------------------------------------------------------------


class TestRemoveDiacritics:
    def test_portuguese_vowels(self):
        assert remove_diacritics("João") == "Joao"
        assert remove_diacritics("José") == "Jose"
        assert remove_diacritics("Ângelo") == "Angelo"

    def test_cedilla(self):
        assert remove_diacritics("Graça") == "Graca"
        assert remove_diacritics("França") == "Franca"

    def test_tilde_nasal(self):
        assert remove_diacritics("Ação") == "Acao"
        assert remove_diacritics("Leão") == "Leao"

    def test_plain_ascii_unchanged(self):
        assert remove_diacritics("Ricardo") == "Ricardo"
        assert remove_diacritics("Magro") == "Magro"

    def test_empty_string(self):
        assert remove_diacritics("") == ""


# ---------------------------------------------------------------------------
# parse_name_parts
# ---------------------------------------------------------------------------


class TestParseNameParts:
    def test_three_part_name(self):
        first, last, middles = parse_name_parts("Ricardo Andrade Magro")
        assert first == "Ricardo"
        assert last == "Magro"
        assert middles == ["Andrade"]

    def test_two_part_name(self):
        first, last, middles = parse_name_parts("Ricardo Magro")
        assert first == "Ricardo"
        assert last == "Magro"
        assert middles == []

    def test_single_word(self):
        first, last, middles = parse_name_parts("Ricardo")
        assert first == "Ricardo"
        assert last == ""
        assert middles == []

    def test_four_part_name(self):
        first, last, middles = parse_name_parts("Maria Jose da Silva")
        assert first == "Maria"
        assert last == "Silva"
        assert middles == ["Jose", "da"]

    def test_strips_whitespace(self):
        first, last, _ = parse_name_parts("  Ricardo Magro  ")
        assert first == "Ricardo"
        assert last == "Magro"


# ---------------------------------------------------------------------------
# build_variations
# ---------------------------------------------------------------------------


class TestBuildVariations:
    def test_minimum_count_three_part_name(self):
        """Three-part name should produce at least 6 distinct variations."""
        variations = build_variations("Ricardo Andrade Magro")
        assert len(variations) >= 6

    def test_always_contains_full_name(self):
        v = build_variations("Ricardo Andrade Magro")
        types = [x["type"] for x in v]
        assert "full_name" in types

    def test_always_contains_last_first(self):
        v = build_variations("Ricardo Andrade Magro")
        types = [x["type"] for x in v]
        assert "last_first" in types

    def test_always_contains_surname_only(self):
        v = build_variations("Ricardo Andrade Magro")
        types = [x["type"] for x in v]
        assert "surname_only" in types

    def test_no_accents_added_when_name_has_accents(self):
        v = build_variations("João Andrade Magro")
        types = [x["type"] for x in v]
        assert "no_accents" in types

    def test_no_accents_skipped_when_name_is_ascii(self):
        """If the name has no diacritics, no_accents variant must not appear."""
        v = build_variations("Ricardo Magro")
        types = [x["type"] for x in v]
        assert "no_accents" not in types

    def test_no_accents_value_correct(self):
        v = build_variations("João Andrade Magro")
        no_acc = [x for x in v if x["type"] == "no_accents"]
        assert len(no_acc) == 1
        assert no_acc[0]["variation"] == "Joao Andrade Magro"

    def test_surname_only_value(self):
        v = build_variations("Ricardo Andrade Magro")
        surname = [x for x in v if x["type"] == "surname_only"]
        assert len(surname) == 1
        assert surname[0]["variation"] == "Magro"

    def test_last_first_value(self):
        v = build_variations("Ricardo Andrade Magro")
        lf = [x for x in v if x["type"] == "last_first"]
        assert len(lf) == 1
        assert lf[0]["variation"] == "Magro Ricardo"

    def test_first_last_skipped_for_two_part_name(self):
        """For 'Ricardo Magro', first_last == no_accents == full_name — must not duplicate."""
        v = build_variations("Ricardo Magro")
        first_last = [x for x in v if x["type"] == "first_last"]
        # first+last IS the full name for two-part names, so it should be skipped
        assert len(first_last) == 0

    def test_alias_included(self):
        v = build_variations("Ricardo Magro", aliases=["Rick Magro"])
        alias_vars = [x for x in v if x["type"] == "alias"]
        assert len(alias_vars) == 1
        assert alias_vars[0]["variation"] == "Rick Magro"

    def test_multiple_aliases(self):
        v = build_variations("Ricardo Magro", aliases=["Rick Magro", "R. Magro Jr."])
        alias_vars = [x for x in v if x["type"] == "alias"]
        assert len(alias_vars) == 2

    def test_empty_alias_skipped(self):
        v = build_variations("Ricardo Magro", aliases=["", "   "])
        alias_vars = [x for x in v if x["type"] == "alias"]
        assert len(alias_vars) == 0

    def test_relative_included(self):
        relatives = [{"nome": "Ana Paula Magro", "relacao": "conjuge"}]
        v = build_variations("Ricardo Magro", relatives=relatives)
        rel_vars = [x for x in v if x["type"] == "relative"]
        assert len(rel_vars) >= 1
        rel_names = [x["variation"] for x in rel_vars]
        assert "Ana Paula Magro" in rel_names

    def test_relative_surname_also_included(self):
        relatives = [{"nome": "Ana Paula Magro", "relacao": "conjuge"}]
        v = build_variations("Ricardo Magro", relatives=relatives)
        rel_vars = [x for x in v if x["type"] == "relative"]
        rel_names = [x["variation"] for x in rel_vars]
        assert "Magro" in rel_names

    def test_relative_with_accented_name(self):
        relatives = [{"nome": "Cláudia Mário", "relacao": "conjuge"}]
        v = build_variations("Ricardo Magro", relatives=relatives)
        rel_vars = [x for x in v if x["type"] == "relative"]
        rel_names = [x["variation"] for x in rel_vars]
        assert "Claudia Mario" in rel_names

    def test_relative_missing_nome_skipped(self):
        relatives = [{"relacao": "conjuge"}]
        v = build_variations("Ricardo Magro", relatives=relatives)
        rel_vars = [x for x in v if x["type"] == "relative"]
        assert len(rel_vars) == 0

    def test_all_variations_have_required_keys(self):
        v = build_variations("Ricardo Andrade Magro")
        for item in v:
            assert "variation" in item
            assert "type" in item
            # note is optional but present in all generated items
            assert "note" in item

    def test_initials_last_present_for_three_part_name(self):
        v = build_variations("Ricardo Andrade Magro")
        types = [x["type"] for x in v]
        assert "initials_last" in types

    def test_initials_last_values(self):
        v = build_variations("Ricardo Andrade Magro")
        initials_vars = [x["variation"] for x in v if x["type"] == "initials_last"]
        assert "R. A. Magro" in initials_vars
        assert "R. Magro" in initials_vars


# ---------------------------------------------------------------------------
# build_output
# ---------------------------------------------------------------------------


class TestBuildOutput:
    def test_required_keys_present(self):
        v = build_variations("Ricardo Andrade Magro")
        out = build_output("Ricardo Andrade Magro", v)
        assert "target_name" in out
        assert "generated_at" in out
        assert "approved_by_human" in out
        assert "variations" in out

    def test_approved_false_by_default(self):
        v = build_variations("Ricardo Magro")
        out = build_output("Ricardo Magro", v)
        assert out["approved_by_human"] is False
        assert "approved_at" not in out

    def test_approved_true_sets_timestamp(self):
        v = build_variations("Ricardo Magro")
        out = build_output("Ricardo Magro", v, approved=True)
        assert out["approved_by_human"] is True
        assert "approved_at" in out

    def test_target_name_preserved(self):
        name = "João Andrade Magro"
        v = build_variations(name)
        out = build_output(name, v)
        assert out["target_name"] == name

    def test_generated_at_is_iso8601(self):
        from datetime import datetime

        v = build_variations("Ricardo Magro")
        out = build_output("Ricardo Magro", v)
        # Should parse without raising
        dt = datetime.fromisoformat(out["generated_at"])
        assert dt.tzinfo is not None  # must be timezone-aware


# ---------------------------------------------------------------------------
# CLI integration (subprocess)
# ---------------------------------------------------------------------------


class TestCLI:
    def test_basic_invocation_produces_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--name", "Ricardo Andrade Magro"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["target_name"] == "Ricardo Andrade Magro"

    def test_output_has_minimum_variations(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--name", "Ricardo Andrade Magro"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert len(data["variations"]) >= 6

    def test_cli_with_alias_flag(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--name",
                "Ricardo Magro",
                "--alias",
                "Rick Magro",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        alias_vars = [v for v in data["variations"] if v["type"] == "alias"]
        assert len(alias_vars) == 1
        assert alias_vars[0]["variation"] == "Rick Magro"

    def test_cli_with_relatives_json(self):
        relatives_json = '[{"nome": "Ana Magro", "relacao": "conjuge"}]'
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--name",
                "Ricardo Magro",
                "--relatives",
                relatives_json,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        rel_vars = [v for v in data["variations"] if v["type"] == "relative"]
        assert len(rel_vars) >= 1

    def test_cli_approved_flag(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--name",
                "Ricardo Magro",
                "--approved",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["approved_by_human"] is True

    def test_cli_invalid_relatives_json(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--name",
                "Ricardo Magro",
                "--relatives",
                "not-valid-json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_cli_output_file(self, tmp_path: Path):
        out_file = tmp_path / "variations.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--name",
                "Ricardo Magro",
                "--output",
                str(out_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["target_name"] == "Ricardo Magro"

    def test_cli_accentuated_name(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--name", "João Cláudio Leão"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        no_acc = [v for v in data["variations"] if v["type"] == "no_accents"]
        assert len(no_acc) == 1
        assert no_acc[0]["variation"] == "Joao Claudio Leao"
