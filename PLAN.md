# Projeto final — Knight Center MOOC

## *Advanced Prompt Engineering for Journalists*

# Due Diligence Transnacional Brasil ↔ EUA

### Pipeline CLI para investigação de brasileiros em bases públicas americanas

> **Caso de uso de referência:** investigação Ricardo Andrade Magro (Grupo Refit) — cruzamento FEC, lobby, FARA, registros corporativos estaduais e imprensa.

---

## 1. Visão geral

### Problema

Quando um nome brasileiro aparece em jurisdição americana (refinaria no Texas, offshore em Delaware, possível doação eleitoral, contrato de lobby), o repórter brasileiro precisa cruzar manualmente bases que não falam português, não conversam entre si e exigem que o nome seja "traduzido" em variações antes de cada busca. Hoje, isso é uma sessão de chat one-shot que se perde quando o caso seguinte chega.

### Solução

Uma **skill principal** (`due-diligence-transnacional`) que orquestra **sub-skills por base de dados**, executada pelo Claude Code com input estruturado e produzindo um dossiê em PDF. Cada sub-skill é um módulo independente — pode ser invocado isoladamente ou como parte do pipeline completo.

### Critério 2 do curso (automação) — framing explícito

O curso aceita automação como `reusable script | multi-stage pipeline | scheduled task | custom skill`. Este projeto **não usa scheduled task** porque investigações de due diligence são pontuais e dirigidas — rodar em cron desperdiçaria créditos de API e produziria ruído. A automação aqui combina os outros três:

- **Custom skill** (orquestrador + sub-skills) — encoda a metodologia
- **Multi-stage pipeline** (5 estágios com revisão humana entre eles) — roda o caso de ponta a ponta
- **Reusable scripts** (Python standalone) — cada sub-skill expõe um script CLI invocável fora do Claude Code, para quem prefere chamar uma base direto

Esse desenho deixa três níveis de uso para o jornalista:

1. *"Quero o pipeline completo"* → roda o orquestrador
2. *"Quero só checar o FEC"* → roda a sub-skill `search-fec` ou o script `fec_search.py`
3. *"Quero adaptar para minha pauta"* → fork do repo, ajusta `CLAUDE.md` e schemas

---

## 2. Estrutura do repositório

