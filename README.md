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
uv sync
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
python scripts/run_pipeline.py --target examples/case-fictional/target.yaml
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
