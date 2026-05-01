---
name: triangulate-findings
description: >
  Cruza achados de múltiplas bases (FEC, LDA, FARA, registros estaduais,
  OpenCorporates, imprensa) em busca de coincidências de endereço, data de
  incorporação, entidades e pessoas vinculadas. Eleva o nível de confiança
  quando ≥2 fontes primárias concordam. Produz findings-consolidated.json
  para uso pela skill generate-dossier-pdf. Acionar quando o orquestrador
  due-diligence-transnacional completar o Estágio 3 (buscas em paralelo).
---

# Triangulação de Achados

## Quando ativar

- Depois que todas (ou a maioria das) sub-skills de busca retornaram seus
  `findings/<base>.json`.
- Quando o orquestrador chama o Estágio 4 do pipeline.
- Quando o usuário pedir: "cruza os achados", "consolida os resultados".

## Inputs

- Diretório `findings/` com um ou mais arquivos `<base>.json` validados
  contra `schemas/findings.schema.json`.
- (Opcional) `identity-variations.json` — para listar todas as variações
  testadas no apêndice.

## Lógica de cruzamento

### 1. Índice de endereços

Extrai `normalized.address` de cada hit. Se o mesmo endereço (ou prefixo
de 15 caracteres) aparecer em bases diferentes, cria uma triangulação do
tipo `address_match`.

### 2. Índice de entidades

Extrai `normalized.entity_name` de cada hit. Correspondência case-insensitive
e strip de sufixos comuns (LLC, Inc, Corp, Ltd). Se a mesma entidade aparecer
em ≥2 bases, cria `entity_match`.

### 3. Índice de pessoas

Extrai `normalized.full_name` de cada hit. Mesma lógica de normalização.
Cria `person_match` quando a mesma pessoa aparece em bases distintas.

### 4. Índice de datas

Extrai `normalized.date` de cada hit. Se datas de incorporação em bases
diferentes diferem em ≤30 dias para a mesma entidade, cria `date_match`.

## Escala de confiança na triangulação

| Fontes concordantes | Confiança       |
|---------------------|-----------------|
| ≥ 3 bases primárias | `confirmado`    |
| 2 bases primárias   | `provavel`      |
| 1 primária + 1 news | `indicio`       |
| 1 base apenas       | não triangulado |

Bases primárias: FEC, LDA, FARA, FL-SUNBIZ, DE-CORPS, TX-COMPTROLLER,
OPENCORPORATES. NEWS-BR e NEWS-US são corroborativas, não primárias.

## Identificação de lacunas

Uma lacuna é registrada quando:
- Uma base esperada (listada em `bases_prioritarias` do target.yaml) não
  tem arquivo de achados, ou
- O arquivo existe mas `status = "error"`, ou
- Todas as variações estão em `no_hits` (ausência documentada).

Lacunas são dados jornalísticos — sempre registrar com a metodologia
executada, não apenas omitir.

## Output

`findings-consolidated.json` validado contra
`schemas/findings-consolidated.schema.json`.

Estrutura:
```json
{
  "target_name": "...",
  "consolidated_at": "ISO-8601",
  "sources_count": 5,
  "findings": [ /* array de findings individuais */ ],
  "triangulations": [ /* array de cruzamentos */ ],
  "high_confidence_flags": [ /* strings descritivas */ ],
  "gaps": [ /* lacunas identificadas */ ],
  "legal_contexts": [ /* contextos legais agregados de todas as bases */ ],
  "next_frontiers": [ /* próximas frentes agregadas */ ]
}
```

## Anti-alucinação

- Nunca inferir relacionamento entre achados sem correspondência explícita
  nos campos normalizados.
- Sempre registrar quais campos foram comparados e qual o critério.
- Se a correspondência for fuzzy (endereço parcial, nome com typo), usar
  nível de confiança `indicio`, não `confirmado`.
- O script `scripts/triangulate.py` implementa esta lógica de forma
  reproduzível e auditável.

## Script CLI

```bash
python skills/triangulate-findings/scripts/triangulate.py \
    --findings-dir examples/case-fictional/findings/ \
    --output examples/case-fictional/findings.json
```

## Referências

- `skills/due-diligence-transnacional/references/confidence-levels.md`
- `schemas/findings.schema.json`
- `schemas/findings-consolidated.schema.json`
