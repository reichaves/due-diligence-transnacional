---
name: search-news-archive
description: >
  Busca cobertura jornalística de uma pessoa brasileira em outlets confiáveis
  do Brasil e dos EUA. Usa web search com filtros de site para outlets
  curados em `references/trusted-outlets.md`. Use quando o orquestrador
  `due-diligence-transnacional` solicitar, ou quando o usuário pedir
  "/consultar-base news NOME". Retorna links de matérias com resumo e
  classificação de relevância. Nunca inventa cobertura — se não encontrar,
  registra explicitamente.
---

# Busca em Arquivo de Imprensa

## Inputs

- `identity-variations.json` (obrigatório)
- `outlet_filter` (opcional) — `"BR"`, `"US"`, ou `"both"` (default: `"both"`)
- `date_range` (opcional) — `{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}`
- `topic_keywords` (opcional) — lista de termos para combinar com o nome

## Ferramentas disponíveis

- Web search (integrado ao Claude Code)
- Web fetch para recuperar texto de matérias específicas

## Outlets cobertos

Ver lista completa em `references/trusted-outlets.md`.

**Brasil (amostra):**
- Folha de S.Paulo (folha.com.br)
- O Estado de S. Paulo (estadao.com.br)
- O Globo (oglobo.globo.com)
- The Intercept Brasil (theintercept.com/brasil)
- Agência Pública (agenciapublica.org.br)
- Piauí (piaui.folha.uol.com.br)
- Agência Brasil (agenciabrasil.ebc.com.br)
- UOL (uol.com.br)
- G1 (g1.globo.com)
- Metrópoles (metropoles.com)

**EUA (amostra):**
- ProPublica (propublica.org)
- Reuters (reuters.com)
- The New York Times (nytimes.com)
- The Washington Post (washingtonpost.com)
- Bloomberg (bloomberg.com)
- Miami Herald (miamiherald.com)
- The Guardian US (theguardian.com)
- OCCRP (occrp.org)

## Procedimento

### 1. Construir queries de busca

Para cada variação de nome, construir query no formato:
```
"<variação>" site:<outlet>
```

Combinar com topic keywords quando fornecidos:
```
"<variação>" (<keyword1> OR <keyword2>) site:<outlet>
```

Limitar a **top 3 outlets BR + top 3 outlets EUA** por variação para
não estourar cota de web search. Priorizar outlets de maior cobertura
investigativa (Pública, Intercept, ProPublica, OCCRP, Reuters).

### 2. Processar resultados

Para cada matéria encontrada:
- URL completa
- Título exato como aparece no resultado
- Data de publicação (se disponível no snippet)
- Outlet
- Snippet/resumo (dos primeiros 300 caracteres úteis)
- Relevância: `"alta"` (nome é sujeito principal), `"media"` (nome mencionado), `"baixa"` (referência passageira)

### 3. Verificação de acesso

Se matéria estiver atrás de paywall:
- Registrar URL e título
- Marcar `"paywall": true`
- Sugerir em `next_frontiers`: "Acessar via biblioteca ou contato com redação"

### 4. Busca em buscadores de investigação

Além dos outlets individualmente, executar:
- Busca OCCRP: `"<variação>" site:occrp.org`
- Busca ICIJ (Panama Papers, Pandora Papers): `"<variação>" site:icij.org`
- Busca OpenSecrets: `"<variação>" site:opensecrets.org`

## Output

`findings/news-br.json` e `findings/news-us.json` conforme
`schemas/findings.schema.json`.

Campo `source_id` = URL da matéria (identificador único).

```json
{
  "base": "NEWS-BR",
  "consulted_at": "2026-04-30T14:30:00-03:00",
  "queries_executed": 24,
  "status": "ok",
  "hits": [
    {
      "variation_matched": "Ricardo Magro",
      "match_type": "exact",
      "source_id": "https://agenciapublica.org.br/noticia/exemplo/",
      "source_url": "https://agenciapublica.org.br/noticia/exemplo/",
      "confidence": "confirmado",
      "raw_record": {
        "title": "Grupo Refit aparece em contrato milionário com Petrobras",
        "outlet": "Agência Pública",
        "date": "2024-11-15",
        "snippet": "Ricardo Magro, sócio do Grupo Refit...",
        "paywall": false,
        "relevance": "alta"
      }
    }
  ],
  "no_hits": ["Ricardo Andrade Magro", "R. Magro"],
  "methodology_note": "Busca limitada a outlets listados em references/trusted-outlets.md. Não cobre imprensa local ou portais não-curados."
}
```

## Regras anti-alucinação

- NUNCA resumir conteúdo de matéria sem ter acessado o texto via web fetch.
- Se o snippet for ambíguo (pode ser outra pessoa com nome similar), marcar
  `confidence: "indicio"` e registrar nota.
- Não afirmar que matéria existe com base em URL não verificada.
- Paywall = registrar, não ignorar.

## Referências

- `references/trusted-outlets.md` — lista curada de outlets confiáveis BR+EUA
