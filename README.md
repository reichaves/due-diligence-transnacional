# Due Diligence Transnacional

[![GitHub](https://img.shields.io/badge/GitHub-reichaves-181717?logo=github)](https://github.com/reichaves/due-diligence-transnacional)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-D4A017)](https://claude.ai/code)
[![License](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)
[![OpenFEC](https://img.shields.io/badge/API-OpenFEC-dc2626)](https://api.open.fec.gov/developers/)
[![Tests](https://img.shields.io/badge/Tests-99%20passing-22c55e)](tests/)

> A CLI pipeline for investigative journalists to cross-reference **any name with U.S. ties** against U.S. public databases — producing a source-cited, confidence-scored PDF dossier. Optimized for Brazilian and Latin American names; works for any origin country.

**Author:** [Reinaldo Chaves](https://github.com/reichaves) — data journalist in Brazil · reichaves@gmail.com · [LinkedIn](https://br.linkedin.com/in/reinaldochaves)

> **Note:** All examples in this repository use fictional names and companies created for illustrative purposes only. Any resemblance to real persons or organizations is coincidental.

---

## ⚠️ Important Notice — Read Before Using

> **AI-generated research from public data sources.**
> This project is available at https://github.com/reichaves/due-diligence-transnacional

**This tool is for journalistic use only.** It is designed exclusively for data journalism and public-interest transparency. Any other use is the sole responsibility of the user.

**All data must be verified.** Every item in the dossier was produced by AI models based on publicly available data. All information must be verified against original source documents before publication or any other use.

**Presumption of innocence.** Evidence of potential misconduct requires further investigation with additional sources and documents. **The fact that a person or company appears in this dossier does not imply guilt or wrongdoing.**

**Beware of homonyms.** Always verify that the person or company found is indeed the intended research subject. Common names produce false positives. Cross-reference with additional identifiers (city, employer, birth year) before drawing conclusions.

**No guarantee of completeness.** Public data sources may contain errors, outdated information, or omissions. We are not responsible for defects or inaccuracies in public data sources.

**The user bears sole responsibility** for the correct use of the information produced by this pipeline.

---

## What it does

Given a target name and context, the pipeline:

1. Expands the name into search variations (transliterations, initials, inverted order, relatives)
2. Runs parallel searches across U.S. public databases:
   - **FEC** — Federal Election Commission donations (Schedule A)
   - **LDA** — Lobbying Disclosure Act registrations
   - **FARA** — Foreign Agents Registration Act
   - **State corporate registries** — Florida (Sunbiz), Delaware, Texas
   - **OpenCorporates** — global corporate database
   - **Press archive** — Brazilian and U.S. news sources
3. Triangulates findings (address matches, date overlaps, shared associates)
4. Produces a structured PDF dossier with explicit sources and confidence levels
5. Prints a mandatory disclaimer to the terminal after each run

Every claim in the dossier has a source citation. "Not found" is also a finding — methodology is always documented.

The dossier PDF includes a prominent **Legal and Ethical Notice** section (section 8) that must be read before the document is shared or published.

## What it does NOT do

- No access to paid databases (Lexis, Sayari, Refinitiv)
- No facial recognition or visual OSINT (use a separate OSINT skill for that) - Check it out at https://github.com/reichaves/osint-investigation
- No scheduled/automated runs — investigations are one-off and directed
- Does not replace the reporter: the pipeline delivers structured leads; editorial interpretation stays with the journalist

---

## Prerequisites

| Component | Minimum version | Check |
|-----------|----------------|-------|
| Python | 3.11 | `python --version` |
| Claude Code | any | `claude --version` |
| Git | any | `git --version` |

Claude Code requires a **Claude Max subscription** or an **Anthropic API key**. See [claude.ai/code](https://claude.ai/code) to get started.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/reichaves/due-diligence-transnacional.git
cd due-diligence-transnacional
```

### 2. Create a virtual environment and install dependencies

**With uv (recommended):**

```bash
pip install uv
uv sync
```

**With pip:**

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e .
```

Installed packages: `click`, `pyyaml`, `requests`, `beautifulsoup4`, `reportlab`, `pydantic`, `jsonschema`, `python-dotenv`.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys (see [API Keys](#api-keys) section below).

### 4. Configure the fec-mcp MCP server (recommended)

The pipeline uses the [`fec-mcp`](https://github.com/reichaves/fec-mcp-server) MCP server for structured FEC queries. The configuration is already present in `.mcp.json` at the repository root:

```json
{
  "mcpServers": {
    "fec-mcp": {
      "command": "uvx",
      "args": ["fec-mcp"]
    }
  }
}
```

Install `uvx` if not already available:

```bash
pip install uv
```

Without the MCP server, the pipeline falls back to a Python script that calls the FEC public API directly — coverage is equivalent but slower and less structured.

### 5. Open Claude Code inside the project directory

The slash commands are registered via files in `.claude/commands/` — Claude Code loads them automatically when you open it inside the project directory:

```bash
cd due-diligence-transnacional
claude
```

Claude Code loads `CLAUDE.md` and all commands in `.claude/commands/` on startup. No manual registration needed.

> **Troubleshooting:** If you get `Unknown skill: investigar` (or any other command), make sure you opened Claude Code from **inside** the `due-diligence-transnacional` directory. Commands are project-scoped and only available when Claude Code is running in the correct working directory.

### 6. Validate the installation

Run the test suite:

```bash
pytest tests/ -v
```

Expected output: `99 passed`.

Optionally, run the fictional example end-to-end to confirm PDF generation works:

```bash
python scripts/run_pipeline.py \
    --target examples/case-fictional/target.yaml \
    --skip-search \
    --findings-dir examples/case-fictional/findings/ \
    --output-dir /tmp/test-output/
```

Expected: a `dossier.pdf` in `/tmp/test-output/` with 10 sections, including the Legal and Ethical Notice section.

---

## API Keys

### Required

| Key | Purpose | Where to obtain |
|-----|---------|----------------|
| `FEC_API_KEY` | FEC public database queries (higher rate limits) | [api.data.gov/signup](https://api.open.fec.gov/developers/) — free, arrives in minutes |
| `OPENCORPORATES_API_KEY` | Global corporate registry searches | [opencorporates.com/api_accounts/new](https://opencorporates.com/api_accounts/new) — free tier: 50 req/day; journalist plan: free for credentialed outlets |

### Optional

| Key | Purpose |
|-----|---------|
| `ANTHROPIC_API_KEY` | Direct Anthropic API access (if not using Claude Code with a Max subscription) |
| `LOG_LEVEL` | Controls logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) — default: `INFO` |

> The FEC API works without a key (rate-limited to 1,000 req/day), but registering for a free key raises the limit to 1,000 req/hour.

Copy `.env.example` to `.env` and fill in your values. The `.env` file is git-ignored and must never be committed.

---

## Usage

All commands are available inside Claude Code when run from the project directory. Each command has a Portuguese version and an English version — they are fully equivalent.

### Mode 1 — Full pipeline (recommended)

```
/investigar "Carlos Eduardo Ferreira"    # Portuguese
/investigate "Carlos Eduardo Ferreira"   # English
```

Claude will:

1. Load `CLAUDE.md` and activate the `due-diligence-transnacional` skill
2. Ask for additional context (occupation, city, known relatives)
3. Generate name variations and request your approval
4. Launch parallel searches across all configured databases (sub-agents)
5. Show consolidated findings for your review
6. Generate the final PDF dossier

Human review checkpoints are mandatory at stages 2→3 and 4→5.

### Mode 2 — Single database query

```
/consultar-base fec "Carlos Ferreira"    # Portuguese
/search-database fec "Carlos Ferreira"   # English
```

Useful when you only need to check one specific database.

Available databases: `fec`, `lda`, `fara`, `fl` (Florida), `de` (Delaware), `tx` (Texas), `oc` (OpenCorporates), `news-br`, `news-us`.

### Mode 3 — Name expansion only

```
/expandir-nome "Carlos Eduardo Ferreira"   # Portuguese
/expand-name "Carlos Eduardo Ferreira"     # English
```

Generates name variations without running any searches. Useful to review the variation set before a full investigation.

### Mode 4 — Generate dossier from existing findings

```
/gerar-dossie cases/ferreira/findings-consolidated.json    # Portuguese
/generate-dossier cases/ferreira/findings-consolidated.json  # English
```

Generates the PDF from a pre-existing consolidated findings file. Use this to re-generate the dossier after manually editing findings.

### Mode 5 — Standalone Python (no Claude Code required)

```bash
python scripts/run_pipeline.py --target examples/case-fictional/target.yaml
```

Each sub-skill also exposes its own script, callable independently:

```bash
# Corporate registry search (Florida)
python skills/search-state-corps/scripts/florida_sunbiz.py \
    --variations identity-variations.json \
    --output findings/fl_sunbiz.json

# Triangulate findings
python skills/triangulate-findings/scripts/triangulate.py \
    --findings-dir findings/ \
    --output findings-consolidated.json

# Generate PDF dossier in Portuguese (default)
python skills/generate-dossier-pdf/scripts/generate_report.py \
    --consolidated findings-consolidated.json \
    --target target.yaml \
    --output dossier.pdf \
    --lang pt-BR

# Generate PDF dossier in English
python skills/generate-dossier-pdf/scripts/generate_report.py \
    --consolidated findings-consolidated.json \
    --target target.yaml \
    --output dossier-en.pdf \
    --lang en-US
```

### Bilingual PDF output

The dossier PDF can be generated in **Portuguese** (`pt-BR`) or **English** (`en-US`). The language controls all section headings, table headers, confidence-level labels, the disclaimer text, and the terminal notice.

Language precedence (highest to lowest):
1. `--lang` flag on the CLI
2. `investigation_language` field in `target.yaml`
3. Default: `pt-BR`

### Using in English / non-Latin American targets

The pipeline works for **any journalist** investigating **any person with U.S. ties** — regardless of the journalist's own country or the target's origin. A U.S. journalist investigating a Nigerian businessman with a Delaware company, a European reporter tracking a Chinese investor through Florida real estate, or an Argentine journalist following a compatriot's lobbying activity can all use this pipeline.

Set `investigation_language: en-US` and `origin_country` in your `target.yaml`:

> **Coverage note for non-Latin names:** The name-expansion algorithm handles accent removal and order inversions for any name. For transliteration patterns specific to Chinese, Arabic, Nigerian, or other non-Latin names, the coverage is lower than for Latin names — review the generated variations carefully before running searches.

```yaml
nome_completo: "Pablo Vargas Mendoza"
ocupacao: "General Manager"
empresa_principal: "Vargas Energy USA LLC"
origin_country: "PE"
investigation_language: "en-US"
razao_investigativa: >
  Pablo Vargas Mendoza is general manager of Vargas Energy USA LLC, a US
  subsidiary of a Peruvian oil company.
bases_prioritarias:
  - fec
  - lda-fara
  - state-corps
  - opencorporates
  - news
```

Then run with the English command:

```
/investigate "Pablo Vargas Mendoza"
```

See `examples/case-vargas-fictional/` for a complete walkthrough with a Peruvian target.

---

## Command reference

| Portuguese | English | Description |
|---|---|---|
| `/investigar "Name"` | `/investigate "Name"` | Full 5-stage pipeline |
| `/consultar-base <db> "Name"` | `/search-database <db> "Name"` | Single database query |
| `/expandir-nome "Name"` | `/expand-name "Name"` | Name variation expansion only |
| `/gerar-dossie <findings.json>` | `/generate-dossier <findings.json>` | PDF generation from existing findings |

---

## PDF dossier structure

Each generated dossier contains 10 sections:

| # | Section | Content |
|---|---------|---------|
| Cover | Cover + metadata | Target name, date, database count, hit count |
| 1 | Executive Summary | High-confidence flags, pipeline statistics |
| 2 | Methodology | Databases queried, query counts, methodology notes |
| 3 | Identity Variations | All name variations searched |
| 4 | Findings by Database | Per-database results with source citations and confidence levels |
| 5 | Triangulations | Cross-database matches (address, date, associate overlaps) |
| 6 | Gaps and Next Steps | Documented gaps, suggested follow-up actions |
| 7 | Applicable Legal Context | Relevant U.S. legal frameworks (§ 30121, FARA, OFAC, etc.) |
| **8** | **Legal and Ethical Notice** | **Mandatory disclaimer — must be read before sharing the document** |
| App. | Appendix | Query timestamps for all databases |

The Legal and Ethical Notice (section 8) is displayed prominently with a colored border. It is also printed to the terminal after every PDF generation.

---

## Project structure

```
due-diligence-transnacional/
├── CLAUDE.md                      # Project instructions loaded by Claude on startup
├── pyproject.toml                 # Python package metadata and dependencies
├── .env.example                   # Environment variable template
├── .mcp.json                      # MCP server configuration (fec-mcp)
│
├── .claude/                       # Claude Code project configuration
│   ├── settings.json              # MCP server enable list
│   └── commands/                  # Slash commands — loaded automatically on startup
│       ├── investigar.md          # /investigar — full pipeline (Portuguese)
│       ├── investigate.md         # /investigate — full pipeline (English)
│       ├── consultar-base.md      # /consultar-base — single database query (Portuguese)
│       ├── search-database.md     # /search-database — single database query (English)
│       ├── expandir-nome.md       # /expandir-nome — name expansion (Portuguese)
│       ├── expand-name.md         # /expand-name — name expansion (English)
│       ├── gerar-dossie.md        # /gerar-dossie — PDF generation (Portuguese)
│       └── generate-dossier.md    # /generate-dossier — PDF generation (English)
│
├── skills/                        # Skill definitions referenced by CLAUDE.md
│   ├── due-diligence-transnacional/   # Main orchestrator skill
│   │   ├── SKILL.md               # Orchestration logic, MCP detection, pipeline stages
│   │   └── references/
│   │       ├── confidence-levels.md   # Confidence scale: confirmed/probable/indication/not-found
│   │       ├── ethical-guardrails.md  # When to refuse an investigation
│   │       └── methodology.md         # Research methodology documentation
│   │
│   ├── expand-brazilian-identity/ # Name variation generator (works for any nationality)
│   │   ├── SKILL.md
│   │   ├── references/transliteration-patterns.md
│   │   └── scripts/expand_identity.py
│   │
│   ├── search-fec/                # FEC donation search
│   │   ├── SKILL.md               # 3-level execution: fec-mcp → osint → Python script
│   │   └── references/
│   │       ├── fec-fields-guide.md
│   │       ├── legal-context-30121.md
│   │       └── mcp-detection.md
│   │
│   ├── search-lobby-fara/         # LDA + FARA search
│   │   ├── SKILL.md
│   │   ├── references/lda-fara-explainer.md
│   │   ├── scripts/lda_search.py
│   │   └── scripts/fara_search.py
│   │
│   ├── search-state-corps/        # State corporate registry search (FL, DE, TX)
│   │   ├── SKILL.md
│   │   ├── references/state-registries-guide.md
│   │   ├── scripts/florida_sunbiz.py
│   │   ├── scripts/delaware_corp.py
│   │   └── scripts/texas_comptroller.py
│   │
│   ├── search-opencorporates/     # OpenCorporates global search
│   │   ├── SKILL.md
│   │   └── scripts/opencorporates_search.py
│   │
│   ├── search-news-archive/       # Press archive (BR + US media + generic web)
│   │   ├── SKILL.md
│   │   └── references/trusted-outlets.md
│   │
│   ├── triangulate-findings/      # Cross-reference all findings
│   │   ├── SKILL.md
│   │   └── scripts/triangulate.py
│   │
│   └── generate-dossier-pdf/      # PDF dossier generator
│       ├── SKILL.md
│       ├── scripts/generate_report.py   # --lang pt-BR | en-US; bilingual output
│       └── templates/dossier_template.py
│
├── schemas/                       # JSON Schema validation (Draft 2020-12)
│   ├── target.schema.json
│   ├── identity-variations.schema.json
│   ├── findings.schema.json
│   ├── findings-consolidated.schema.json
│   └── confidence-levels.schema.json
│
├── docs/                          # Reference documentation
│   ├── setup.md
│   ├── methodology.md
│   ├── legal-context.md
│   ├── data-sources.md
│   ├── ethics.md
│   └── limitations.md
│
├── examples/                      # End-to-end examples with pre-generated findings
│   ├── target-template.yaml
│   ├── case-fictional/
│   ├── case-brazil-fictional/
│   └── case-vargas-fictional/     # Non-Brazilian target — demonstrates i18n support
│
├── tests/                         # Automated tests (pytest) — 99 passing
│   ├── test_identity_expansion.py
│   ├── test_triangulation.py
│   ├── test_lobby_fara.py
│   └── fixtures/sample_fec_response.json
│
└── scripts/
    └── run_pipeline.py            # Standalone CLI — runs the full pipeline without Claude Code
```

---

## Optional MCP servers

The pipeline auto-detects and uses these MCP servers when available. Without them, Python scripts are used as fallback — equivalent coverage, but slower.

### fec-mcp (recommended for FEC searches)

Provides `mcp__fec-mcp__*` tools for structured, direct access to the FEC API.

Repository: [github.com/reichaves/fec-mcp-server](https://github.com/reichaves/fec-mcp-server)

```bash
pip install uv
uvx fec-mcp --help   # test the installation
```

Already configured in `.mcp.json`. When active, the `search-fec` skill operates at **Level 1** (direct structured API) instead of the Python script fallback.

### osint-investigation

Provides `mcp__osint-investigation__*` tools for open-source intelligence gathering. Used as secondary fallback when `fec-mcp` is unavailable.

To confirm which level is active, run:

```
/search-database fec "Carlos Eduardo Ferreira"
```

If the output says `Level 1 — fec-mcp`, the MCP server is active. If it says `Level 3 — Python script`, the server was not detected.

---

## Known limitations

See `docs/limitations.md` for the full list. Summary:

- Brazilian name transliteration is imperfect (Ferreira vs. Ferreirra vs. C. Ferreira) — mitigated but not eliminated
- State corporate registries vary in quality and coverage
- FARA has multi-month delays between registration and public availability
- Delaware corporations reveal minimal public information — the sub-skill returns existence, not ultimate beneficial owner
- Florida Sunbiz blocks automated queries (HTTP 403) — manual verification required
- OpenCorporates free API key is rate-limited (50 req/day); journalist plan available

---

## Ethics

This pipeline is designed for investigating **persons of public relevance**: executives with government contracts, political donors, foreign agents, individuals involved in reported crimes or human rights violations. Do not use it to investigate private individuals. Full guidelines in `docs/ethics.md`.

---

## Citation

If this pipeline contributes to a published story or research, please cite:

> Chaves, R. (2026). *Due Diligence Transnacional: CLI pipeline for cross-referencing names with U.S. ties in American public databases*. https://github.com/reichaves/due-diligence-transnacional

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Author

**Reinaldo Chaves**
Data journalist in Brazil
[github.com/reichaves](https://github.com/reichaves) · [LinkedIn](https://br.linkedin.com/in/reinaldochaves) · reichaves@gmail.com
