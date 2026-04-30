# Escala de Níveis de Confiança

Esta escala deve ser aplicada a cada afirmação individual no dossiê.
Não existe nível "suspeito" ou "provado" — apenas os quatro abaixo.

## confirmado

**Critério:** duas ou mais fontes primárias independentes concordam com
a mesma informação, sem ambiguidade de identidade.

**Exemplo:** nome "Ricardo Magro" aparece como officer no Sunbiz (FL)
E como contribuinte no FEC Schedule A, ambos com mesmo endereço em Miami.

**No dossiê:** afirmação direta. Cite ambas as fontes.

---

## provavel

**Critério:** uma fonte primária com dado sólido, mais evidência
circunstancial de suporte (sem contradição).

**Exemplo:** empresa "Refit USA LLC" listada no Sunbiz com officer "R.
Magro" — sem confirmação de que é o mesmo Ricardo Magro investigado,
mas contexto de negócios bate com o alvo.

**No dossiê:** "É provável que..." seguido de citação da fonte e da
evidência circunstancial. Indicar o que faltou para chegar a `confirmado`.

---

## indicio

**Critério:** dado circunstancial sem fonte primária que confirme
diretamente. Pode ser cruzamento de imprensa, menção secundária, ou
achado em base com dados incompletos.

**Exemplo:** artigo de jornal menciona "Ricardo Magro" como sócio de
empresa em Houston, mas não há registro estadual confirmando.

**No dossiê:** "Há indício de..." seguido de fonte e limitação explícita.
Sempre recomendar investigação adicional para confirmar.

---

## nao-encontrado

**Critério:** busca executada corretamente, todas as variações testadas,
base acessível — e nenhum resultado retornado.

**Exemplo:** FEC Schedule A buscado com 12 variações do nome entre
2004–2024, zero hits.

**No dossiê:** "Não encontrado em [BASE] após consulta de [N] variações
em [DATA]." Se houver contexto legal que explique a ausência (ex:
§ 30121), citá-lo.

**Importante:** `nao-encontrado` não significa "inocente" ou "limpo".
Significa que o pipeline não localizou rastro nesta base com esta metodologia.

---

## Regras de aplicação

- Nunca eleve um nível sem evidência adicional. `indicio` só vira `provavel`
  com nova fonte primária — não com inferência do modelo.
- Quando dois achados se contradizem, use o nível mais baixo e documente
  a contradição.
- O nível de confiança é da **afirmação específica**, não do alvo como um todo.
  O mesmo dossiê pode ter um achado `confirmado` e dez `nao-encontrado`.
- Em caso de dúvida, use `indicio`. É melhor subestimar do que superestimar.
