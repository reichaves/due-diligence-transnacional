---
name: due-diligence-transnacional
description: >
  Orquestra investigação de due diligence de pessoa física brasileira em
  bases públicas americanas (FEC, LDA, FARA, registros corporativos
  estaduais, OpenCorporates, imprensa). Use quando o usuário pedir para
  investigar, fazer due diligence, "checar" ou "rastrear" alguém em bases
  americanas; quando mencionar nomes brasileiros que possam ter atividade
  nos EUA (offshores, doações, lobby, refinarias, real estate em Miami);
  ou quando pedir um dossiê estruturado a partir de um nome. Aciona
  sub-skills especializadas e produz PDF final com fontes citadas e
  níveis de confiança.
---

# Due Diligence Transnacional — Orquestrador

## Quando ativar

Ative quando o usuário disser algo como:
- "Investigar Fulano nas bases dos EUA"
- "Quero rastrear se X tem empresa nos EUA"
- "Faz due diligence em Y"
- "Cruza o nome Z com FEC, lobby, FARA"
- Comando explícito: `/investigar "Nome"`

## Quando NÃO ativar

- Investigação em jurisdição que não seja EUA → use outras skills
- OSINT visual (foto, vídeo) → use `osint-investigation`
- Pessoa sem relevância pública → recusar e explicar (vide `references/ethical-guardrails.md`)

## Pipeline (5 estágios)

### Estágio 1 — Coletar contexto do alvo

Pergunte ao usuário:
1. Nome completo do alvo (em português ou inglês)
2. Ocupação/empresa principal
3. Cidade/estado de residência (se conhecida)
4. Parentes diretos (cônjuge, pais, filhos) se relevantes
5. Razão jornalística para a investigação (vai para o log do projeto)
6. Bases prioritárias (default: todas)

Salve em `cases/<slug-do-alvo>/target.yaml`. Schema em
`schemas/target.schema.json`.

### Estágio 2 — Expandir variações de identidade

Acione a sub-skill `expand-brazilian-identity` passando o `target.yaml`.
Output: `identity-variations.json` (schema em
`schemas/identity-variations.schema.json`).

**STOP — revisão humana obrigatória.** Mostre as variações ao usuário e
pergunte se quer adicionar/remover. Não avance sem confirmação explícita.

### Estágio 3 — Buscas em paralelo

Para cada base na lista de prioridades, dispare a sub-skill correspondente
**como sub-agente** (contexto isolado, ferramentas só do necessário):

| Base                       | Sub-skill                  |
|----------------------------|----------------------------|
| FEC                        | `search-fec`               |
| LDA + FARA                 | `search-lobby-fara`        |
| Florida / Delaware / Texas | `search-state-corps`       |
| OpenCorporates             | `search-opencorporates`    |
| Imprensa BR + EUA          | `search-news-archive`      |

Cada sub-skill recebe `identity-variations.json` e produz
`findings/<base>.json`. Use sub-agentes para isolar contexto — segue o
princípio do Módulo 4 do curso (*"sub-agent tasks must stay narrowly scoped"*).

### Estágio 4 — Triangular achados

Acione `triangulate-findings` passando todos os `findings/*.json`.
Output: `findings-consolidated.json` com:
- Coincidências de endereço entre achados
- Coincidências de data de incorporação
- Pessoas vinculadas que aparecem em mais de uma base
- Flags de confiança elevada (≥ 2 fontes primárias)
- Lacunas identificadas (ex: "FARA não retornou — possível buscar manualmente")

**STOP — revisão humana obrigatória.** Mostre o JSON consolidado.
Pergunte se há achado a remover ou contexto a adicionar.

### Estágio 5 — Gerar dossiê PDF

Acione `generate-dossier-pdf` com `findings-consolidated.json`.
Output: `dossier.pdf` em `cases/<slug-do-alvo>/`.

Estrutura do dossiê (vide `templates/dossier_template.py`):
1. Capa + metadados da consulta
2. Resumo executivo (gerado pelo modelo a partir dos achados)
3. Metodologia
4. Variações de identidade buscadas
5. Achados por base (com fonte + nível de confiança)
6. Triangulações
7. Lacunas e próximas frentes
8. Contexto legal aplicável (§ 30121 etc.)
9. Apêndice com timestamps de todas as consultas

## Princípios para o orquestrador

- Nunca pule estágios. Se uma sub-skill falhar, registre a falha no JSON
  com `{"status": "error", "reason": "..."}` — isso vira "lacuna" no dossiê.
- Não reinterprete achados das sub-skills. O orquestrador só consolida.
- Toda comunicação com o usuário em **português** ou em **inglês** se o usuário digitar.
- Antes de gerar o PDF, sempre confirmar a lista de achados com o usuário.

## Referências

- `references/methodology.md` — metodologia detalhada
- `references/confidence-levels.md` — escala de confiança
- `references/ethical-guardrails.md` — quando recusar uma investigação
