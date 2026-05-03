---
name: search-opencorporates
description: >
  Busca global de empresas onde uma pessoa brasileira aparece como officer
  usando a API OpenCorporates. Cobre mais de 140 jurisdições, incluindo
  todos os 50 estados americanos, offshores (Cayman, BVI, Bermuda) e
  países da América Latina. Use quando o orquestrador
  `due-diligence-transnacional` solicitar, ou quando o usuário pedir
  "/consultar-base opencorporates NOME". Complementa a busca estadual
  com cobertura global.
---

# Busca OpenCorporates

## Inputs

- `identity-variations.json` (obrigatório)
- `jurisdiction_code` (opcional) — filtrar por jurisdição (ex: `"us_fl"`, `"ky"`, `"bm"`)
- `max_results_per_variation` (opcional) — default: 20

## Ferramentas disponíveis

- Script `scripts/opencorporates_search.py` — officer search na API OpenCorporates
- Chave de API: variável de ambiente `OPENCORPORATES_API_KEY`

## Endpoints usados

```
GET https://api.opencorporates.com/v0.4/officers/search
  ?q=<variação>
  &api_token=<OPENCORPORATES_API_KEY>
  &jurisdiction_code=<jurisdiction>   # opcional
  &per_page=20
```

Para cada empresa encontrada via officer search, opcionalmente:
```
GET https://api.opencorporates.com/v0.4/companies/<jurisdiction>/<company_number>
  ?api_token=<OPENCORPORATES_API_KEY>
```

## Procedimento

### 1. Officer search por variação de nome

Para cada variação em `identity-variations.json`:
- Executar officer search
- Registrar `position` (Director, Officer, Agent, etc.)
- Registrar `start_date` e `end_date` do cargo

### 2. Enriquecer com dados da empresa

Para cada empresa encontrada:
- `name`, `company_number`, `jurisdiction_code`
- `incorporation_date`, `dissolution_date`
- `company_type`, `current_status`
- URL canônica: `https://opencorporates.com/companies/<jurisdiction>/<company_number>`

### 3. Atenção especial a jurisdições offshore

Priorizar flags em hits com `jurisdiction_code` em:
- `ky` (Cayman Islands)
- `vg` (British Virgin Islands)
- `bm` (Bermuda)
- `pa` (Panama)
- `us_de` (Delaware — equivalente offshore americano)

Esses hits entram em `next_frontiers` com sugestão de verificar beneficial
ownership via FinCEN BOI (se empresa americana pós-2024) ou via ICIJ Offshore
Leaks Database.

## Output

`findings/opencorporates.json` conforme `schemas/findings.schema.json`.

Exemplo de hit:
```json
{
  "variation_matched": "Carlos Ferreira",
  "match_type": "exact",
  "source_id": "us_fl/P19000012345",
  "source_url": "https://opencorporates.com/companies/us_fl/P19000012345",
  "confidence": "provavel",
  "raw_record": {
    "officer_name": "CARLOS EDUARDO FERREIRA",
    "position": "director",
    "start_date": "2019-03-15",
    "end_date": null,
    "company_number": "P19000012345",
    "jurisdiction_code": "us_fl",
    "company_name": "FERREIRA GLOBAL ENERGY CORP"
  },
  "normalized": {
    "full_name": "CARLOS EDUARDO FERREIRA",
    "entity_name": "FERREIRA GLOBAL ENERGY CORP",
    "entity_type": "Corporation",
    "role": "director",
    "state": "FL",
    "date": "2019-03-15"
  }
}
```

## Rate limits e cota

- Plano free: 500 req/mês
- Plano pago: 10.000+ req/mês
- O script implementa rate limiting (1 req/s) e retries com exponential backoff.
- Se `OPENCORPORATES_API_KEY` não estiver definida, o script roda sem chave
  (limite muito menor) e registra aviso.

## Regras anti-alucinação

- `match_type: "fuzzy"` quando OpenCorporates retorna officer com nome similar
  mas não idêntico — frequente por diferenças de acentuação.
- Não afirmar que pessoa é **atual** officer se `end_date` estiver preenchido.
- Citar `company_number` e `jurisdiction_code` em todo hit.
- Se API retornar 429 (rate limit) ou 503, registrar `status: "partial"`.

## Referências

- Script: `scripts/opencorporates_search.py`
- OpenCorporates API docs: https://api.opencorporates.com/documentation/API-Reference
