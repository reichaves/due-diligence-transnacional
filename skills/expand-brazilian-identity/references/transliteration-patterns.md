# Padrões de Transliteração de Nomes Brasileiros em Bases Americanas

Este documento descreve as transformações mais comuns observadas quando
nomes brasileiros são inseridos em formulários americanos por terceiros
(contadores, secretárias, advogados).

## Substituições de caracteres (diacríticos)

| Caractere BR | Transliteração mais comum | Variações observadas |
|---|---|---|
| ã, Ã | a, A | an (ex: "São" → "Sao" ou "San") |
| â, Â | a, A | — |
| á, Á | a, A | — |
| à, À | a, A | — |
| ä, Ä | a, A | — |
| é, É | e, E | — |
| ê, Ê | e, E | — |
| í, Í | i, I | — |
| ó, Ó | o, O | — |
| ô, Ô | o, O | — |
| õ, Õ | o, O | on (ex: "Leõ" → "Leon") |
| ú, Ú | u, U | — |
| ü, Ü | u, U | — |
| ç, Ç | c, C | ss (ex: "Graça" → "Graca" ou "Grassa") |

## Padrões de ordem de nome

Formulários americanos frequentemente usam a ordem "sobrenome, nome" ou
pedem separadamente "first name" e "last name", causando confusão:

| Nome BR original | Variações em formulários EUA |
|---|---|
| João da Silva | Joao da Silva / Silva Joao / Joao Silva / Da Silva Joao |
| Maria José Santos | Maria Santos / Santos Maria / M.J. Santos / Maria Jose Santos |

## Sobrenomes compostos

Sobrenomes brasileiros compostos são frequentemente truncados ou hifenizados:

| Sobrenome BR | Variações em formulários EUA |
|---|---|
| Andrade Magro | Andrade-Magro / Magro / Andrade |
| da Costa Silva | Da Costa / Costa Silva / Silva / Dacosta |
| de Oliveira | Oliveira / De Oliveira / DeOliveira |

## Preposições e artigos

Preposições como "da", "de", "do", "dos", "das" são frequentemente:
- Omitidas: "Ana de Lima" → "Ana Lima"
- Capitalizadas: "De Lima" (início de formulário)
- Incorporadas ao sobrenome: "DeLima" ou "Delima"

## Nomes comuns com americanização

Alguns jornalistas ou assessores optam por americanizar o nome do cliente:

| Nome BR | Versão americanizada |
|---|---|
| João | John |
| José | Joe / Joseph |
| Maria | Mary |
| Paulo | Paul |
| Luís / Luiz | Louis / Lewis |
| Pedro | Peter |
| Ricardo | Richard / Rick |
| Carlos | Charles / Chuck |
| Eduardo | Edward / Ed |

**Atenção:** americanizações devem ser incluídas como variações `alias`
somente se houver evidência de que o alvo usa essa versão — não presumir.

## Padrões de iniciação em EUA

Abreviações de nome médio são comuns em documentos americanos:

- "Ricardo Andrade Magro" → "Ricardo A. Magro" → "R. A. Magro" → "R. Magro"
- FEC e FARA frequentemente usam "first + initial + last"

## Erros tipográficos frequentes

Erros documentados em bases reais (observados em FEC Schedule A):

| Original | Erro tipográfico |
|---|---|
| Magro | Maggro / Margo / Magrao |
| Souza | Sousa / Souza / Soza |
| Pereira | Perreria / Perreira |
| Gonçalves | Goncalves / Gonczalves |

**Nota:** o pipeline não gera variações com erros tipográficos
automaticamente — incluir manualmente se houver evidência de que o erro
já ocorreu em alguma base.
