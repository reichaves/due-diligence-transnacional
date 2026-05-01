# Contexto Legal — Bases Americanas

Este documento descreve o contexto legal aplicável às buscas executadas
pelo pipeline. Conhecer essas leis é parte da metodologia — ausência de
registro em uma base pode ser o resultado legalmente esperado, não um
achado negativo.

---

## 1. FEC — 52 U.S.C. § 30121

### A proibição

**52 U.S.C. § 30121(a)(1)** (anteriormente 2 U.S.C. § 441e) proíbe que
qualquer **nacional estrangeiro** (*foreign national*) faça:

- Contribuição ou doação a comitê de partido político (federal, estadual ou local)
- Contribuição a candidato federal, estadual ou local
- Gasto em conexão com qualquer eleição americana
- Contribuição a comitê de ação política (PAC)

**§ 30121(a)(2)** proíbe que cidadãos americanos **solicitem ou aceitem**
contribuições de nacionais estrangeiros.

### Quem é "nacional estrangeiro"

São *foreign nationals*:
- Cidadãos de outros países **sem** residência permanente legal (green card)
- Estrangeiros com qualquer categoria de visto temporário (F-1, H-1B, B-1/B-2, etc.)
- Entidades corporativas organizadas sob lei estrangeira
- Entidades com controle estrangeiro majoritário

**Não são** *foreign nationals*:
- Portadores de green card (podem contribuir como residentes legais)
- Cidadãos naturalizados americanos (podem contribuir como qualquer cidadão)

### Implicação para investigações de brasileiros

**Ausência no FEC para cidadão brasileiro sem green card é o resultado
esperado e legalmente coerente.** O achado investigativo surge quando:

1. O brasileiro tem green card ou cidadania americana mas não há registro
   → pode ser relevante se ele deveria ter contribuído a um candidato
2. O brasileiro não poderia contribuir mas há registro → violação potencial
3. Empresa americana controlada por brasileiro fez contribuições → verificar
   a exceção de "entidade doméstica" abaixo

### Exceção: entidades domésticas

Empresas constituídas nos EUA (mesmo com controle estrangeiro) **podem**
contribuir para PACs e party committees desde que:
- Os fundos usados sejam de operações americanas (não de remessas estrangeiras)
- A decisão de contribuir não seja tomada pelo sócio estrangeiro

Esta "regra da separação" permite que holding americana de grupo brasileiro
finance atividade política — o que torna o rastreamento de empresas
americanas ligadas a brasileiros especialmente relevante.

### Penalidades

- FEC: multas civis (geralmente % do valor indevido)
- DOJ: processo criminal para violações > USD 25.000
- Pena máxima: 2 anos de prisão

### Fontes

- Texto completo: https://uscode.house.gov (título 52, seção 30121)
- FEC Advisory Opinion 2019-12 (entidades domésticas com controle estrangeiro)

---

## 2. LDA — Lobbying Disclosure Act (2 U.S.C. § 1601 et seq.)

### O que regula

Lobbistas e organizações que fazem **contato direto com funcionários do
Congresso ou do Poder Executivo** em nome de clientes, em relação a
legislação federal, regulamentação, licenças ou contratos.

### Gatilho de registro

Uma pessoa deve se registrar se simultaneamente:
1. Fizer 2 ou mais *lobbying contacts* em período de 3 meses; E
2. Gastar ≥ 20% do tempo em atividades de lobby; E
3. A organização pagante gastar ≥ USD 3.000 em lobby no trimestre

### Disclosure semestral (formulário LD-2)

A cada 6 meses, os registrantes reportam:
- Rendimentos recebidos por cliente
- Gastos estimados de lobby
- Questões legislativas/regulatórias trabalhadas
- Branches do governo contatados
- Nomes dos lobbistas que fizeram contatos

### Onde buscar

- Base: https://lda.senate.gov/
- API pública: https://lda.senate.gov/api/v1/

### Conexão com Brasil

Empresas brasileiras que contratam lobbistas americanos aparecem como
`client_name`. Setores com histórico:
- Siderurgia e alumínio (tarifas de importação)
- Aviação civil (slots em aeroportos americanos)
- Petróleo e gás (regulação do pré-sal)
- Agronegócio (acesso ao mercado americano, certificações fitossanitárias)

---

## 3. FARA — Foreign Agents Registration Act (22 U.S.C. § 611 et seq.)

### O que regula

Pessoas ou organizações que atuam como **agentes de principal estrangeiro**
em atividades políticas, de relações públicas, ou que influenciam funcionários
públicos americanos ou a opinião pública americana.

### Diferença crítica em relação ao LDA

