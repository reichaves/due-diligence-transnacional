# Catálogo de Fontes — Due Diligence Transnacional

Descrição de cada base de dados usada pelo pipeline: URL, tipo de acesso,
cobertura, frequência de atualização e limitações conhecidas.

---

## 1. FEC — Federal Election Commission

| Campo            | Detalhe                                              |
|------------------|------------------------------------------------------|
| URL              | https://api.open.fec.gov/                            |
| Tipo de acesso   | API REST (chave gratuita em api.data.gov)            |
| Cobertura        | Contribuições eleitorais federais desde 1979         |
| Atualização      | Diária (filings processados no dia seguinte)         |
| Autenticação     | API key obrigatória (`FEC_API_KEY`)                  |
| Rate limit       | 1.000 req/hora (plano gratuito)                      |
| MCP disponível   | Sim — `fec-mcp` (configurado em `.mcp.json`)         |

### O que o pipeline busca

Schedule A (contribuições a candidatos e comitês): nome do contribuinte,
empregador, ocupação, valor, data, comitê destinatário.

### Cobertura de formulários consultados

- Schedule A: contribuições individuais recebidas
- Schedule E: gastos independentes por PACs e Super PACs

### Limitações

- Nomes de contribuintes são inseridos manualmente pelos comitês —
  transliteração inconsistente é comum
- Threshold de reporte: contribuições < USD 200 não precisam de nome
  completo do contribuinte (apenas total acumulado)
- Eleições estaduais e locais estão em bancos estaduais separados
  (este pipeline não os cobre)

---

## 2. LDA — Senate Lobbying Disclosure Database

| Campo            | Detalhe                                               |
|------------------|-------------------------------------------------------|
| URL              | https://lda.senate.gov/                               |
| Tipo de acesso   | API REST pública (sem autenticação)                   |
| Cobertura        | Registros desde 1998 (implementação da LDA de 1995)   |
| Atualização      | Semestral (períodos: Jan-Jun e Jul-Dez)               |
| Autenticação     | Não necessária para buscas                            |
| Rate limit       | Não documentado; respeitar 1 req/segundo              |

### O que o pipeline busca

Filings LD-2: registrante (empresa de lobby), cliente, lobbistas nomeados,
honorários declarados, issues trabalhadas, branches do governo contatados.

### Limitações

- Disclosure semestral: dados têm até 6 meses de defasagem
- Threshold de registro: lobby abaixo de USD 3.000/trimestre não aparece
- Empresas que cancelam registro antes do filing não aparecem
- Nomes de clientes estrangeiros podem estar em formas abreviadas ou em inglês

---

## 3. FARA — Foreign Agents Registration Act Database

