# Guia de Campos FEC — Schedule A (Contributions)

## O que é o Schedule A

O Schedule A é o formulário de disclosure de **recebimentos** de um comitê
político federal americano. Todo doador individual que contribuir com mais
de USD 200 a um comitê deve ter nome, endereço, empregador e ocupação
divulgados publicamente.

## Campos principais

| Campo FEC                     | Descrição                                               |
|-------------------------------|---------------------------------------------------------|
| `transaction_id`              | ID único da transação — usar como `source_id`           |
| `contributor_name`            | Nome do doador (SOBRENOME, NOME MIDDLE)                 |
| `contributor_first_name`      | Primeiro nome                                           |
| `contributor_last_name`       | Sobrenome                                               |
| `contributor_middle_name`     | Nome do meio                                            |
| `contributor_prefix`          | Prefixo (Mr., Ms., Dr. etc.)                            |
| `contributor_suffix`          | Sufixo (Jr., III etc.)                                  |
| `contributor_street_1`        | Endereço linha 1 — PII, redija quando irrelevante       |
| `contributor_city`            | Cidade                                                  |
| `contributor_state`           | UF (2 letras)                                           |
| `contributor_zip`             | CEP americano                                           |
| `contributor_employer`        | Empregador declarado pelo doador                        |
| `contributor_occupation`      | Ocupação declarada                                      |
| `contribution_receipt_date`   | Data da contribuição (YYYY-MM-DD)                       |
| `contribution_receipt_amount` | Valor em USD                                            |
| `committee_id`                | ID do comitê receptor (começa com C)                   |
| `committee_name`              | Nome do comitê receptor                                 |
| `candidate_id`                | ID do candidato (começa com P, H ou S)                 |
| `candidate_name`              | Nome do candidato                                       |
| `entity_type`                 | IND (individual), ORG (organização) etc.                |
| `is_individual`               | True/false                                              |
| `two_year_transaction_period` | Ciclo eleitoral (ex: 2024)                              |
| `filing_id`                   | ID do filing que contém esta transação                  |
| `image_number`                | Número da imagem do documento original                  |
| `line_number`                 | Linha no formulário FEC                                 |
| `memo_code`                   | M = memoized (não conta para limite), vazio = real      |
| `memo_text`                   | Nota livre do comitê                                    |

## Tipos de comitê (committee_type)

| Código | Tipo                                   |
|--------|----------------------------------------|
| P      | Presidential                           |
| H      | House                                  |
| S      | Senate                                 |
| D      | Delegate Committee                     |
| E      | Electioneering Communication           |
| I      | Independent Expenditure (PAC)          |
| N      | PAC - Nonqualified                     |
| Q      | PAC - Qualified                        |
| U      | Single Candidate Independent Expend.   |
| V      | PAC with Non-Contribution Account      |
| W      | PAC with Non-Contribution Account      |
| X      | Party - Nonqualified                   |
| Y      | Party - Qualified                      |
| Z      | National Party Nonfederal Account      |

## URL canônica de uma transação

```
https://www.fec.gov/data/receipts/?two_year_transaction_period=XXXX&transaction_id=<transaction_id>
```

## Limites de contribuição (ciclo 2025-2026)

| Tipo de doação                    | Limite individual por ciclo |
|-----------------------------------|-----------------------------|
| Para candidato federal (primária) | USD 3.300                   |
| Para candidato federal (geral)    | USD 3.300                   |
| Para national party committee     | USD 41.300/ano              |
| Para PAC (não Super PAC)          | USD 5.000/ano               |
| Super PAC                         | Sem limite (independente)   |

## Como a FEC retorna nomes brasileiros

Nomes brasileiros são tipicamente inseridos em ordem americana:
**SOBRENOME, NOME PRENOME** (ex: `MAGRO, RICARDO ANDRADE`).

Variações comuns de inserção incorreta:
- Sem acento: `MAGRO, RICARDO ANDRADE` em vez de `MAGRO, RICARDO ÂNDRADE`
- Sobrenome composto separado: `ANDRADE, RICARDO MAGRO`
- Apelido no lugar do nome: `MAGRO, RICK`

Por isso a expansão de variações é obrigatória antes da busca.
