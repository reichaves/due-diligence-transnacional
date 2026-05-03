# MCP Tool Detection — search-fec

Before executing a FEC search, check which execution mode is available in the
current Claude Code session. Use the highest level available.

---

## Level 1 — fec-mcp (preferred)

If the tool `mcp__fec-mcp__search_contributions` is listed as available in this
session, use it. It queries the FEC API directly and returns structured JSON.

Example call:

```
mcp__fec-mcp__search_contributions(contributor_name="Carlos Eduardo Ferreira")
mcp__fec-mcp__search_contributions(contributor_name="Ferreira Carlos")
```

Other fec-mcp tools available at Level 1:

| Tool | Purpose |
|------|---------|
| `mcp__fec-mcp__search_contributions` | Busca doações por nome de doador (Schedule A) |
| `mcp__fec-mcp__get_candidate_finances` | Finanças de candidato específico |
| `mcp__fec-mcp__get_top_donors` | Maiores doadores de um comitê |
| `mcp__fec-mcp__search_candidates` | Buscar candidatos por nome |
| `mcp__fec-mcp__search_pacs` | Buscar PACs e Super PACs |
| `mcp__fec-mcp__get_contributions_by_state` | Doações filtradas por estado |
| `mcp__fec-mcp__get_independent_expenditures` | Gastos independentes |
| `mcp__fec-mcp__get_campaign_filings` | Relatórios de campanha |
| `mcp__fec-mcp__get_campaign_expenditures` | Gastos de campanha |

Installation: see `docs/setup.md` → "Ferramentas opcionais (MCP)"

---

## Level 2 — osint-investigation MCP

If `mcp__fec-mcp__*` tools are NOT available but `mcp__osint-investigation__*`
tools are listed in the session, use them for broader open-source intelligence
gathering around the target name (web search, document search, public records).

osint-investigation does not provide structured FEC data — it is a fallback for
general open-source research that may surface press mentions of FEC activity.

---

## Level 3 — Fallback (Python script)

If neither MCP server is available, execute via Bash:

```bash
python skills/search-fec/scripts/fec_search.py \
  --variations identity-variations.json \
  --output findings/fec.json
```

When operating at Level 3, inform the user:

> "fec-mcp-server não detectado nesta sessão. A busca está sendo executada via
> script Python com a API pública da FEC. Para melhor cobertura e desempenho,
> instale o fec-mcp-server: https://github.com/reichaves/fec-mcp-server"

---

## How to detect which level is active

Claude Code automatically lists available MCP tools at session start. To check:

1. If you can call `mcp__fec-mcp__search_contributions` → Level 1
2. If you can call `mcp__osint-investigation__*` → Level 2
3. Otherwise → Level 3

Do not attempt Level 1 calls and fall back silently — always log which level
was used in the `methodology_note` field of `findings/fec.json`.

Example methodology_note values:

- Level 1: `"Busca executada via MCP fec-mcp (mcp__fec-mcp__search_contributions). Cobre todas as eleições com registros digitalizados (1980–presente)."`
- Level 2: `"Busca executada via MCP osint-investigation (fallback). Resultado menos estruturado que Level 1."`
- Level 3: `"Busca executada via script Python fec_search.py com API pública FEC. fec-mcp-server não disponível nesta sessão."`
