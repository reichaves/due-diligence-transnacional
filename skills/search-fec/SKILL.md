---
name: search-fec
description: >
  Busca contribuições eleitorais federais americanas (Schedule A da FEC)
  para um conjunto de variações de nome de pessoa brasileira. Use quando
  o orquestrador `due-diligence-transnacional` solicitar, ou quando o
  usuário pedir explicitamente "/consultar-base fec NOME". Retorna JSON
  estruturado com hits, no-hits e contexto legal aplicável (52 U.S.C. § 30121).
---

# Busca FEC — Federal Election Commission

## Inputs

- `identity-variations.json` (obrigatório) — lista de variações de nome gerada pela skill `expand-brazilian-identity`
- `state_filter` (opcional) — UF americana para filtrar (ex: "FL", "TX")
- `min_date` (opcional) — data mínima ISO YYYY-MM-DD (default: sem limite)
- `max_date` (opcional) — data máxima ISO YYYY-MM-DD (default: sem limite)

## Modo de execução

Esta skill opera em 3 níveis, em ordem de preferência. Use sempre o nível mais
alto disponível na sessão atual e registre qual foi usado em `methodology_note`.

### Nível 1 — fec-mcp (preferido)

Se `mcp__fec-mcp__search_contributions` estiver disponível nesta sessão, use-o.
Retorna JSON estruturado diretamente da API FEC.

```
mcp__fec-mcp__search_contributions(contributor_name="Carlos Eduardo Ferreira")
```

Outras ferramentas fec-mcp disponíveis no Nível 1:
`mcp__fec-mcp__get_top_donors`, `mcp__fec-mcp__search_candidates`,
`mcp__fec-mcp__search_pacs`, `mcp__fec-mcp__get_contributions_by_state`,
`mcp__fec-mcp__get_independent_expenditures`, `mcp__fec-mcp__get_campaign_filings`.

### Nível 2 — osint-investigation MCP

Se fec-mcp não estiver disponível mas `mcp__osint-investigation__*` estiver,
use-o para pesquisa de fontes abertas em torno do nome do alvo. Não retorna
dados FEC estruturados — é um fallback para menções na imprensa ou registros públicos.

### Nível 3 — Script Python (fallback)

Se nenhum MCP estiver disponível, execute via Bash:

```bash
python skills/search-fec/scripts/fec_search.py \
  --variations identity-variations.json \
  --output findings/fec.json
```

Informe o usuário que o fec-mcp-server não foi detectado e que instalá-lo melhora
a cobertura. Instruções em `docs/setup.md` → "Ferramentas opcionais (MCP)".

Vide `references/mcp-detection.md` para lógica de detecção detalhada.

## Ferramentas disponíveis (Nível 1)

- `mcp__fec-mcp__search_contributions` — busca por nome de doador (Schedule A)
- `mcp__fec-mcp__get_candidate_finances` — finanças de candidato
- `mcp__fec-mcp__get_top_donors` — maiores doadores de um comitê
- `mcp__fec-mcp__search_candidates` — buscar candidatos por nome
- `mcp__fec-mcp__search_pacs` — buscar PACs e Super PACs
- `mcp__fec-mcp__get_contributions_by_state` — doações filtradas por estado
- `mcp__fec-mcp__get_independent_expenditures` — gastos independentes

## Procedimento passo a passo

### 1. Validar input

Verificar que `identity-variations.json` está presente e válido.
Extrair lista de variações do campo `variations[].name_string`.

### 2. Executar queries

Para cada variação em `identity-variations.json`:

```
fec-finance:search_contributions(contributor_name=<variação>)
```

Quando `state_filter` for fornecido, repetir com `contributor_state=<UF>`.

Registrar número total de queries executadas.

### 3. Processar hits

Para cada contribuição retornada, registrar:

| Campo FEC                     | Campo no hit JSON                |
|-------------------------------|----------------------------------|
| `contributor_name`            | `raw_record.contributor_name`    |
| `contributor_employer`        | `raw_record.contributor_employer`|
| `contributor_occupation`      | `raw_record.contributor_occupation`|
| `contributor_city`            | `raw_record.contributor_city`    |
| `contributor_state`           | `raw_record.contributor_state`   |
| `contribution_receipt_date`   | `raw_record.date`                |
| `contribution_receipt_amount` | `raw_record.amount_usd`          |
| `committee_id`                | `raw_record.committee_id`        |
| `committee_name`              | `raw_record.committee_name`      |
| `transaction_id`              | `source_id`                      |

URL canônica: `https://www.fec.gov/data/receipts/?two_year_transaction_period=XXXX&transaction_id=<transaction_id>`

### 4. Diferenciar match exato de fuzzy

A FEC retorna resultados por similaridade além dos exatos.
Registrar `match_type`:
- `"exact"` — nome retornado é igual à string buscada (case-insensitive)
- `"fuzzy"` — nome retornado difere da string buscada

### 5. Registrar no-hits

Quando NENHUMA variação retornar hit, registrar explicitamente em
`no_hits` com a lista completa das variações testadas.

Quando ALGUMA variação retornar hit mas outras não, as sem resultado
também entram em `no_hits`.

### 6. Incluir contexto legal obrigatório

Sempre incluir em `legal_context`:

```
"52 U.S.C. § 30121 proíbe nacionais estrangeiros (que não sejam green
card holders) de fazer contribuições ou gastos em eleições federais,
estaduais ou locais americanas. Ausência de hits em FEC para cidadão
brasileiro sem residência permanente nos EUA é o resultado esperado e
legalmente coerente — não é um achado negativo em si."
```

## Output

`findings/fec.json` conforme `schemas/findings.schema.json`.

**Exemplo de output sem hits (resultado esperado para brasileiro sem green card):**

```json
{
  "base": "FEC",
  "consulted_at": "2026-04-30T14:30:00-03:00",
  "queries_executed": 8,
  "status": "ok",
  "hits": [],
  "no_hits": [
    "Carlos Eduardo Ferreira",
    "Carlos Ferreira",
    "Ferreira Carlos",
    "C. Ferreira",
    "C.E. Ferreira",
    "Ricardo Andrade",
    "Ferreira",
    "Ricardo A Ferreira"
  ],
  "legal_context": [
    "52 U.S.C. § 30121 proíbe nacionais estrangeiros de fazer contribuições em eleições americanas. Ausência de hits é resultado esperado para cidadão brasileiro sem residência permanente nos EUA."
  ],
  "next_frontiers": [
    "Verificar se o alvo possui green card ou cidadania americana — se sim, doação seria legal e a ausência de registro seria significativa",
    "Verificar 501(c)(4)s e dark money groups, que aceitam doações de estrangeiros e não exigem disclosure público",
    "Verificar PACs estaduais em Florida e Texas (regras estaduais diferem da federal)"
  ],
  "methodology_note": "Busca executada no endpoint /schedules/schedule_a/ da API FEC via MCP fec-finance. Cobre todas as eleições com registros digitalizados (1980–presente). Nomes testados case-insensitive."
}
```

## Regras anti-alucinação

- NUNCA afirme que alguém doou sem `transaction_id` confirmado.
- SEMPRE relate as variações testadas, mesmo quando encontrou em apenas uma.
- NUNCA infira identidade por similaridade de nome sem registrar `match_type: "fuzzy"`.
- Se a API retornar erro, registrar `status: "error"` e mensagem — nunca inventar ausência de resultado.

## Referências

- `references/fec-fields-guide.md` — guia dos campos do Schedule A
- `references/legal-context-30121.md` — texto da lei e exceções
- `references/mcp-detection.md` — lógica de detecção MCP (Níveis 1–3)