```
due-diligence-transnacional/
│
├── README.md                          # Documentação principal (PT/EN)
├── CLAUDE.md                          # Contexto do projeto (sempre carregado)
├── LICENSE                            # MIT
├── .gitignore                         # Inclui .env, *.pdf de casos reais
├── .env.example                       # Template de chaves de API
├── pyproject.toml                     # Dependências Python (uv/poetry)
├── plugin.json                        # Manifesto do plugin Claude Code
│
├── skills/                            # Skills carregadas sob demanda
│   ├── due-diligence-transnacional/   # ⭐ Skill orquestradora
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── methodology.md
│   │       ├── confidence-levels.md
│   │       └── ethical-guardrails.md
│   │
│   ├── expand-brazilian-identity/     # Sub-skill 1: variações de nome
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── transliteration-patterns.md
│   │   └── scripts/
│   │       └── expand_identity.py
│   │
│   ├── search-fec/                    # Sub-skill 2: FEC via MCP
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── fec-fields-guide.md
│   │       └── legal-context-30121.md
│   │
│   ├── search-lobby-fara/             # Sub-skill 3: LDA + FARA
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── lda-fara-explainer.md
│   │   └── scripts/
│   │       ├── lda_search.py
│   │       └── fara_search.py
│   │
│   ├── search-state-corps/            # Sub-skill 4: registros estaduais
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── state-registries-guide.md
│   │   └── scripts/
│   │       ├── florida_sunbiz.py
│   │       ├── delaware_corp.py
│   │       └── texas_comptroller.py
│   │
│   ├── search-opencorporates/         # Sub-skill 5: OpenCorporates
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── opencorporates_search.py
│   │
│   ├── search-news-archive/           # Sub-skill 6: imprensa BR/EUA
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── trusted-outlets.md
│   │
│   ├── triangulate-findings/          # Sub-skill 7: cruzamento
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── triangulate.py
│   │
│   └── generate-dossier-pdf/          # Sub-skill 8: PDF final
│       ├── SKILL.md
│       ├── templates/
│       │   └── dossier_template.py    # ReportLab
│       └── scripts/
│           └── generate_report.py
│
├── commands/                          # Slash commands do Claude Code
│   ├── investigar.md                  # /investigar "Nome Completo"
│   ├── expandir-nome.md               # /expandir-nome "Nome"
│   ├── consultar-base.md              # /consultar-base fec "Nome"
│   └── gerar-dossie.md                # /gerar-dossie findings.json
│
├── scripts/                           # Scripts standalone (chamáveis fora do CC)
│   ├── run_pipeline.py                # Pipeline completo via CLI
│   └── (atalhos para os scripts das sub-skills)
│
├── schemas/                           # Esquemas JSON validados
│   ├── target.schema.json             # Input
│   ├── identity-variations.schema.json
│   ├── findings.schema.json           # Output consolidado
│   └── confidence-levels.schema.json
│
├── docs/
│   ├── setup.md                       # Instalação passo a passo
│   ├── methodology.md                 # Metodologia detalhada
│   ├── legal-context.md               # § 30121, FARA, LDA, sunshine laws
│   ├── data-sources.md                # Catálogo de fontes
│   ├── ethics.md                      # Guardrails éticos de jornalismo
│   └── limitations.md                 # O que o pipeline NÃO faz
│
├── examples/
│   ├── target-template.yaml           # Esqueleto de input
│   ├── case-fictional/                # Caso 100% fictício (didático)
│   │   ├── target.yaml
│   │   ├── identity-variations.json
│   │   ├── findings.json
│   │   └── dossier.pdf
│   └── case-magro-redacted/           # Caso real, sanitizado para demo
│       ├── target.yaml
│       ├── findings.json
│       └── dossier.pdf
│
└── tests/
    ├── test_identity_expansion.py
    ├── test_triangulation.py
    └── fixtures/
        └── sample_fec_response.json
```

---

## 3. `CLAUDE.md` — Contexto do projeto

Este arquivo é carregado sempre que o Claude Code inicia uma sessão neste repositório.

