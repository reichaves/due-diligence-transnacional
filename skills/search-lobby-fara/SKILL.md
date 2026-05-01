---
name: search-lobby-fara
description: >
  Busca registros de lobby (LDA — Lobbying Disclosure Act) e de agentes
  estrangeiros (FARA — Foreign Agents Registration Act) para um conjunto
  de variações de nome de pessoa brasileira. Use quando o orquestrador
  `due-diligence-transnacional` solicitar, ou quando o usuário pedir
  "/consultar-base lda NOME" ou "/consultar-base fara NOME". Retorna
  JSON estruturado com filings encontrados, variações testadas e contexto
  legal de ambas as leis.
---

# Busca Lobby (LDA) e Agente Estrangeiro (FARA)

## Inputs

- `identity-variations.json` (obrigatório)
- `base_filter` (opcional) — `"lda"`, `"fara"`, ou `"both"` (default: `"both"`)
- `year_start` (opcional) — ano inicial para filtrar filings (ex: 2015)

## Ferramentas disponíveis

- Script `scripts/lda_search.py` — busca no Senate LDA Disclosure Database
- Script `scripts/fara_search.py` — busca no eFile FARA (DOJ)
- Web search como fallback para verificação cruzada

## O que são LDA e FARA

Ver `references/lda-fara-explainer.md` para detalhes completos.

**Resumo:**
- **LDA** (2 U.S.C. § 1601 et seq.) — Registra lobbistas que fazem contato com
  funcionários do Congresso ou do Executivo em nome de cliente. Inclui pessoa
  física (lobbista) e organização cliente. Limite: pessoa deve ter ≥ 20% do
  tempo gasto em lobby E receber ≥ USD 3.000/trimestre.
- **FARA** (22 U.S.C. § 611 et seq.) — Registra agentes que atuam em nome de
  entidade ou governo estrangeiro em atividades políticas ou de relações públicas
  nos EUA. Mais amplo que LDA — inclui mídia, relações públicas, consultoria.

## Procedimento

### LDA — Senate Disclosure Database

Base: `https://lda.senate.gov/api/v1/`

Para cada variação de nome:
1. Buscar como **lobbyist**: `GET /lobbyists/?name=<variação>`
2. Buscar como **client**: `GET /clients/?name=<variação>`
3. Buscar em **filings**: `GET /filings/?lobbyist_name=<variação>`

Para cada filing encontrado, registrar:
- `filing_uuid` → `source_id`
- `registrant_name` (empresa de lobby)
- `client_name`
- `lobbyist_name` (lista de lobbistas)
- `period_of_performance` (período)
- `income` (valor recebido em USD)
- `expenses` (gastos declarados)
- `general_issue_area_code` e `description`
- `filing_type` e `dt_posted`
- URL: `https://lda.senate.gov/filings/public/filing/<filing_uuid>/print/`

### FARA — eFile FARA (DOJ)

Base: `https://efile.fara.gov/`

Para cada variação de nome:
1. Buscar registrantes: `GET /api/v1/Registrant/json/?name=<variação>`
2. Buscar em exhibits: busca textual via `GET /api/v1/Exhibit-AB/json/?name=<variação>`

Para cada registro FARA encontrado, registrar:
- `registration_number` → `source_id`
- `registrant_name`
- `foreign_principal` (quem é o principal estrangeiro)
- `foreign_principal_country`
- `registration_date`
- `termination_date` (se encerrado)
- `activity_description`
- URL: `https://efile.fara.gov/docs/<registration_number>/`

### Atraso de disponibilização FARA

Registrar em `methodology_note`: "FARA pode ter atraso de 30-90 dias entre
a data do registro e a disponibilização pública no sistema eFile. Busca manual
em registros físicos (pre-2008) pode ser necessária para casos mais antigos."

## Output

`findings/lda.json` e `findings/fara.json` (ou combinados como
`findings/lobby-fara.json`) conforme `schemas/findings.schema.json`.

## Regras anti-alucinação

- Citar `filing_uuid` (LDA) ou `registration_number` (FARA) em todo hit.
- Se a API retornar timeout ou erro 500, registrar `status: "partial"` —
  não inferir ausência de registros.
- Diferenciar: pessoa como **lobbista** vs. pessoa como **cliente**.
- FARA tem cobertura digital limitada pré-2008 — registrar essa limitação.

## Referências

- `references/lda-fara-explainer.md` — contexto legal detalhado
- Scripts: `scripts/lda_search.py`, `scripts/fara_search.py`
