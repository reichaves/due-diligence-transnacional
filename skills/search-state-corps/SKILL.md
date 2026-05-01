---
name: search-state-corps
description: >
  Busca empresas onde uma pessoa brasileira aparece como officer, registered
  agent ou governing person em registros corporativos estaduais americanos
  (Florida/Sunbiz, Delaware/Division of Corporations, Texas/Secretary of
  State). Use quando o orquestrador `due-diligence-transnacional` solicitar,
  ou quando o usuário pedir "/consultar-base state-corps NOME". Retorna JSON
  com entidades encontradas, estados cobertos e limitações conhecidas de cada
  registro.
---

# Busca em Registros Corporativos Estaduais

## Estados cobertos (por padrão)

| Estado    | Base                              | URL base                          |
|-----------|-----------------------------------|-----------------------------------|
| Florida   | Sunbiz (Division of Corporations) | https://search.sunbiz.org/        |
| Delaware  | Division of Corporations (DoC)    | https://icis.corp.delaware.gov/   |
| Texas     | Secretary of State                | https://www.sos.state.tx.us/      |

## Inputs

- `identity-variations.json` (obrigatório)
- `states` (opcional) — lista de estados a pesquisar (default: `["FL", "DE", "TX"]`)

## Ferramentas disponíveis

- `scripts/florida_sunbiz.py` — Sunbiz officer search
- `scripts/delaware_corp.py` — Delaware entity search
- `scripts/texas_comptroller.py` — Texas SOS entity search
- Web search como fallback e verificação

## Procedimento por estado

### Florida — Sunbiz

Endpoint público: `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults`

Para cada variação de nome:
1. Buscar como **officer/registered agent** (tipo: `OfficerDirector`)
2. Buscar como **entidade** (tipo: `EntityName`) — captura empresas com nome similar

Campos a registrar:
- `document_number` → `source_id`
- `entity_name`
- `entity_type` (Corporation, LLC, LP, etc.)
- `principal_address`
- `mailing_address`
- `registered_agent_name`
- `status` (Active, Inactive)
- `date_filed`
- `officer_name` e `officer_title` (quando o alvo é officer)
- URL: `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquiryType=EntityName&inquiryDirectionType=ForwardList&searchNameOrder=<entity_name>&aggregateId=<document_number>`

### Delaware

Endpoint: `https://icis.corp.delaware.gov/Ecorp/EntitySearch/NameSearch.aspx`

**Atenção:** Delaware protege informações de officers/beneficial owners por design.
O registro retorna apenas: nome da entidade, tipo, data de incorporação,
status, e agente registrado (que geralmente é escritório de advogado).

Campos a registrar:
- `entity_number` → `source_id`
- `entity_name`
- `entity_type`
- `incorporation_date`
- `status`
- `registered_agent` (geralmente Corporation Trust Company ou similar)
- URL: `https://icis.corp.delaware.gov/Ecorp/EntitySearch/NameSearch.aspx`

Registrar em `methodology_note`:
"Delaware não divulga officers, diretores ou beneficial owners publicamente.
Registro de existência de empresa NÃO implica relação com o alvo — apenas
confirma que a entidade existe. Para identificar relação, consultar Sunbiz
(FL) cross-reference, FARA, ou documentos judiciais."

### Texas

Endpoint: `https://mycpa.cpa.state.tx.us/coa/`

Para cada variação:
1. Buscar entidade por nome de officer (`/search/name`)
2. Buscar entidade por nome da empresa

Campos a registrar:
- `taxpayer_number` → `source_id`
- `taxpayer_name` (entity name)
- `mailing_address`
- `city`, `state`, `zip`
- `status`
- `right_to_transact`
- URL: `https://mycpa.cpa.state.tx.us/coa/`

## Output

`findings/state-corps.json` com hits separados por estado, conforme
`schemas/findings.schema.json`.

Adicionar campo extra em `hits[].normalized`:
```json
{
  "state_registry": "FL",
  "entity_name": "REFIT ENERGY CORP",
  "entity_type": "CORPORATION",
  "role": "OFFICER - President",
  "status": "ACTIVE",
  "date": "2019-03-15"
}
```

## Regras anti-alucinação

- Delaware: NUNCA afirmar que o alvo é owner/officer de empresa DE apenas
  por encontrar empresa com nome similar — ausência de dados de officers é
  característica do sistema, não ausência de informação.
- Registrar `match_type: "fuzzy"` quando nome da entidade contém o sobrenome
  mas não é idêntico ao alvo.
- Se Sunbiz retornar timeout, registrar `status: "partial"` para FL.

## Referências

- `references/state-registries-guide.md` — guia completo das diferenças entre estados
- Scripts: `scripts/florida_sunbiz.py`, `scripts/delaware_corp.py`, `scripts/texas_comptroller.py`
