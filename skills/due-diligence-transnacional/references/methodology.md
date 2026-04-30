# Metodologia de Due Diligence Transnacional

## Princípio geral

Este pipeline segue a metodologia de jornalismo investigativo baseada em
fontes primárias públicas. Cada achado deve ser rastreável a uma transação,
registro ou documento específico — nunca a inferência do modelo.

## Ordem de busca recomendada

1. **FEC** — busca mais rápida, resposta via MCP, contexto legal bem definido
2. **LDA** — senate.gov tem API pública; limpar antes de cruzar
3. **FARA** — efile.fara.gov; atraso de publicação de meses é normal
4. **Registros estaduais** — FL primeiro (maior comunidade BR); depois DE, TX
5. **OpenCorporates** — cobertura global, útil para jurisdições menores
6. **Imprensa** — valida achados de bases ou indica pistas não cobertas

## Variações de nome: por que são obrigatórias

Bases americanas foram preenchidas por terceiros (doadores, agentes,
secretárias) que transliteraram nomes brasileiros de forma inconsistente.
Um mesmo "João" pode aparecer como "Joao", "Joã", "John" ou pela inicial
"J.". Sem expandir variações, o pipeline produziria falso-negativo.

Variações mínimas para qualquer nome:
- Nome completo com e sem acentos
- Primeiro nome + último sobrenome
- Última ordem (sobrenome, nome) — padrão de alguns formulários
- Iniciais + último sobrenome
- Sobrenome isolado (busca ampla, ruído alto — verificar manualmente)

## Triangulação

Um achado isolado numa só base vale `indício`. Dois achados independentes
(ex: mesmo endereço na FEC e no Sunbiz) elevam para `provável`. Três ou mais
fontes primárias com dados consistentes chegam a `confirmado`.

A triangulação procura especificamente:
- Mesmo endereço físico ou PO Box
- Mesma data de incorporação ou evento
- Terceiros vinculados (sócios, procuradores) que aparecem em mais de uma base
- Valores monetários próximos com contexto temporal alinhado

## Documentação de ausências

Quando uma base retorna zero resultados:
1. Registrar TODAS as variações testadas
2. Registrar data e hora da consulta
3. Registrar versão da base (se disponível)
4. Anotar contexto legal (ex: 52 U.S.C. § 30121 explica por que brasileiro
   não deve aparecer em FEC)
5. Classificar como `nao-encontrado` — não como "limpo" ou "inocente"

## Limitações estruturais

- Transliteração imperfeita: o pipeline mitiga, não elimina
- Delaware entity search: revela existência, não proprietário
- FARA: atraso de publicação pode ocultar registros recentes
- OpenCorporates: cobertura varia por jurisdição
- Nenhuma das buscas acessa bases pagas (Lexis, Sayari, Refinitiv)

## Revisões humanas obrigatórias

O pipeline impõe duas paradas obrigatórias:

1. **Antes das buscas** — aprovação das variações de identidade: evita
   multiplicar ruído com variações erradas.

2. **Antes do PDF** — aprovação dos achados consolidados: jornalista pode
   remover achados duvidosos, adicionar contexto, ou solicitar nova busca.

Estas paradas não são opcionais. Pular qualquer uma invalida a metodologia.
