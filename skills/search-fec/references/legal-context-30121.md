# Contexto Legal — 52 U.S.C. § 30121 (antes: 2 U.S.C. § 441e)

## Texto da proibição (resumo)

**52 U.S.C. § 30121(a)(1)** proíbe que qualquer **nacional estrangeiro**
(*foreign national*) faça:

- Contribuição ou doação a qualquer comitê de partido político federal, estadual ou local
- Contribuição ou doação para campanha de candidato federal, estadual ou local
- Gasto (*expenditure*) em conexão com eleição federal, estadual ou local
- Contribuição a comitê de ação política (PAC)
- Qualquer combinação das anteriores

**§ 30121(a)(2)** proíbe que cidadãos americanos ou residentes permanentes
**solicitem, aceitem ou recebam** contribuições de nacionais estrangeiros.

## Quem é "nacional estrangeiro"

São *foreign nationals* sob a lei americana:

- Cidadãos de outros países **sem** residência permanente legal (*green card*)
- Estrangeiros com visto de não-imigrante (turistas, estudantes F-1, trabalhadores H-1B etc.)
- Entidades corporativas organizadas sob lei estrangeira
- Entidades com controle estrangeiro majoritário

**NÃO são** *foreign nationals*:

- Portadores de green card (residentes permanentes legais) — podem contribuir
- Cidadãos naturalizados americanos — podem contribuir como qualquer americano

## Implicação para investigações sobre brasileiros

**Ausência de hit no FEC para cidadão brasileiro sem green card é o resultado
esperado e legalmente coerente.** Não é um achado negativo — é o resultado
previsto pela lei.

O achado investigativo surge quando:

1. O brasileiro **tem** green card ou cidadania americana mas não há
   registro de contribuição → pode ser relevant se ele deveria ter registrado
2. O brasileiro **não deveria** poder contribuir mas há registro de
   contribuição → violação potencial de § 30121
3. Há contribuição de empresa americana controlada por brasileiro → ver
   exceção de entidade doméstica abaixo

## Exceção importante: entidades domésticas

Empresas **constituídas nos EUA** (mesmo que controladas por estrangeiro)
**podem** contribuir para PACs e party committees, desde que:
- Os fundos usados nas contribuições não sejam de origem estrangeira
- A decisão de fazer a contribuição não seja tomada pelo sócio estrangeiro

Esta é a "regra da separação" — permite que holding americana de grupo
brasileiro financie atividade política, desde que o dinheiro seja de
operações americanas e o sócio brasileiro não tome a decisão.

## Multas e enforcement

- FEC investiga reclamações; DOJ processa criminalmente casos graves
- Pena máxima: 2 anos de prisão + multa se violação > USD 25.000
- Casos recentes: Lev Parnas (2019), iHeartMedia/San Antonio (2012)

## O que registrar no findings quando não há hit

```json
{
  "legal_context": [
    "52 U.S.C. § 30121 proíbe nacionais estrangeiros sem residência permanente de contribuir a campanhas americanas. Ausência de hits é resultado esperado para cidadão brasileiro.",
    "Exceção: entidade doméstica (empresa constituída nos EUA) pode contribuir se fundos forem de origem americana e decisão não for do sócio estrangeiro — investigar se o alvo possui empresa americana operante."
  ]
}
```

## Fontes

- Texto completo: https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title52-section30121
- FEC Advisory Opinion 2019-12 (entidades domésticas com controle estrangeiro)
- DOJ FARA Unit: https://www.justice.gov/nsd-fara
