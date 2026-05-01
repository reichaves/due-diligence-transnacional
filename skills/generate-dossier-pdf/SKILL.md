---
name: generate-dossier-pdf
description: >
  Gera o dossiê final em PDF a partir de findings-consolidated.json e
  target.yaml. Usa ReportLab para produzir um documento estruturado com
  capa, resumo executivo, metodologia, achados por base com fonte e nível
  de confiança, triangulações, lacunas, contexto legal e apêndice de
  timestamps. Acionar como último estágio do pipeline, após revisão humana
  dos achados consolidados.
---

# Geração de Dossiê PDF

## Quando ativar

- Estágio 5 do pipeline: após revisão humana do `findings-consolidated.json`.
- Quando o usuário pedir: "/gerar-dossie", "gera o PDF", "exporta o relatório".

## Inputs

| Arquivo                    | Obrigatório | Descrição                                 |
|----------------------------|-------------|-------------------------------------------|
| `findings-consolidated.json` | Sim       | Output do triangulate-findings            |
| `target.yaml`              | Sim         | Contexto do alvo (nome, razão, parentes)  |
| `identity-variations.json` | Não         | Para apêndice de variações buscadas       |

## Estrutura do dossiê

### Página 1 — Capa
- Título: "DOSSIÊ DE DUE DILIGENCE"
- Nome do alvo (centralizado, destaque)
- Data de geração
- Aviso: "DOCUMENTO CONFIDENCIAL — USO JORNALÍSTICO"
- Rodapé: "Gerado por due-diligence-transnacional pipeline"

### Seção 1 — Resumo Executivo
Parágrafo de 3-5 linhas sintetizando os achados de maior confiança.
Gerado pelo modelo a partir dos `high_confidence_flags` e
triangulações. Sem adjetivação especulativa — apenas fatos com fonte.

### Seção 2 — Metodologia
- Bases consultadas
- Número de variações de nome testadas
- Data e hora de cada consulta
- Ferramentas utilizadas (MCP fec-finance, scraping sunbiz, etc.)

### Seção 3 — Variações de Identidade Buscadas
Tabela com todas as variações, tipo e nota (se identity-variations.json
disponível), ou lista do `no_hits` agregado.

### Seção 4 — Achados por Base
Para cada base com hits, uma subseção com:
- Nome da base e URL oficial
- Tabela de hits: campo | valor
- Fonte explícita: `(Fonte: <base>, ID <source_id>, consultado em <data>)`
- Nível de confiança: badge colorido (`confirmado` / `provável` / `indício`)
- Para bases sem hits: "Não encontrado — [variações testadas]"

### Seção 5 — Triangulações
Tabela de cruzamentos com: tipo | bases envolvidas | detalhe | confiança.

### Seção 6 — Lacunas e Próximas Frentes
Lista de lacunas identificadas com sugestão de ação manual.

### Seção 7 — Contexto Legal Aplicável
Resumo dos contextos legais relevantes agregados das sub-skills.

### Apêndice — Timestamps de Consulta
Tabela completa: base | timestamp | queries executadas | status.

## Padrões editoriais no PDF

- Sem cores chamativas: preto/cinza, máximo um azul escuro para cabeçalhos.
- Fonte serifada (Times-Roman) para corpo do texto.
- Fonte sem serifa (Helvetica) para labels, badges e tabelas.
- Margens de 2,5 cm (standard jornalístico).
- Numeração de página no rodapé.
- Sem emojis, sem exclamação, sem adjetivação especulativa.

## Anti-alucinação

O script `generate_report.py` **nunca gera texto livre** para os achados —
apenas formata o que está no JSON. O único trecho gerado pelo modelo é o
"Resumo Executivo", que deve ser baseado exclusivamente nos
`high_confidence_flags` do JSON de entrada.

## Script CLI

```bash
python skills/generate-dossier-pdf/scripts/generate_report.py \
    --consolidated examples/case-fictional/findings.json \
    --target examples/case-fictional/target.yaml \
    --output examples/case-fictional/dossier.pdf
```

## Template

`templates/dossier_template.py` — contém estilos ReportLab reutilizáveis
e funções de formatação. Importe em `generate_report.py`.

## Referências

- `schemas/findings-consolidated.schema.json`
- `skills/due-diligence-transnacional/references/confidence-levels.md`
