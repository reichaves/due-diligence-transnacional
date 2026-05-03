"""
Purpose: Automated security regression tests for the due-diligence-transnacional pipeline.
Author:  Reinaldo Chaves <reichaves@gmail.com>
Date:    2026-05-03
Dependencies: pytest, ast (stdlib)

Tests cover:
  - Path traversal prevention in _slug()
  - Absence of hardcoded API keys in source files
  - Absence of subprocess shell=True in all scripts
  - subprocess commands passed as lists (not strings)
  - yaml.safe_load used exclusively (never bare yaml.load)
  - target.yaml required fields validated before pipeline use
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT / "scripts"
SKILLS_DIR = ROOT / "skills"


# ---------------------------------------------------------------------------
# Helper: load _slug() from run_pipeline.py without running the full module
# ---------------------------------------------------------------------------

def _load_slug_fn():
    spec = importlib.util.spec_from_file_location(
        "run_pipeline", SCRIPTS_DIR / "run_pipeline.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Stub heavy imports so we can load the module in isolation
    sys.modules.setdefault("click", type(sys)("click"))
    sys.modules.setdefault("yaml", type(sys)("yaml"))
    try:
        spec.loader.exec_module(mod)
    except Exception:
        pass
    return mod._slug  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 1. Path traversal prevention
# ---------------------------------------------------------------------------

class TestSlugPathTraversal:
    """_slug() must produce a safe filesystem component with no path separators."""

    @pytest.fixture(scope="class")
    def slug(self):
        return _load_slug_fn()

    def test_normal_name_produces_slug(self, slug):
        result = slug("João da Silva")
        assert result == "joo-da-silva"

    def test_dot_dot_stripped(self, slug):
        """Names with '..' must not produce path-traversal slugs."""
        result = slug("../../../etc/passwd")
        # All dots and slashes removed; only a-z0-9- remain
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result

    def test_forward_slash_stripped(self, slug):
        result = slug("name/with/slashes")
        assert "/" not in result

    def test_backslash_stripped(self, slug):
        result = slug("name\\with\\backslashes")
        assert "\\" not in result

    def test_empty_after_stripping_raises(self, slug):
        """A name that reduces to empty after sanitising must raise ValueError."""
        with pytest.raises(ValueError, match="empty slug"):
            slug("../../../")

    def test_slug_max_40_chars(self, slug):
        long_name = "a" * 100
        assert len(slug(long_name)) <= 40

    def test_slug_only_safe_chars(self, slug):
        result = slug("Müller & Associates, LLC!")
        assert re.match(r"^[a-z0-9\-]+$", result), f"Unsafe chars in slug: {result!r}"


# ---------------------------------------------------------------------------
# 2. No hardcoded API keys in Python source files
# ---------------------------------------------------------------------------

# Pattern: long alphanumeric strings that look like API keys (30+ chars)
_KEY_PATTERN = re.compile(r"[A-Za-z0-9]{30,}")
# Allowlist: known-safe long strings in source (base64 test fixtures, etc.)
_ALLOWLISTED_FILES = {
    "test_security.py",  # this file itself
}
# Files where keys are explicitly loaded from env (not hardcoded)
_ENV_LOAD_PATTERN = re.compile(r"os\.getenv|os\.environ|load_dotenv|\$\{")


def _collect_python_sources() -> list[Path]:
    sources = list(SCRIPTS_DIR.glob("*.py"))
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            sources.extend((skill_dir / "scripts").glob("*.py") if (skill_dir / "scripts").exists() else [])
    return [p for p in sources if p.name not in _ALLOWLISTED_FILES]


class TestNoHardcodedKeys:
    def test_no_hardcoded_api_keys_in_source(self):
        """No Python source file should contain a bare 30+ char alphanumeric literal
        that looks like an API key (i.e., not loaded from environment)."""
        violations: list[str] = []
        for path in _collect_python_sources():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in _KEY_PATTERN.finditer(text):
                token = match.group()
                line_no = text[: match.start()].count("\n") + 1
                line = text.splitlines()[line_no - 1]
                # Skip if it's inside an env-load expression or a comment
                if _ENV_LOAD_PATTERN.search(line):
                    continue
                if line.strip().startswith("#"):
                    continue
                # Skip common false positives: URLs, hashes in test data
                if "http" in line or "sha" in line.lower():
                    continue
                violations.append(f"{path.relative_to(ROOT)}:{line_no}: {token[:20]}...")
        assert not violations, (
            "Possible hardcoded API keys found:\n" + "\n".join(violations)
        )

    def test_mcp_json_key_is_env_ref(self):
        """`.mcp.json` must use ${VAR} references, not literal key values."""
        mcp_path = ROOT / ".mcp.json"
        if not mcp_path.exists():
            pytest.skip(".mcp.json not present")
        content = mcp_path.read_text(encoding="utf-8")
        # Any value that is a 30+ char alphanum and NOT a ${VAR} ref is a violation
        bare_keys = re.findall(r'"[A-Za-z0-9]{30,}"', content)
        assert not bare_keys, (
            f".mcp.json contains what looks like bare API keys: {bare_keys}. "
            "Use ${VAR_NAME} references instead."
        )


# ---------------------------------------------------------------------------
# 3. No subprocess shell=True
# ---------------------------------------------------------------------------

def _ast_find_shell_true(path: Path) -> list[int]:
    """Return line numbers where subprocess.run/Popen is called with shell=True."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                violations.append(node.lineno)
    return violations


