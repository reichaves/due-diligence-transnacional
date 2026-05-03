# Due Diligence Transnacional

[![GitHub](https://img.shields.io/badge/GitHub-reichaves-181717?logo=github)](https://github.com/reichaves/due-diligence-transnacional)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatível-D4A017)](https://claude.ai/code)
[![License](https://img.shields.io/badge/Licença-MIT-22c55e)](LICENSE)
[![OpenFEC](https://img.shields.io/badge/API-OpenFEC-dc2626)](https://api.open.fec.gov/developers/)
[![Testes](https://img.shields.io/badge/Testes-99%20passando-22c55e)](tests/)

> Pipeline CLI para jornalistas investigativos cruzarem **qualquer nome com vínculos nos EUA** em bases públicas americanas — gerando um dossiê em PDF com fontes citadas e níveis de confiança. Otimizado para nomes brasileiros e latino-americanos; funciona para qualquer país de origem.

**Autor:** [Reinaldo Chaves](https://github.com/reichaves) — jornalista de dados no Brasil · reichaves@gmail.com · [LinkedIn](https://br.linkedin.com/in/reinaldochaves)

> **Nota:** Todos os exemplos neste repositório usam nomes e empresas fictícios criados exclusivamente para fins didáticos. Qualquer semelhança com pessoas ou organizações reais é mera coincidência.

---

## ⚠️ Aviso Importante — Leia Antes de Usar

**Este pipeline trabalha com bases de dados públicas dos EUA e produz documentos de uso jornalístico. Antes de usar, compreenda as seguintes limitações e responsabilidades:**

- **Resultados não são verdade absoluta.** Os achados refletem o que está disponível em bases públicas no momento da consulta. Registros podem estar desatualizados, incompletos ou conter erros. Todo resultado deve ser verificado de forma independente antes da publicação.
- **"Não encontrado" não significa inocência.** A ausência de registros em bases americanas pode indicar simplesmente que a pessoa usa estruturas corporativas intermediárias, nomes diferentes ou que os registros ainda não foram indexados.
- **Instabilidade de APIs externas.** Algumas bases (ex.: Florida Sunbiz, OpenCorporates) podem retornar erros HTTP 403/401 ou estar temporariamente fora do ar. Nesses casos, o pipeline documenta a falha e sugere verificação manual — não inventa dados.
- **Chave da API OpenCorporates é necessária.** Sem uma chave válida, buscas no OpenCorporates retornam HTTP 401. Obtenha a chave gratuita para jornalistas em [opencorporates.com/api_accounts/new](https://opencorporates.com/api_accounts/new).
- **Uso exclusivo para interesse público.** Este pipeline é restrito à investigação de figuras públicas com vínculo documentado nos EUA (executivos, doadores políticos, agentes estrangeiros, investigados em crimes reportados). Não use para investigar cidadãos comuns.
- **Responsabilidade editorial é do jornalista.** O pipeline entrega leads estruturados com fontes citadas. A interpretação, contextualização e decisão de publicação são inteiramente responsabilidade do repórter e do veículo.

---

## O que faz

A partir de um nome de alvo e contexto, o pipeline:

1. Expande o nome em variações para busca (transliterações, iniciais, ordem invertida, parentes)
2. Executa buscas em paralelo nas bases públicas americanas:
   - **FEC** — doações eleitorais federais (Schedule A)
   - **LDA** — registros de lobby (Lobbying Disclosure Act)
   - **FARA** — registro como agente estrangeiro
   - **Registros corporativos estaduais** — Flórida (Sunbiz), Delaware, Texas
   - **OpenCorporates** — base global de empresas
   - **Arquivo de imprensa** — veículos brasileiros e americanos
3. Triangula achados (coincidências de endereço, datas, sócios comuns)
4. Produz um dossiê em PDF com fontes explícitas e níveis de confiança

Toda afirmação no dossiê tem citação de fonte. "Não encontrado" também é um achado — a metodologia é sempre documentada.

## O que NÃO faz (escopo fechado)

- Não acessa bases pagas (Lexis, Sayari, Refinitiv)
- Não faz reconhecimento facial nem OSINT visual (use uma skill OSINT separada) - Confira em https://github.com/reichaves/osint-investigation
- Não roda de forma agendada — investigações são pontuais e dirigidas
- Não substitui o repórter: o pipeline entrega leads estruturados; a interpretação editorial fica com o jornalista

---

## Pré-requisitos

| Componente | Versão mínima | Verificar |
|-----------|--------------|-----------|
| Python | 3.11 | `python --version` |
| Claude Code | qualquer | `claude --version` |
| Git | qualquer | `git --version` |

Claude Code requer assinatura **Claude Max** ou uma **chave de API Anthropic**. Acesse [claude.ai/code](https://claude.ai/code) para começar.

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/reichaves/due-diligence-transnacional.git
cd due-diligence-transnacional
```

### 2. Criar ambiente virtual e instalar dependências

**Com uv (recomendado):**

```bash
pip install uv
uv sync
```

**Com pip:**

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e .
```

Pacotes instalados: `click`, `pyyaml`, `requests`, `beautifulsoup4`, `reportlab`, `pydantic`, `jsonschema`, `python-dotenv`.

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas chaves de API (veja a seção [Chaves de API](#chaves-de-api) abaixo).

### 4. Configurar o servidor MCP fec-mcp (recomendado)

O pipeline usa o servidor MCP [`fec-mcp`](https://github.com/reichaves/fec-mcp-server) para consultas estruturadas à FEC. A configuração já está no `.mcp.json` na raiz do repositório:

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

Instale o `uvx` se necessário:

```bash
pip install uv
```

Sem o servidor MCP, o pipeline usa um script Python que chama diretamente a API pública da FEC — a cobertura é equivalente, mas mais lenta e menos estruturada.

### 5. Abrir o Claude Code dentro do diretório do projeto

Os slash commands são registrados via arquivos em `.claude/commands/` — o Claude Code os carrega automaticamente ao abrir dentro do diretório do projeto:

```bash
cd due-diligence-transnacional
claude
```

O Claude Code carrega o `CLAUDE.md` e todos os commands em `.claude/commands/` na inicialização. Nenhum registro manual é necessário.

> **Solução de problemas:** Se aparecer o erro `Unknown skill: investigar` (ou qualquer outro comando), verifique se você abriu o Claude Code de **dentro** do diretório `due-diligence-transnacional`. Os commands têm escopo de projeto e só ficam disponíveis quando o Claude Code está rodando no diretório correto.

### 6. Validar a instalação

Execute o conjunto de testes:

```bash
pytest tests/ -v
```

Saída esperada: `99 passed`.

Opcionalmente, rode o exemplo fictício ponta a ponta para confirmar que a geração de PDF funciona:

```bash
python scripts/run_pipeline.py \
    --target examples/case-fictional/target.yaml \
    --skip-search \
    --findings-dir examples/case-fictional/findings/ \
    --output-dir /tmp/teste-output/
```

Esperado: um `dossier.pdf` em `/tmp/teste-output/` com 10 seções.

---

## Chaves de API

### Obrigatórias

| Chave | Finalidade | Onde obter |
|-------|-----------|-----------|
| `FEC_API_KEY` | Consultas à base da FEC (limites de requisição mais altos) | [api.data.gov/signup](https://api.open.fec.gov/developers/) — gratuita, chega em minutos |
| `OPENCORPORATES_API_KEY` | Buscas no registro global de empresas | [opencorporates.com/api_accounts/new](https://opencorporates.com/api_accounts/new) — plano gratuito: 50 req/dia; plano jornalista: gratuito para veículos credenciados |

### Opcionais

| Chave | Finalidade |
|-------|-----------|
| `ANTHROPIC_API_KEY` | Acesso direto à API Anthropic (se não usar Claude Code com assinatura Max) |
| `LOG_LEVEL` | Controla verbosidade dos logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`) — padrão: `INFO` |

> A API da FEC funciona sem chave (limite de 1.000 req/dia), mas cadastrar uma chave gratuita eleva o limite para 1.000 req/hora.

Copie `.env.example` para `.env` e preencha com seus valores. O arquivo `.env` está no `.gitignore` e **nunca deve ser commitado**.

---

## Uso

Todos os comandos ficam disponíveis dentro do Claude Code ao rodar no diretório do projeto. Cada comando tem versão em português e em inglês — são equivalentes.

### Modo 1 — Pipeline completo (recomendado)

```
/investigar "Carlos Eduardo Ferreira"    # português
/investigate "Carlos Eduardo Ferreira"   # inglês
```

O Claude vai:

1. Carregar o `CLAUDE.md` e ativar a skill `due-diligence-transnacional`
2. Pedir contexto adicional (ocupação, cidade, parentes conhecidos)
3. Gerar variações de nome e solicitar sua aprovação
4. Disparar buscas em paralelo em todas as bases configuradas (sub-agentes)
5. Mostrar achados consolidados para sua revisão
6. Gerar o dossiê final em PDF

Revisões humanas obrigatórias nos estágios 2→3 e 4→5.

### Modo 2 — Consulta em base única

```
/consultar-base fec "Carlos Ferreira"    # português
/search-database fec "Carlos Ferreira"   # inglês
```

Útil quando você só quer verificar uma base específica.

Bases disponíveis: `fec`, `lda`, `fara`, `fl` (Flórida), `de` (Delaware), `tx` (Texas), `oc` (OpenCorporates), `news-br`, `news-us`.

### Modo 3 — Expansão de nome isolada

```
/expandir-nome "Carlos Eduardo Ferreira"   # português
/expand-name "Carlos Eduardo Ferreira"     # inglês
```

Gera variações de nome sem executar nenhuma busca. Útil para revisar o conjunto de variações antes de uma investigação completa.

### Modo 4 — Gerar dossiê a partir de achados existentes

```
/gerar-dossie cases/ferreira/findings-consolidated.json    # português
/generate-dossier cases/ferreira/findings-consolidated.json  # inglês
```

Gera o PDF a partir de um arquivo de achados consolidados já existente. Use quando quiser re-gerar o dossiê após editar manualmente os achados.

### Modo 5 — Script Python standalone (sem Claude Code)

```bash
python scripts/run_pipeline.py --target examples/case-fictional/target.yaml
```

Cada sub-skill também expõe seu próprio script, chamável de forma independente:

```bash
# Busca FEC
python skills/search-fec/scripts/fec_search.py \
    --variations identity-variations.json \
    --output findings/fec.json

# Registro corporativo estadual (Flórida)
python skills/search-state-corps/scripts/florida_sunbiz.py \
    --variations identity-variations.json \
    --output findings/fl_sunbiz.json

# Triangular achados
python skills/triangulate-findings/scripts/triangulate.py \
    --findings-dir findings/ \
    --output findings-consolidated.json

# Gerar dossiê PDF em português (padrão)
python skills/generate-dossier-pdf/scripts/generate_report.py \
    --consolidated findings-consolidated.json \
    --output dossier.pdf \
    --lang pt-BR

# Gerar dossiê PDF em inglês
python skills/generate-dossier-pdf/scripts/generate_report.py \
    --consolidated findings-consolidated.json \
    --output dossier-en.pdf \
    --lang en-US
```

### Saída bilíngue do dossiê PDF

O dossiê pode ser gerado em português (padrão) ou inglês. A língua é resolvida na seguinte ordem de precedência:

1. **Flag `--lang`** passada diretamente ao script (prioridade máxima)
2. **Campo `investigation_language`** no `target.yaml` (`pt-BR` ou `en-US`)
3. **Padrão:** `pt-BR`

Exemplo com flag explícita:

```bash
python skills/generate-dossier-pdf/scripts/generate_report.py \
    --consolidated findings-consolidated.json \
    --output dossier-en.pdf \
    --lang en-US
```

Exemplo via `target.yaml`:

```yaml
investigation_language: "en-US"
```

Todos os rótulos de seção, cabeçalhos de tabela, níveis de confiança e o bloco de aviso legal são traduzidos automaticamente.

### Investigações em inglês / alvos não latino-americanos

O pipeline funciona para **qualquer jornalista** investigando **qualquer pessoa com vínculos nos EUA** — independentemente do país do jornalista ou da origem do alvo. Um repórter estadunidense investigando um empresário nigeriano com empresa no Delaware, um jornalista europeu rastreando um investidor chinês com imóveis na Flórida, ou um jornalista argentino seguindo a atividade de lobby de um compatriota podem todos usar este pipeline.

Defina `investigation_language: en-US` e `origin_country` no seu `target.yaml`:

> **Nota de cobertura para nomes não-latinos:** O algoritmo de expansão de nome lida com remoção de acentos e inversão de ordem para qualquer nome. Para padrões de transliteração específicos de nomes chineses, árabes, nigerianos ou outros não-latinos, a cobertura é menor do que para nomes latinos — revise as variações geradas com cuidado antes de executar as buscas.

```yaml
nome_completo: "Pablo Vargas Mendoza"
ocupacao: "General Manager"
empresa_principal: "Vargas Energy USA LLC"
origin_country: "PE"
investigation_language: "en-US"
razao_investigativa: >
  Pablo Vargas Mendoza é gerente-geral da Vargas Energy USA LLC, subsidiária
  americana de uma empresa petrolífera peruana.
bases_prioritarias:
  - fec
  - lda-fara
  - state-corps
  - opencorporates
  - news
```

Em seguida, execute com o comando em inglês:

```
/investigate "Pablo Vargas Mendoza"
```

Veja `examples/case-vargas-fictional/` para um walkthrough completo com alvo peruano.

---

## Estrutura do dossiê PDF

Cada dossiê gerado contém 10 seções:

| # | Seção | Conteúdo |
|---|-------|----------|
| 1 | Capa | Nome do alvo, data, aviso de confidencialidade |
| 2 | Resumo executivo | Achados de alta confiança, bandeiras de risco |
| 3 | Contexto legal | Marcos legais relevantes (ex.: 52 U.S.C. § 30121) |
| 4 | FEC — Doações eleitorais | Schedule A, PACs, comitês — todos os hits ou "não encontrado" documentado |
| 5 | LDA / FARA — Lobby e agência estrangeira | Registros de lobby e agência com datas e clientes |
| 6 | Registros corporativos estaduais | Flórida, Delaware, Texas — sócios, endereços, datas |
| 7 | OpenCorporates / Offshore | Empresas globais, offshores, indicadores de jurisdição opaca |
| 8 | Arquivo de imprensa | Cobertura jornalística brasileira e americana, com URL e data |
| 9 | Aviso legal e ético | Limitações da metodologia, precauções editoriais, responsabilidade |
| 10 | Apêndice — Timestamps | Log completo de todas as consultas com data/hora e status |

---

## Referência de comandos

| Português | Inglês | Descrição |
|---|---|---|
| `/investigar "Nome"` | `/investigate "Name"` | Pipeline completo em 5 estágios |
| `/consultar-base <base> "Nome"` | `/search-database <db> "Name"` | Consulta a uma base específica |
| `/expandir-nome "Nome"` | `/expand-name "Name"` | Expansão de variações de nome |
| `/gerar-dossie <findings.json>` | `/generate-dossier <findings.json>` | Gerar PDF a partir de achados existentes |

---

## Estrutura do projeto

```
due-diligence-transnacional/
├── CLAUDE.md                      # Instruções do projeto carregadas pelo Claude na inicialização
├── pyproject.toml                 # Metadados do pacote Python e dependências
├── .env.example                   # Template de variáveis de ambiente
├── .mcp.json                      # Configuração do servidor MCP (fec-mcp)
│
├── .claude/                       # Configuração do projeto para o Claude Code
│   ├── settings.json              # Lista de servidores MCP habilitados
│   └── commands/                  # Slash commands — carregados automaticamente na inicialização
│       ├── investigar.md          # /investigar — pipeline completo (português)
│       ├── investigate.md         # /investigate — pipeline completo (inglês)
│       ├── consultar-base.md      # /consultar-base — consulta por base (português)
│       ├── search-database.md     # /search-database — consulta por base (inglês)
│       ├── expandir-nome.md       # /expandir-nome — expansão de nome (português)
│       ├── expand-name.md         # /expand-name — expansão de nome (inglês)
│       ├── gerar-dossie.md        # /gerar-dossie — geração de PDF (português)
│       └── generate-dossier.md    # /generate-dossier — geração de PDF (inglês)
│
├── commands/                      # Cópias-fonte dos arquivos de comando (referência de documentação)
│   ├── investigar.md
│   ├── consultar-base.md
│   ├── expandir-nome.md
│   └── gerar-dossie.md
│
├── skills/                        # Definições de skills referenciadas pelo CLAUDE.md
│   ├── due-diligence-transnacional/   # Skill orquestradora principal
│   │   ├── SKILL.md               # Lógica de orquestração, detecção MCP, estágios do pipeline
│   │   └── references/
│   │       ├── confidence-levels.md   # Escala de confiança: confirmado/provável/indício/não-encontrado
│   │       ├── ethical-guardrails.md  # Quando recusar uma investigação
│   │       └── methodology.md         # Documentação da metodologia de pesquisa
│   │
│   ├── expand-brazilian-identity/ # Gerador de variações de nome (funciona para qualquer nacionalidade)
│   │   ├── SKILL.md               # Lida com transliteração, iniciais, ordem invertida, parentes
│   │   ├── references/transliteration-patterns.md
│   │   └── scripts/expand_identity.py  # CLI standalone; suporta flag --origin-country
│   │
│   ├── search-fec/                # Busca de doações na FEC
│   │   ├── SKILL.md               # Execução em 3 níveis (fec-mcp → osint → script Python)
│   │   └── references/
│   │       ├── fec-fields-guide.md    # Mapeamento dos campos do Schedule A
│   │       ├── legal-context-30121.md # 52 U.S.C. § 30121 (proibição de doação de estrangeiro)
│   │       └── mcp-detection.md       # Lógica de detecção MCP com templates de methodology_note
│   │
│   ├── search-lobby-fara/         # Busca LDA + FARA
│   │   ├── SKILL.md
│   │   ├── references/lda-fara-explainer.md
│   │   ├── scripts/lda_search.py
│   │   └── scripts/fara_search.py
│   │
│   ├── search-state-corps/        # Busca em registros corporativos estaduais (FL, DE, TX)
│   │   ├── SKILL.md
│   │   ├── references/state-registries-guide.md
│   │   ├── scripts/florida_sunbiz.py
│   │   ├── scripts/delaware_corp.py
│   │   └── scripts/texas_comptroller.py
│   │
│   ├── search-opencorporates/     # Busca global OpenCorporates
│   │   ├── SKILL.md
│   │   └── scripts/opencorporates_search.py
│   │
│   ├── search-news-archive/       # Arquivo de imprensa (BR + EUA + busca genérica)
│   │   ├── SKILL.md
│   │   └── references/trusted-outlets.md
│   │
│   ├── triangulate-findings/      # Cruzamento de todos os achados
│   │   ├── SKILL.md               # Detecta coincidências de endereço/data/sócios entre fontes
│   │   └── scripts/triangulate.py
│   │
│   └── generate-dossier-pdf/      # Gerador de dossiê PDF
│       ├── SKILL.md
│       ├── scripts/generate_report.py  # Suporta --lang pt-BR|en-US
│       └── templates/dossier_template.py  # Template ReportLab (estrutura de 10 seções)
│
├── schemas/                       # Validação JSON Schema (Draft 2020-12)
│   ├── target.schema.json         # Input: definição do alvo
│   ├── identity-variations.schema.json   # Conjunto de variações de nome
│   ├── findings.schema.json       # Registro de achado individual por fonte
│   ├── findings-consolidated.schema.json # Output triangulado
│   └── confidence-levels.schema.json     # Enum de nível de confiança
│
├── docs/                          # Documentação de referência
│   ├── setup.md                   # Guia de instalação detalhado (incluindo setup MCP)
│   ├── methodology.md             # Metodologia de pesquisa
│   ├── legal-context.md           # Marcos legais americanos aplicáveis
│   ├── data-sources.md            # Cobertura e limitações por base de dados
│   ├── ethics.md                  # Diretrizes éticas e guardrails
│   └── limitations.md             # Limitações conhecidas por jurisdição e fonte
│
├── examples/                      # Exemplos ponta a ponta com achados pré-gerados
│   ├── target-template.yaml       # Template para criar um novo target.yaml
│   ├── case-fictional/            # Alvo brasileiro (Carlos Eduardo Fontana) — achados + PDF
│   ├── case-brazil-fictional/     # Caso brasileiro alternativo (Carlos Eduardo Ferreira)
│   └── case-vargas-fictional/     # Alvo não brasileiro (peruano) — demonstra suporte i18n
│
├── tests/                         # Testes automatizados (pytest)
│   ├── test_identity_expansion.py # Lógica de variações de nome
│   ├── test_triangulation.py      # Lógica de cruzamento de achados
│   ├── test_lobby_fara.py         # Parsing LDA/FARA
│   └── fixtures/sample_fec_response.json
│
└── scripts/
    └── run_pipeline.py            # CLI standalone — executa o pipeline completo sem Claude Code
```

---

## Servidores MCP opcionais

O pipeline detecta automaticamente e usa esses servidores MCP quando disponíveis. Sem eles, scripts Python são usados como fallback — cobertura equivalente, mas mais lenta.

### fec-mcp (recomendado para buscas FEC)

Fornece ferramentas `mcp__fec-mcp__*` para acesso direto e estruturado à API da FEC.

Repositório: [github.com/reichaves/fec-mcp-server](https://github.com/reichaves/fec-mcp-server)

```bash
pip install uv
uvx fec-mcp --help   # testar a instalação
```

Já configurado no `.mcp.json`. Quando ativo, a skill `search-fec` opera no **Nível 1** (API estruturada direta) em vez do fallback via script Python.

### osint-investigation

Fornece ferramentas `mcp__osint-investigation__*` para coleta de inteligência de fontes abertas. Usado como fallback secundário quando `fec-mcp` não está disponível.

Repositório: [github.com/reichaves/osint-investigation](https://github.com/reichaves/osint-investigation)

Para confirmar qual nível está ativo, execute:

```
/consultar-base fec "Carlos Eduardo Ferreira"
```

Se a saída disser `Nível 1 — fec-mcp`, o servidor MCP está ativo. Se disser `Nível 3 — script Python`, o servidor não foi detectado.

---

## Limitações conhecidas

Veja `docs/limitations.md` para a lista completa. Resumo:

- Transliteração de nomes brasileiros é imperfeita (Ferreira vs. Ferreirra vs. C. Ferreira) — mitigada mas não eliminada
- Registros corporativos estaduais variam em qualidade e cobertura
- **Florida Sunbiz** retorna HTTP 403 frequentemente em consultas automatizadas — verifique manualmente em [sunbiz.org](https://search.sunbiz.org/) quando o script falhar
- FARA tem atraso de meses entre o registro e a disponibilização pública
- Empresas em Delaware revelam informação mínima publicamente — a sub-skill retorna existência, não o ultimate beneficial owner
- **OpenCorporates** exige chave de API válida; sem ela, todas as buscas retornam HTTP 401. O pipeline documenta a falha e sugere o banco ICIJ Offshore Leaks como alternativa
- Bases de imprensa cobrem veículos brasileiros e americanos indexados publicamente — reportagens pagas ou em arquivos fechados não são acessadas

---

## Ética

Este pipeline foi desenvolvido para investigação de **pessoas com relevância pública**: executivos com contratos governamentais, doadores políticos, agentes estrangeiros, indivíduos envolvidos em crimes reportados ou violações de direitos humanos. Não use para investigar pessoas comuns. Diretrizes completas em `docs/ethics.md`.

---

## Segurança

Este pipeline é uma **ferramenta CLI local** — sem servidor web, sem porta de escuta, sem processo persistente. Propriedades principais:

- Chamadas de rede vão apenas para uma [lista fixa de bases públicas americanas](docs/security-model.md#network-access) (FEC, FARA, OpenCorporates, registros estaduais) — nenhuma URL fornecida pelo usuário é acessada
- Todo output é gravado em `cases/<slug>/` — path traversal é bloqueado pela validação de `_slug()`
- Subprocessos usam `shell=False` (argumentos como lista) — sem vetor de injeção de shell
- Sem `pickle`, `eval` ou `exec` em nenhum lugar do código
- Chaves de API ficam apenas em `.env` — nunca no código-fonte (`.env` e `.mcp.json` estão no `.gitignore`)

Execute os testes de segurança automatizados:

```bash
pytest tests/test_security.py -v
```

Para reportar uma vulnerabilidade de forma privada, veja [`SECURITY.md`](SECURITY.md).
Modelo de confiança completo e checklist de uso seguro: [`docs/security-model.md`](docs/security-model.md).

---

## Citação

Se este pipeline contribuir para uma reportagem ou pesquisa publicada, sugerimos citar:

> Chaves, R. (2026). *Due Diligence Transnacional: pipeline CLI para cruzamento de nomes com vínculos nos EUA em bases públicas americanas*. https://github.com/reichaves/due-diligence-transnacional

---

## Licença

MIT — veja [`LICENSE`](LICENSE).

---

## Autor

**Reinaldo Chaves**
Jornalista de dados no Brasil
[github.com/reichaves](https://github.com/reichaves) · [LinkedIn](https://br.linkedin.com/in/reinaldochaves) · reichaves@gmail.com
