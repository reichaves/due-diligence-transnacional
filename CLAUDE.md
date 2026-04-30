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
- Datas no padrão DD/MM/AAAA (português) ou MM/DD/AAAA (inglês) se a
  pergunta for em inglês.
- Valores em USD com paridade BRL aproximada quando relevante. Sempre
  mostrar o valor em USD primeiro.

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