```markdown
# Due Diligence Transnacional Brasil ↔ EUA

## Sobre este projeto

Este é um pipeline CLI para investigação jornalística de brasileiros que
aparecem em bases públicas americanas (FEC, LDA, FARA, registros corporativos
estaduais, OpenCorporates). Foi desenvolvido para o Knight Center MOOC
*Advanced Prompt Engineering for Journalists* e é mantido por Reinaldo Chaves
(jornalista brasileiro) - https://br.linkedin.com/in/reinaldochaves

O usuário-alvo é um jornalista brasileiro investigativo, ou pode ser um 
jornalista internacional se interagir em outro idioma. Outputs e 
comunicação com o usuário devem ser em **português brasileiro** ou 
**inglês americano** se solicitado, com terminologia jurídica e jornalística
apropriada.

## Princípios não-negociáveis

1. **Anti-alucinação acima de tudo.** Se a base não retornou o dado, diga
   "não encontrado" — nunca invente. Toda afirmação no dossiê final deve
   ter fonte explícita (base de dados + ID/URL + data da consulta).

2. **"Não encontrado" também é achado.** A ausência de rastros é um dado
   jornalístico desde que a metodologia esteja documentada. Sempre mostre
   *o que foi buscado*, não só *o que foi encontrado*.

3. **Variações de nome são obrigatórias.** Antes de qualquer busca em base
   americana, expanda o nome em pelo menos: nome completo, sobrenome
   isolado, ordem invertida, iniciais, variações com acento removido, e
   parentes diretos quando conhecidos.

4. **Contexto legal sempre presente.** Quando uma busca falha por barreira
   legal (ex: 52 U.S.C. § 30121 proíbe estrangeiro de doar a campanha
   federal), explique a barreira no dossiê — isso é parte do achado.

5. **Nível de confiança em toda afirmação.** Use a escala em
   `skills/due-diligence-transnacional/references/confidence-levels.md`:
   - `confirmado` — múltiplas fontes primárias concordam
   - `provável` — uma fonte primária + circunstanciais
   - `indício` — circunstancial, precisa confirmação
   - `não-encontrado` — busca executada sem retorno

6. **Nunca exponha PII desnecessária.** Endereços residenciais, datas de
   nascimento e CPFs/SSNs só entram no dossiê quando relevantes para a
   identificação inequívoca do alvo. Caso contrário, redija.

## Padrões editoriais (do jornalismo)

- Sem adjetivação especulativa ("supostamente", "aparentemente", "tudo
  indica") — use o nível de confiança em vez disso.
- Citação de fonte ao final de cada afirmação no formato:
  `(Fonte: FEC Schedule A, ID 202401120300xxx, consultado em DD/MM/AAAA)`
- Não use emoji, não use linguagem de marketing, não use exclamação.
- Datas no padrão DD/MM/AAAA (português) ou MM/DD/AAAA (inglês) se a perguntanta for em Inglês..
- Valores em USD com paridade BRL aproximada quando relevante. Mas sempre mostrar o valor em USD primeiro.

## Como o pipeline funciona

1. Usuário fornece um `target.yaml` com nome, contexto, e bases prioritárias
2. Skill `expand-brazilian-identity` gera variações
3. **Revisão humana** das variações (não pular esse passo)
4. Sub-skills de busca rodam em paralelo (cada uma com escopo estreito)
5. Skill `triangulate-findings` cruza endereços, datas, parentes
6. **Revisão humana** dos achados antes do PDF
7. Skill `generate-dossier-pdf` produz o relatório final

## Chaves e segredos

NUNCA escreva chaves de API em código. Use `.env` (vide `.env.example`).
Chaves esperadas:
- `FEC_API_KEY` — api.open.fec.gov
- `OPENCORPORATES_API_KEY` — opencorporates.com
- `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY` (do CLI escolhido)

## Quando NÃO usar este pipeline

- Pessoas comuns sem relevância pública (problema ético — vide `docs/ethics.md`)
- Investigações em jurisdições fora EUA/BR (sub-skills não cobrem)
- Quando o caso pede análise qualitativa de documento (use Claude direto)
- Quando há prazo de minutos (pipeline leva 15-30 min de ponta a ponta)
```

---

## 4. `README.md` — Documentação principal