| Aspecto        | LDA                         | FARA                                   |
|----------------|-----------------------------|----------------------------------------|
| Foco           | Lobby legislativo/executivo | Influência política estrangeira        |
| Principal      | Qualquer cliente            | Entidade ou governo estrangeiro        |
| Atividades     | Contato direto com governo  | Inclui mídia, RP, consultoria política |
| Administrado   | Senate/House                | DOJ — Departamento de Justiça          |
| Penalidade     | Multa civil                 | Até 5 anos de prisão (criminal)        |

### Atraso de disponibilização

FARA tem histórico de atrasos entre o registro legal (prazo: 48h do início
das atividades) e a disponibilização pública no eFile. Casos investigados
pelo DOJ revelaram atrasos de meses. Ausência no eFile não exclui registro
tardio — sempre documentar esta limitação no dossiê.

### Onde buscar

- Base: https://www.fara.gov/
- eFile: https://efile.fara.gov/
- Registros pré-2008: via FOIA ao DOJ

### Isenção LDA

Agentes podem requerer isenção de FARA se já registrados no LDA. O DOJ
tem restringido essa isenção desde 2017 — verificar se o registro LDA
cobre as atividades ou se FARA é necessário independentemente.

---

## 4. Sunshine Laws estaduais — registros corporativos

### Florida — Sunbiz.org

Flórida tem uma das leis de divulgação corporativa mais abrangentes dos EUA.
O Sunbiz (Division of Corporations) disponibiliza:
- Nome e endereço de todos os officers e registered agents
- Histórico de filings anuais
- Datas de incorporação e dissolução
- Documentos de constituição (Articles of Incorporation)

Acesso: https://search.sunbiz.org/ — gratuito, sem autenticação.

**Lei de referência:** Florida Statutes, Chapter 607 (corporations) e
Chapter 605 (LLCs).

### Delaware — Division of Corporations

Delaware tem as leis de privacidade corporativa **mais permissivas** dos EUA.
A busca pública revela apenas:
- Nome da entidade
- Data de incorporação
- Registered agent (geralmente uma empresa fiduciária, não o proprietário real)
- Status (ativo/dissolvido)

**O que Delaware NÃO revela publicamente:** nomes de sócios, beneficiários
finais (beneficial owners), ou diretores.

Para obter informações de proprietários de Delaware, é necessário:
1. Registro FinCEN (Beneficial Ownership Information) — acessível apenas
   para autoridades e com processo judicial
2. FOIA para documentos contratuais quando há envolvimento federal

**Lei de referência:** Delaware General Corporation Law (Title 8, Chapter 1).

### Texas — Comptroller of Public Accounts

Texas exige que empresas estrangeiras registradas no estado informem:
- Officers e diretores
- Registered agent no Texas
- SIC code (setor de atividade)
- Endereço principal

Busca: https://mycpa.cpa.state.tx.us/coa/

**Lei de referência:** Texas Business Organizations Code, Title 1.

---

## 5. OpenCorporates — cobertura e limitações

OpenCorporates agrega dados de registros corporativos de +140 jurisdições.
Para fins deste pipeline, é útil para:
- Confirmar registros já encontrados em bases estaduais
- Identificar empresas em jurisdições não cobertas diretamente (Nevada, Wyoming, etc.)
- Registrar officers que aparecem em múltiplas jurisdições

**Limitações:**
- Qualidade varia por jurisdição — algumas fontes têm atraso de meses
- Não cobre beneficiários finais onde a legislação local não exige disclosure
- Dados de officer podem estar desatualizados se a empresa não atualizar filings

---

## 6. Resumo: o que cada lei exige vs. o que o pipeline busca

| Lei/Base       | O pipeline busca               | Ausência significa          |
|----------------|--------------------------------|------------------------------|
| 52 U.S.C. § 30121 (FEC) | Contribuições eleitorais  | Normal para brasileiro sem green card |
| LDA            | Lobby em nome do alvo ou de empresa vinculada | Não há atividade de lobby registrada |
| FARA           | Registro como agente estrangeiro | Não registrado — pode ter atraso |
| Sunbiz (FL)    | Empresas onde o alvo é officer | Nenhuma empresa ativa em FL  |
| DE-CORPS       | Existência de empresa em Delaware | Sem holding DE documentada |
| TX-COMPTROLLER | Empresas registradas no Texas  | Sem presença corporativa TX  |

---

## Aviso de atualização

As leis e bases descritas neste documento estão corretas na data de
publicação (maio de 2026). Leis tributárias e de registro corporativo mudam
com frequência. Antes de usar este pipeline para uma reportagem publicável,
verifique se há alterações legais relevantes.