class TestNoShellTrue:
    def test_no_shell_true_in_pipeline_scripts(self):
        violations: list[str] = []
        for path in _collect_python_sources():
            lines = _ast_find_shell_true(path)
            for ln in lines:
                violations.append(f"{path.relative_to(ROOT)}:{ln}")
        assert not violations, (
            "subprocess call with shell=True found (injection risk):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 4. subprocess commands are lists, not strings
# ---------------------------------------------------------------------------

def _ast_find_subprocess_string_cmd(path: Path) -> list[int]:
    """Return line numbers where subprocess.run/Popen is called with a string (not list) as first arg."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Check if it's a subprocess call
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        if func_name not in ("run", "Popen", "call", "check_call", "check_output"):
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        # If first arg is a plain string constant → unsafe
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            violations.append(node.lineno)
        # f-string as first arg → unsafe
        if isinstance(first_arg, ast.JoinedStr):
            violations.append(node.lineno)
    return violations


class TestSubprocessArgLists:
    def test_subprocess_commands_are_lists(self):
        violations: list[str] = []
        for path in _collect_python_sources():
            lines = _ast_find_subprocess_string_cmd(path)
            for ln in lines:
                violations.append(f"{path.relative_to(ROOT)}:{ln}")
        assert not violations, (
            "subprocess called with string command (use a list instead):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 5. yaml.safe_load only — no bare yaml.load
# ---------------------------------------------------------------------------

class TestYamlSafeLoad:
    def test_no_bare_yaml_load_in_source(self):
        """yaml.load() without an explicit Loader is a deserialization risk.
        Only yaml.safe_load() or yaml.load(x, Loader=yaml.SafeLoader) are allowed."""
        violations: list[str] = []
        pattern = re.compile(r"\byaml\.load\s*\(")
        safe_pattern = re.compile(r"yaml\.safe_load|Loader\s*=")
        for path in _collect_python_sources():
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, line in enumerate(lines, 1):
                if pattern.search(line) and not safe_pattern.search(line):
                    violations.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()}")
        assert not violations, (
            "Unsafe yaml.load() detected (use yaml.safe_load instead):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 6. target.yaml schema — required fields present
# ---------------------------------------------------------------------------

class TestTargetYamlSchema:
    """The load_target helper must enforce required fields."""

    def test_load_target_requires_nome_completo(self, tmp_path):
        """target.yaml without 'nome_completo' must cause the pipeline to exit."""
        import subprocess as sp

        bad_yaml = tmp_path / "target.yaml"
        bad_yaml.write_text("razao_investigativa: test\n", encoding="utf-8")
        result = sp.run(
            [sys.executable, str(SCRIPTS_DIR / "run_pipeline.py"), "--target", str(bad_yaml)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Pipeline should exit non-zero for missing nome_completo"
        assert "nome_completo" in result.stderr or "nome_completo" in result.stdout

    def test_load_target_requires_razao_investigativa(self, tmp_path):
        """target.yaml without 'razao_investigativa' may still work (not always required),
        but 'nome_completo' is mandatory — verify the check is active."""
        import subprocess as sp

        good_yaml = tmp_path / "target.yaml"
        good_yaml.write_text(
            "nome_completo: Test Name\nrazao_investigativa: investigação de teste\n",
            encoding="utf-8",
        )
        # Pipeline will fail later (missing scripts/env), but it must NOT fail on schema
        result = sp.run(
            [sys.executable, str(SCRIPTS_DIR / "run_pipeline.py"), "--target", str(good_yaml)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Accept any return code — we only check that schema validation passed
        assert "missing required field: nome_completo" not in result.stderr
