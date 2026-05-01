# LDA e FARA — Contexto Legal para Investigações Transnacionais

## 1. LDA — Lobbying Disclosure Act (2 U.S.C. § 1601 et seq.)

### O que regula

Lobbistas e organizações que fazem **contato com funcionários do Congresso
ou do Poder Executivo** em nome de clientes, em relação a legislação federal,
regulamentação, licenças ou contratos.

### Quem deve se registrar

Uma pessoa deve se registrar como lobbista se:

1. Fazer **2 ou mais contatos de lobby** em 3 meses; E
2. Gastar **≥ 20% do tempo** em atividades de lobby em 3 meses; E
3. A organização que o contratou pagar **≥ USD 3.000** em honorários no trimestre

### Disclosure semestral (LD-2)

A cada 6 meses, os registrantes devem reportar:
- Rendimentos recebidos de cada cliente
- Gastos estimados de lobby
- Questões legislativas/regulatórias trabalhadas
- Branches do governo contatados
- Nomes de cada lobbista que fez contatos

### Onde buscar

- Base: https://lda.senate.gov/
- API REST: https://lda.senate.gov/api/v1/ (sem autenticação para buscas básicas)
- Download anual: https://lda.senate.gov/api/v1/filings/?format=json

### Campos relevantes para investigação

| Campo             | Descrição                                          |
|-------------------|----------------------------------------------------|
| `filing_uuid`     | ID único do filing — usar como `source_id`         |
| `registrant_name` | Nome da empresa de lobby                           |
| `client_name`     | Quem está pagando o lobby                          |
| `lobbyist_name`   | Nome do lobbista individual                        |
| `income`          | Honorários recebidos (USD)                         |
| `expenses`        | Gastos totais declarados (USD)                     |
| `general_issue_area_code` | Área de atuação (ex: ENG=Energia, TAX=Tributação) |
| `period_of_performance`   | Período coberto                          |

### Conexão com Brasil

Empresas brasileiras que contratam lobbistas americanos aparecem como
`client_name`. Exemplos de setores com histórico de lobby por empresas BR:
- Siderurgia e alumínio (tarifas de importação)
- Aviação civil (slots em aeroportos americanos)
- Petróleo e gás (regulação do pré-sal)
- Agronegócio (acesso ao mercado americano)

---

## 2. FARA — Foreign Agents Registration Act (22 U.S.C. § 611 et seq.)

### O que regula

Pessoas ou organizações que atuam como **agentes de principal estrangeiro**
(*foreign principal*) em atividades políticas, de relações públicas, ou que
tentam influenciar funcionários públicos americanos ou a opinião pública.

### Diferença crítica em relação ao LDA

| Aspecto          | LDA                           | FARA                                    |
|------------------|-------------------------------|------------------------------------------|
| Foco             | Lobby legislativo/executivo   | Influência política estrangeira          |
| Principal        | Qualquer cliente              | Entidade ou governo estrangeiro          |
| Atividades       | Contato direto com governo    | Inclui mídia, RP, consultoria            |
| Administrado por | Senate/House                  | DOJ (Departamento de Justiça)            |
| Penalidade       | Multa civil                   | Até 5 anos de prisão (criminal)          |

### Quem deve se registrar

Qualquer pessoa que:
1. Atua como agente, representante ou consultor de uma entidade ou governo estrangeiro; E
2. Engaja em atividades políticas, de lobby ou de relações públicas nos EUA

**Isenções:** advogados em procedimentos legais, atividades religiosas,
atividades acadêmicas, ou jornalistas credenciados por mídia estrangeira.

### Onde buscar

- Base: https://www.fara.gov/
- eFile: https://efile.fara.gov/
- API: https://efile.fara.gov/api/v1/
- Registros físicos pré-2008: disponíveis via FOIA ao DOJ

### Campos relevantes

| Campo                      | Descrição                                       |
|----------------------------|-------------------------------------------------|
| `registration_number`      | ID único do agente registrado — `source_id`     |
| `registrant_name`          | Nome do agente (pessoa ou empresa)              |
| `foreign_principal`        | Nome do principal estrangeiro                   |
| `foreign_principal_country`| País do principal                               |
| `registration_date`        | Data do registro inicial                        |
| `termination_date`         | Data de encerramento (null = ativo)             |
| `activity_description`     | Descrição das atividades exercidas              |

### Atraso de disponibilização

FARA tem histórico de atrasos entre o prazo legal de registro (dentro de
48h de início das atividades) e a disponibilização pública no eFile.
Casos investigados pelo DOJ revelaram atrasos de meses. Sempre registrar
em `methodology_note` que a ausência no eFile não exclui registro tardio.

### Violações notáveis com conexão Brasil/América Latina

- Caso Odebrecht: empresas de RP americanas registradas como agentes para
  projetos da empreiteira no Peru, Panamá e Venezuela (2010-2018)
- Caso Manafort/Gates: ex-campaign manager de Trump registrado retroativamente
  por lobby em nome do governo ucraniano (2017)

---

## 3. Interação entre LDA e FARA

Uma atividade pode ser coberta por ambas as leis ou apenas por uma.

- Se cliente é americano mas com funding estrangeiro → pode acionar FARA
- Se contato é com Congresso sobre legislação → aciona LDA
- Se atividade é de RP/mídia para governo estrangeiro → aciona FARA

Agentes podem se registrar como isentos de FARA se já registrados no LDA
(*LDA exemption*), mas o DOJ tem restringido essa isenção desde 2017.

---

## Fontes

- LDA: https://lda.senate.gov/
- FARA: https://www.justice.gov/nsd-fara
- FARA Guide (DOJ): https://www.justice.gov/nsd-fara/frequently-asked-questions
- LDA Guide (Senate): https://lobbyingdisclosure.house.gov/ldaguid.html