```markdown
# Due Diligence Transnacional Brasil ↔ EUA

> Pipeline CLI para cruzar nomes brasileiros em bases públicas americanas.
> Construído com Claude Code, MCP fec-finance, e APIs públicas.

**Status:** projeto educacional — Knight Center MOOC, *Advanced Prompt
Engineering for Journalists* (2026).

## O que faz

Recebe um nome de pessoa física brasileira como input e gera um dossiê
estruturado em PDF cobrindo:

- Doações eleitorais federais (FEC)
- Atividade de lobby registrada (LDA — Lobbying Disclosure Act)
- Registro como agente estrangeiro (FARA)
- Empresas em registros corporativos estaduais (FL, DE, TX por padrão)
- Presença na base global OpenCorporates
- Cobertura na imprensa BR e EUA

Toda afirmação no dossiê tem fonte explícita e nível de confiança.

## O que NÃO faz (escopo fechado)

- Não acessa bases pagas (Lexis, Sayari, Refinitiv)
- Não faz reconhecimento facial nem OSINT visual (use a skill OSINT separada)
- Não roda agendado — investigações são pontuais
- Não substitui o repórter: o pipeline entrega leads e dossiê estruturado;
  interpretação editorial fica com o jornalista

## Instalação

```bash
git clone https://github.com/reichaves/due-diligence-transnacional.git
cd due-diligence-transnacional
cp .env.example .env  # editar com suas chaves
uv sync               # ou: pip install -e .
```

Pré-requisitos:

- Python 3.11+
- Claude Code instalado (Claude Max ou API key)
- MCP fec-finance configurado (vide `docs/setup.md`)

## Uso

### Modo 1 — Pipeline completo (recomendado)

```bash
# Dentro do Claude Code, no diretório do projeto:
/investigar "Ricardo Andrade Magro"
```

O Claude vai:

1. Ler `CLAUDE.md` e ativar a skill `due-diligence-transnacional`
2. Pedir contexto extra (ocupação, cidade, parentes conhecidos)
3. Gerar variações e pedir sua aprovação
4. Disparar buscas em paralelo (sub-agentes)
5. Mostrar achados consolidados para sua revisão
6. Gerar o PDF final

### Modo 2 — Sub-skill isolada

```bash
/consultar-base fec "Ricardo Magro"
```

Útil quando você só quer checar uma base específica.

### Modo 3 — Script standalone (sem Claude Code)

```bash
python scripts/fec_search.py --name "Ricardo Magro" --state FL
```

Cada sub-skill expõe um script Python chamável fora do Claude Code, para
quem prefere integrar em pipelines próprios.

## Arquitetura

A automação combina três padrões aceitos pelo curso:

| Padrão           | Onde                                     |
| ---------------- | ---------------------------------------- |
| Custom skill     | `skills/due-diligence-transnacional/`    |
| Multi-stage pipe | 5 estágios em `commands/investigar.md`   |
| Reusable script  | `scripts/*.py` e `skills/*/scripts/*.py` |

Não há scheduled task — investigações de due diligence são pontuais e
dirigidas; rodar em cron seria desperdício de créditos de API.

Cada sub-skill tem **escopo estreito** (princípio do Módulo 4 do curso,
*"agent telephone — sub-agent tasks must stay narrowly scoped"*) e roda
em contexto isolado. Reviews humanas obrigatórias entre estágios 2→3 e 4→5.

## Exemplos

Vide `examples/case-fictional/` para um walkthrough didático com dados
sintéticos. Vide `examples/case-magro-redacted/` para um caso real
sanitizado.

## Limitações conhecidas

Documentadas em `docs/limitations.md`. Resumo:

- Transliteração imperfeita de nomes brasileiros em bases americanas
  (Magro vs. Maggro vs. M. Magro) — mitigado mas não eliminado
- Bases estaduais variam em qualidade e cobertura
- FARA tem atraso de meses entre registro e disponibilização pública
- Empresas em Delaware revelam pouca informação publicamente — sub-skill
  retorna registro de existência, mas não de "ultimate beneficial owner"

## Ética

Este pipeline foi desenhado para investigação de pessoas com **relevância
pública** (gestores de empresas com contratos públicos, doadores políticos,
agentes envolvidos em crimes ou violações de direitos humanos). Não use
para investigar pessoas comuns. Diretrizes em `docs/ethics.md`.

## Licença

MIT — vide `LICENSE`.

## Citação

Se o pipeline ajudar uma reportagem, sugerimos citar:

> Chaves, R. (2026). *Due Diligence Transnacional Brasil ↔ EUA: pipeline
> CLI para investigação jornalística*. Knight Center MOOC final project.
> https://github.com/reichaves/due-diligence-transnacional

## Autor

Reinaldo Chaves — jornalista de dados no Brasil.
github.com/reichaves
https://br.linkedin.com/in/reinaldochaves

```
---

## 5. `plugin.json` — Manifesto do plugin Claude Code

```json
{
  "name": "due-diligence-transnacional",
  "version": "0.1.0",
  "description": "Pipeline CLI para due diligence de brasileiros em bases públicas americanas",
  "author": "Reinaldo Chaves <reichaves@gmail.com>",
  "license": "MIT",
  "homepage": "https://github.com/reichaves/due-diligence-transnacional",
  "skills": [
    "skills/due-diligence-transnacional",
    "skills/expand-brazilian-identity",
    "skills/search-fec",
    "skills/search-lobby-fara",
    "skills/search-state-corps",
    "skills/search-opencorporates",
    "skills/search-news-archive",
    "skills/triangulate-findings",
    "skills/generate-dossier-pdf"
  ],
  "commands": [
    "commands/investigar.md",
    "commands/expandir-nome.md",
    "commands/consultar-base.md",
    "commands/gerar-dossie.md"
  ],
  "requires": {
    "mcp": ["fec-finance"],
    "env": ["OPENCORPORATES_API_KEY"]
  }
}
```

---

## 6. Skill orquestradora — `skills/due-diligence-transnacional/SKILL.md`

```markdown
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
princípio do Módulo 4 do curso (*"sub-agent reviews don't count against
your main session's tokens"*).

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
```

---

## 7. Sub-skills — visão geral e exemplos

### 7.1 Lista das sub-skills

| Skill                       | Função                                              | Bases/APIs                 |
| --------------------------- | --------------------------------------------------- | -------------------------- |
| `expand-brazilian-identity` | Gera variações de nome para busca em bases EUA      | (computa, sem API)         |
| `search-fec`                | Busca contribuições eleitorais federais             | FEC via MCP fec-finance    |
| `search-lobby-fara`         | Busca registros de lobby (LDA) e agente estrangeiro | senate.gov, efile.fara.gov |
| `search-state-corps`        | Busca empresas em registros estaduais               | sunbiz.org, DE, TX         |
| `search-opencorporates`     | Busca global de empresas                            | opencorporates.com API     |
| `search-news-archive`       | Busca imprensa BR + EUA                             | web search                 |
| `triangulate-findings`      | Cruza endereços, datas, pessoas vinculadas          | (computa, sem API)         |
| `generate-dossier-pdf`      | Gera PDF estruturado final                          | ReportLab                  |

### 7.2 Exemplo completo — `skills/search-fec/SKILL.md`

```markdown
---
name: search-fec
description: >
  Busca contribuições eleitorais federais americanas (Schedule A da FEC)
  para um conjunto de variações de nome de pessoa brasileira. Use quando
  o orquestrador `due-diligence-transnacional` solicitar, ou quando o
  usuário pedir explicitamente "/consultar-base fec NOME". Retorna JSON
  estruturado com hits, no-hits e contexto legal aplicável.
---

# Busca FEC — Federal Election Commission

## Inputs

- `identity-variations.json` (obrigatório)
- `state_filter` (opcional): UF americana para filtrar (ex: "FL", "TX")

## Ferramentas

- MCP `fec-finance` (obrigatório, configurar via `docs/setup.md`)

## Procedimento

1. Para cada variação em `identity-variations.json`, executar:
```

   fec-finance:search_contributions(contributor_name=<variação>)

```
Quando útil, repetir com `contributor_state=<UF>`.

2. Para cada hit, registrar:
- `contributor_name` exato como aparece na base
- `contributor_employer`, `contributor_occupation`
- `contribution_receipt_date`
- `contribution_receipt_amount`
- `committee_id` e `committee_name`
- `transaction_id` (para citar)
- URL fec.gov da transação

3. Quando NENHUMA variação retornar hit, registrar explicitamente em
`no_hits` com a lista das variações testadas.

## Output

`findings/fec.json` conforme schema em `schemas/findings.schema.json`,
seção `fec`.

```json
{
  "base": "FEC",
  "consulted_at": "2026-04-29T14:30:00-03:00",
  "queries_executed": 12,
  "hits": [],
  "no_hits": ["Ricardo Andrade Magro", "Ricardo Magro", "..."],
  "legal_context": [
 "52 U.S.C. § 30121 proíbe estrangeiros não-residentes de doar a campanhas federais americanas. Ausência de hits em FEC para cidadão brasileiro é o resultado esperado e legalmente coerente, não um achado negativo."
  ],
  "next_frontiers": [
 "Verificar se há green card ou cidadania americana — se sim, doação seria legal e ausência seria significativa",
 "Verificar 501(c)(4)s, que aceitam doações de estrangeiros e não exigem disclosure"
  ]
}
```

## Anti-alucinação

- Nunca afirme que alguém doou se o hit não veio com `transaction_id`.

- Sempre relate variações testadas, mesmo que tenha encontrado em uma só.

- Diferencie hit por nome exato vs. hit por nome similar (a FEC retorna
  ambos).
  
  ```
  
  ```

### 7.3 Exemplo curto — `skills/expand-brazilian-identity/SKILL.md`

```markdown
---
name: expand-brazilian-identity
description: >
  Gera variações ortográficas e estruturais de um nome brasileiro para
  uso em buscas em bases americanas. Use sempre antes de qualquer busca
  em base dos EUA — nomes brasileiros são transliterados de forma
  inconsistente (ordem invertida, sobrenomes compostos, acentos removidos).
---

# Expansão de Identidade Brasileira

## Inputs

`target.yaml` com `nome_completo`, `parentes` (opcional), `apelidos` (opcional)

## Variações geradas (mínimo)

1. Nome completo como recebido
2. Nome completo sem acentos
3. Primeiro nome + último sobrenome ("Ricardo Magro")
4. Último sobrenome + primeiro nome ("Magro Ricardo") — convenção de
   alguns formulários americanos
5. Iniciais + sobrenome ("R. Magro", "R.A. Magro")
6. Sobrenome isolado (para buscas amplas — gera muito ruído mas captura
   variações irrecuperáveis pelas anteriores)
7. Para cada parente direto fornecido, gerar suas variações
8. Para cada apelido fornecido, registrar como variação separada

## Output

`identity-variations.json` validado contra `schemas/identity-variations.schema.json`.

## Princípio

Sempre gerar a lista, mostrar ao usuário e pedir aprovação. Não buscar
sem confirmação humana — variações ruins multiplicam ruído nas sub-skills.
```

### 7.4 Demais sub-skills (resumos de uma linha)

- **`search-lobby-fara/SKILL.md`** — Consulta o Senate LDA Disclosure Database e o eFile FARA via scraping leve com Playwright; retorna registros formais de lobby ou agente estrangeiro.
- **`search-state-corps/SKILL.md`** — Por estado (FL/sunbiz, DE, TX/Comptroller), retorna empresas onde a pessoa aparece como officer, registered agent ou governing person.
- **`search-opencorporates/SKILL.md`** — Busca global em OpenCorporates por nome (officer search), retorna empresas e jurisdições, útil para descobrir incorporações fora dos estados americanos cobertos.
- **`search-news-archive/SKILL.md`** — Busca em imprensa brasileira (Folha, Estadão, Globo, Intercept, Pública, Piauí) e americana (NYT, WaPo, ProPublica, Reuters), com filtro de outlets confiáveis em `references/trusted-outlets.md`.
- **`triangulate-findings/SKILL.md`** — Recebe todos os JSONs de achados, identifica coincidências (mesmo endereço, mesma data de incorporação, mesma pessoa vinculada), produz JSON consolidado com flags de confiança.
- **`generate-dossier-pdf/SKILL.md`** — Recebe o JSON consolidado, aplica o template ReportLab e produz o PDF final com capa, metodologia, achados, citações e timestamps.

---

## 8. Slash commands

Cada `commands/*.md` é um arquivo curto que define um atalho. Exemplo:

### `commands/investigar.md`

```markdown
---
description: Roda o pipeline completo de due diligence transnacional
argument-hint: "Nome Completo do Alvo"
---

Você vai investigar a pessoa cujo nome está em $ARGUMENTS.

Aja como o orquestrador definido em
`skills/due-diligence-transnacional/SKILL.md`. Siga os 5 estágios sem
pular nenhum. Pare nas revisões humanas obrigatórias (estágios 2→3 e 4→5).
```

Outros: `expandir-nome.md`, `consultar-base.md`, `gerar-dossie.md` —
mesma estrutura, escopo menor.

---

## 9. Schemas — exemplo de `schemas/target.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Target",
  "type": "object",
  "required": ["nome_completo", "razao_investigativa"],
  "properties": {
    "nome_completo": { "type": "string", "minLength": 3 },
    "ocupacao": { "type": "string" },
    "empresa_principal": { "type": "string" },
    "cidade_residencia": { "type": "string" },
    "uf_residencia_us": {
      "type": "string",
      "pattern": "^[A-Z]{2}$",
      "description": "UF americana se residente nos EUA"
    },
    "parentes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["nome", "relacao"],
        "properties": {
          "nome": { "type": "string" },
          "relacao": {
            "type": "string",
            "enum": ["conjuge", "ex-conjuge", "pai", "mae", "filho", "filha", "irmao", "irma", "outro"]
          }
        }
      }
    },
    "apelidos": { "type": "array", "items": { "type": "string" } },
    "razao_investigativa": {
      "type": "string",
      "minLength": 30,
      "description": "Por que esta pessoa está sendo investigada — vai para o log e o dossiê"
    },
    "bases_prioritarias": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["fec", "lda-fara", "state-corps", "opencorporates", "news"]
      },
      "default": ["fec", "lda-fara", "state-corps", "opencorporates", "news"]
    }
  }
}
```

---

## 10. Documentação adicional

### `docs/ethics.md` — pontos obrigatórios

- Quando recusar (pessoa sem relevância pública, perseguição política, doxxing)
- Como tratar PII (mínimo necessário)
- Diretriz de não armazenar dossiês em repositório público sem consentimento
- Como creditar fontes de bases públicas

### `docs/limitations.md` — escopo fechado

Lista explícita do que o pipeline NÃO faz:

- Não cobre jurisdições além de EUA
- Não acessa Lexis/Sayari/Refinitiv
- Não faz reconhecimento facial
- Não busca em bases vazadas
- Não substitui análise editorial

### `docs/setup.md` — instalação

Passo a passo para:

1. Instalar Claude Code
2. Configurar MCP fec-finance
3. Obter chaves OpenCorporates, FEC API
4. Rodar exemplo `case-fictional` para validar

---

## 11. Roadmap de entrega (4 semanas do curso)

| Semana | Entrega                                                          |
| ------ | ---------------------------------------------------------------- |
| 1      | Setup do repo, `CLAUDE.md`, `README.md`, `target.schema.json`    |
| 2      | **Proposta de projeto submetida.** Skills 1-2 (expand, fec)      |
| 3      | Skills 3-6 (lobby/fara, state-corps, opencorporates, news)       |
| 4      | Skills 7-8 (triangulate, generate-pdf), exemplo redacted, README |

**Final do Módulo 4:** repositório público + caso `case-fictional` rodando ponta a ponta + caso `case-magro-redacted` como demonstração.

---

## 12. O que apresentar no fórum do curso

Sugestão de post (em inglês, para a comunidade internacional do MOOC):

> **Title:** Cross-border due diligence pipeline (BR ↔ US public records)
> 
> **Problem:** Brazilian investigative reporters routinely need to check whether a Brazilian person of interest appears in US public databases (FEC, LDA, FARA, state corporate registries). The work is repetitive, name transliteration is messy, and one-shot chat sessions are not reusable.
> 
> **What I built:** A Claude Code plugin with one orchestrator skill and 8 sub-skills (one per database family), a 5-stage pipeline with mandatory human review between stages, JSON schemas for inputs and findings, and a ReportLab PDF dossier as final output.
> 
> **Automation pattern:** `custom skill + multi-stage pipeline + reusable scripts` — explicitly NOT scheduled, because investigations are targeted and API-cost-sensitive.
> 
> **What it doesn't do:** Replace editorial judgment. The pipeline produces structured findings and a dossier with confidence levels; interpretation stays with the journalist.
> 
> **Repo:** [link]
> **Sample case:** [link to redacted Magro example]

---

*Plano elaborado em 29/04/2026 para Reinaldo Chaves (Jornalista de dados no Brasil - https://br.linkedin.com/in/reinaldochaves), como projeto final do Knight Center MOOC* Advanced Prompt Engineering for Journalists *(turma 2026, instrutor Joe Amditis).*
