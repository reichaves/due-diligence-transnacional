# Security Model

This document describes what the `due-diligence-transnacional` pipeline does and does not do from a security and trust perspective. It is intended for:

- Journalists evaluating whether the tool is safe to run on their workstations
- Security reviewers using tools such as Skill Vetter or Socket
- Developers contributing to the project

---

## What this pipeline is

A **local CLI tool** — not a web application, not a server, not a daemon. It:

1. Reads a `target.yaml` file from disk
2. Calls public U.S. databases over HTTPS (fixed URL list)
3. Writes JSON findings to `cases/<slug>/`
4. Generates a PDF dossier

There is no listening port, no authentication server, no persistent process.

---

## Network access

The pipeline connects **only** to the following hardcoded hosts:

| Host | Purpose | Auth |
|------|---------|------|
| `api.open.fec.gov` | FEC campaign finance records | API key (optional — raises rate limit) |
| `efile.fara.gov` | FARA foreign agent registrations | None |
| `api.opencorporates.com` | Global corporate records | API key (optional) |
| `icijleaks.icij.org` | ICIJ Offshore Leaks (fallback) | None |
| `search.sunbiz.org` | Florida corporate registry | None |
| `icis.corp.delaware.gov` | Delaware corporate registry | None |
| `mycpa.cpa.state.tx.us` | Texas comptroller registry | None |

**No user-supplied URL is ever fetched.** The pipeline does not accept a URL parameter. A malicious `target.yaml` cannot redirect HTTP calls to an attacker-controlled host (no SSRF vector).

All calls use:
- `requests.Session()` with `timeout=30`
- Default SSL verification (`verify=True` — never disabled)
- Standard User-Agent rotation (for scraping scripts)

---

## Filesystem access

### Writes

All output files are written inside the **case output directory**, which is derived from the target name via `_slug()`:

```
cases/<slug>/
├── identity-variations.json
├── findings/
│   └── *.json
├── findings-consolidated.json
└── dossier.pdf
```

The `_slug()` function (in `scripts/run_pipeline.py`) enforces that the slug:
- Contains only `[a-z0-9-]`
- Strips all dots, slashes, backslashes, and Unicode characters
- Raises `ValueError` if the sanitised result is empty

A `target.yaml` with `nome_completo: "../../../etc/passwd"` will raise an error rather than write outside `cases/`.

### Reads

The pipeline reads:
- The `target.yaml` file specified by `--target`
- The existing findings JSON files in `--findings-dir` (if `--skip-search` is used)
- No other paths are read from user input

---

## Process execution

All sub-scripts are invoked via `subprocess.run()` with:

- **`shell=False`** (default) — arguments are passed as a Python list, not a shell string
- `[sys.executable, str(script_path)] + args` — the interpreter is always the current Python binary
- User-controlled values (name, aliases) are passed as **positional arguments to `click`**, not interpolated into a shell command

There is no `os.system()`, no `eval()`, no `exec()` in the pipeline source code. Verified by `tests/test_security.py::TestNoShellTrue`.

---

## Serialisation

| Format | Library | Safe pattern used |
|--------|---------|-------------------|
| YAML | `pyyaml` | `yaml.safe_load()` — never bare `yaml.load()` |
| JSON | `json` (stdlib) | `json.loads()` / `json.dumps()` |
| PDF | `reportlab` | All cell content wrapped in `_cell()` → `xml.sax.saxutils.escape()` before rendering |

No `pickle` is used anywhere in the pipeline.

---

## Secret management

| Secret | Where stored | Committed? |
|--------|-------------|-----------|
| `FEC_API_KEY` | `.env` (gitignored) | No |
| `OPENCORPORATES_API_KEY` | `.env` (gitignored) | No |
| MCP server config | `.mcp.json` (gitignored) | No |

**Rule:** All secrets are loaded via `os.getenv()` or `python-dotenv`. No key is ever hardcoded in source. Verified by `tests/test_security.py::TestNoHardcodedKeys`.

### Why `.mcp.json` is gitignored

The MCP server configuration file (`.mcp.json`) passes the `FEC_API_KEY` to the local `fec-mcp` server process. Because this file contains user-specific credentials and local file paths, it must **never** be committed. It is listed in `.gitignore`.

If you are setting up a new environment, copy `.env.example` to `.env` and fill in your keys. The MCP server will pick up `FEC_API_KEY` from the environment variable automatically via the `${FEC_API_KEY}` reference in `.mcp.json`.

---

## Skills trust signal (for Skill Vetter / Socket reviewers)

The `.claude/commands/` slash commands in this repository:

- **Do not execute shell commands directly** — they delegate to Python sub-scripts via Claude sub-agents
- **Do not request elevated filesystem permissions** — all writes go to `cases/<slug>/` inside the project directory
- **Do not access arbitrary URLs** — network calls are limited to the hardcoded host list above
- **Do not store or transmit PII** — findings are written locally; no telemetry or analytics
- **Do not use `eval`, `exec`, or `pickle`** — verified by static analysis tests
- **Use `yaml.safe_load` exclusively** — no unsafe deserialisation

The skills listed in `skills/*/SKILL.md` follow the same constraints. Each skill is a standalone Python script that:
1. Accepts arguments via `click`
2. Calls one external HTTPS endpoint (from the fixed list)
3. Writes a structured JSON findings file to the path provided by `--output`

---

## Safe usage checklist

Before running the pipeline on sensitive cases:

- [ ] Copy `.env.example` to `.env` and fill in your API keys
- [ ] Verify `.env` is in `.gitignore` (it is, but double-check if you forked the repo)
- [ ] Never commit `.mcp.json` — it may contain local key values
- [ ] Investigate only persons of public relevance (see `docs/ethics.md`)
- [ ] Review `identity-variations.json` before running searches (`approved_by_human: true`)
- [ ] Keep `cases/` output local — never push investigation outputs to GitHub
- [ ] Rotate your FEC/OpenCorporates keys if you suspect they were exposed

---

## Known limitations

- The pipeline does not validate the **authenticity** of findings (it trusts that the APIs returned correct data)
- `cases/` findings JSONs are not encrypted at rest — protect the directory on shared machines
- The PDF dossier is not digitally signed — source citations must be independently verifiable

---

## Automated security tests

Run `pytest tests/test_security.py -v` to verify:

1. `_slug()` rejects path-traversal names
2. No hardcoded API keys in source files
3. No `subprocess.run(..., shell=True)` calls
4. All subprocess commands use list arguments
5. `yaml.safe_load` only (no bare `yaml.load`)
6. `target.yaml` schema validation is enforced at pipeline entry