| Campo            | Detalhe                                              |
|------------------|------------------------------------------------------|
| URL              | https://efile.fara.gov/                              |
| Tipo de acesso   | Portal web + API (https://efile.fara.gov/api/v1/)    |
| Cobertura        | Registros eletrônicos desde ~2000; anteriores via FOIA |
| Atualização      | Variável — atraso de semanas a meses é documentado   |
| Autenticação     | Não necessária para buscas básicas                   |

### O que o pipeline busca

Registros de agentes: nome do agente, principal estrangeiro, país,
data de registro, atividades descritas, status (ativo/terminado).

### Limitações

- Atraso de publicação: a lei exige registro em 48h, mas DOJ frequentemente
  leva semanas ou meses para processar e publicar
- Registros pré-2000 não estão digitalizados — requerem FOIA ao DOJ
- Isenção LDA: alguns agentes se registram apenas no LDA, alegando isenção
  FARA — verificar manualmente se a isenção se aplica

---

## 4. Florida Sunbiz — Division of Corporations

| Campo            | Detalhe                                              |
|------------------|------------------------------------------------------|
| URL              | https://search.sunbiz.org/                           |
| Tipo de acesso   | Portal web (scraping leve via requests + BeautifulSoup) |
| Cobertura        | Todas as entidades registradas na Flórida            |
| Atualização      | Diária                                               |
| Autenticação     | Não necessária                                       |

### O que o pipeline busca

Pesquisa por nome de officer/registered agent: empresas onde o alvo
figura como gerente, diretor, ou agente registrado.

### Dados disponíveis

- Nome legal da empresa
- Número de registro (Document Number)
- Data de constituição / effective date
- Status (Active/Inactive/Dissolved)
- Registered agent e endereço
- Todos os officers com endereços declarados

### Limitações

- Busca por officer exige nome exato ou truncado — transliterações podem
  não retornar resultado
- Empresas dissolvidas permanecem na base mas marcadas como Inactive
- Endereços são do momento do filing — podem estar desatualizados

---

## 5. Delaware — Division of Corporations

| Campo            | Detalhe                                               |
|------------------|-------------------------------------------------------|
| URL              | https://icis.corp.delaware.gov/                       |
| Tipo de acesso   | Portal web (formulário com ViewState — mais complexo) |
| Cobertura        | Todas as entidades registradas em Delaware            |
| Atualização      | Diária                                                |
| Autenticação     | Não necessária para buscas básicas                    |

### O que o pipeline busca

Pesquisa por nome da entidade: confirma existência, data de incorporação,
registered agent, status.

### Limitações críticas

**Delaware é a jurisdição com menor disclosure do mundo corporativo americano.**
O portal público revela apenas existência e registered agent — que é
quase sempre uma empresa fiduciária (ex: "The Corporation Trust Company"),
não o proprietário real.

Para informações de ownership real:
- FinCEN BOI (Beneficial Ownership Information) — acessível apenas para
  autoridades com processos legais específicos
- Documentação contratual via FOIA quando há envolvimento federal
- Investigação jornalística de fontes primárias (documentos internos, whistleblowers)

---

## 6. Texas Comptroller of Public Accounts

| Campo            | Detalhe                                               |
|------------------|-------------------------------------------------------|
| URL              | https://mycpa.cpa.state.tx.us/coa/                    |
| Tipo de acesso   | Portal web (busca por nome)                           |
| Cobertura        | Empresas domésticas e estrangeiras registradas no TX  |
| Atualização      | Semanal                                               |
| Autenticação     | Não necessária                                        |

### O que o pipeline busca

Empresas onde o alvo aparece como officer, director, ou responsible party,
em especial nos setores de petróleo/gás (SIC 1311) e agronegócio.

### Limitações

- Busca por nome de pessoa é menos direta do que FL — o pipeline busca
  por nome de empresa vinculada, não por nome do officer diretamente
- Endereços de foreign LLCs registradas no TX podem ser apenas do
  registered agent local

---

## 7. OpenCorporates

| Campo            | Detalhe                                               |
|------------------|-------------------------------------------------------|
| URL              | https://opencorporates.com/                           |
| Tipo de acesso   | API REST (chave necessária para buscas de officer)    |
| Cobertura        | +140 jurisdições, +200 milhões de empresas            |
| Atualização      | Varia por jurisdição (de diária a mensal)             |
| Autenticação     | `OPENCORPORATES_API_KEY` (gratuita com limites)       |
| Rate limit       | 50 req/dia (plano gratuito)                           |

### O que o pipeline busca

Officer search: empresas em qualquer jurisdição coberta onde o alvo aparece
como director, secretary, officer ou beneficial owner.

### Limitações

- Qualidade de cobertura varia muito por jurisdição
- Dados de officer de algumas jurisdições têm atraso de meses
- Plano gratuito (50 req/dia) pode ser insuficiente para alvos com muitas
  variações de nome — priorizar variações mais específicas

---

## 8. Imprensa Brasileira (NEWS-BR)

| Campo            | Detalhe                                              |
|------------------|------------------------------------------------------|
| Fontes cobertas  | Ver `skills/search-news-archive/references/trusted-outlets.md` |
| Tipo de acesso   | Busca web (Claude Code com acesso a web)             |
| Cobertura        | Artigos indexados pelos buscadores                   |
| Atualização      | Tempo real (dependente do índice do buscador)        |

### Outlets de referência

Folha de S.Paulo, O Estado de S. Paulo, O Globo, Agência Pública,
The Intercept Brasil, Piauí, Agência Brasil, Reuters Brasil, Abraji (base
de referências), UOL Investigações.

### Limitações

- Artigos pagos (paywall) retornam apenas headline e lide
- Indexação pode ter atraso de horas a dias após publicação
- Veículos regionais têm cobertura variável no índice

---

## 9. Imprensa Americana (NEWS-US)

| Campo            | Detalhe                                              |
|------------------|------------------------------------------------------|
| Fontes cobertas  | Ver `skills/search-news-archive/references/trusted-outlets.md` |
| Tipo de acesso   | Busca web                                            |

### Outlets de referência

The New York Times, The Washington Post, ProPublica, Reuters, AP News,
Bloomberg, The Wall Street Journal, Houston Chronicle, Miami Herald,
Orlando Sentinel (cobertura FL), Delaware Business Times.

### Limitações

- Mesmas que NEWS-BR (paywall, indexação)
- Nomes brasileiros raramente aparecem em grafias corretas na imprensa
  americana — usar variações sem acentos nas buscas

---

## Bases não cobertas (e por quê)

| Base                  | Por que não cobre                                      |
|-----------------------|--------------------------------------------------------|
| Lexis/Nexis           | Paga, acesso institucional necessário                  |
| Sayari Analytics      | Paga, focada em compliance corporativo                 |
| Refinitiv/LSEG        | Paga                                                   |
| OFAC SDN List         | Seria útil para sanções — pendente de implementação    |
| FinCEN BOI            | Restrito a autoridades — não acessível a jornalistas   |
| Registros de outros estados americanos | Fora do escopo atual (FL, DE, TX cobrem 80%+ dos casos BR-EUA) |
| Bases brasileiras (CGU, TCU, STF) | Fora do escopo — investigação parte do BR |

Para bases pagas, o pipeline registra a lacuna e recomenda acesso manual.
