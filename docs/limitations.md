# Limitações — O que o pipeline NÃO faz

Documentar limitações é parte da metodologia jornalística. Um dossiê
sem limitações explícitas é um dossiê que superestima sua própria confiança.

---

## 1. Limitações de cobertura geográfica

### EUA como única jurisdição de destino

O pipeline cruza alvos de **qualquer país de origem** com bases **americanas**
(FEC, LDA, FARA, FL/DE/TX, OpenCorporates-US). O país de origem do alvo é
configurável via `origin_country` no `target.yaml` (padrão: "BR"). Países de
origem com suporte de busca de imprensa pré-configurado: BR, US. Para outros
países (PE, CO, AR, MX e demais), a skill `search-news-archive` realiza busca
genérica na web.

O que o pipeline **não** cobre na jurisdição de destino:

- Paraísos fiscais populares entre brasileiros: Ilhas Cayman, BVI,
  Luxemburgo, Suíça, Ilhas Jersey — sem sub-skills implementadas
- Europa: não há integração com registros corporativos de Portugal,
  Espanha, Reino Unido, Países Baixos ou outros
- América Latina: Panamá, Uruguai, Argentina — fora do escopo
- Outros estados americanos além de FL, DE, TX: NV, NY, WY e outros
  são omitidos (cobrem minoria dos casos BR-EUA, mas existem)

**Consequência prática:** estruturas de offshore que passam por BVI ou
Cayman antes de chegar aos EUA podem não ser detectadas. O pipeline
encontraria a entidade americana mas não o vínculo offshore.

### Apenas bases públicas americanas

O pipeline não acessa:
- **FinCEN BOI** (Beneficial Ownership Information) — banco de beneficiários
  finais criado pelo CTA (Corporate Transparency Act, 2024), restrito a
  autoridades com processo legal específico. Jornalistas não têm acesso.
- **Bases tributárias estaduais** confidenciais
- **Registros judiciais selados** ou com acesso restrito

---

## 2. Limitações de escopo de busca

### Apenas bases gratuitas ou de baixo custo

O pipeline não acessa bases pagas:

| Base          | O que ofereceria                        | Por que não cobre                |
|---------------|-----------------------------------------|----------------------------------|
| Sayari        | Grafos de ownership, sanctions, PEPs    | Paga — USD 10k+/ano              |
| Lexis/Nexis   | Notícias, registros, processos          | Paga — acesso institucional      |
| Refinitiv     | KYC, due diligence corporativa          | Paga                             |
| PACER         | Processos judiciais federais americanos | Pago por página (0,10 USD)       |
| CourtListener | Processos federais (parcialmente livre) | Não implementado                 |
| OFAC SDN List | Sanções americanas                      | Gratuito mas não implementado    |

Para investigações de alta relevância (grande empresa, personagem político
de primeiro escalão), o pipeline deve ser complementado com buscas manuais
nestas bases.

### Threshold de contribuições FEC

Contribuições individuais menores que **USD 200** não precisam de nome
completo do contribuinte na FEC — aparecem apenas como totais agregados.
O pipeline não captura contribuições abaixo desse valor.

### Lobby abaixo do threshold LDA

Atividade de lobby que não atinge USD 3.000/trimestre ou 20% do tempo do
lobbista não é registrada no LDA. Influência informal ou consultoria política
não contabilizada como lobby fica fora da cobertura.

---

## 3. Limitações de qualidade de dados

### Transliteração imperfeita de nomes brasileiros

O script `expand_identity.py` gera variações sistemáticas, mas não cobre
todos os casos possíveis de erro de transliteração. Variações documentadas
que o script pode perder:

- Erros de digitação únicos (ex: "Ferandes" em vez de "Fernandes")
- Apelidos não fornecidos pelo jornalista (ex: "Betão" para "Roberto")
- Nomes de empresa abreviados de forma não-padrão
- Inversão parcial de nome composto (ex: apenas o segundo sobrenome)

**Mitigação:** a revisão humana obrigatória do Estágio 2 permite ao
jornalista adicionar variações que o script não gerou.

### Delaware não revela proprietários

O registro público de Delaware revela apenas:
- Existência da empresa
- Data de incorporação
- Registered agent (geralmente uma fiduciária, não o dono real)

O nome do proprietário real ou dos beneficiários finais **não está
disponível publicamente**. O pipeline registra a existência da entidade
em Delaware, não quem a controla.

### FARA tem atraso de publicação

O prazo legal de registro no FARA é 48h após início das atividades, mas
o DOJ frequentemente leva semanas ou meses para processar e publicar.
Ausência no eFile FARA não garante ausência de registro — pode ser
registro ainda em processamento.

### OpenCorporates: qualidade variável por jurisdição

A cobertura e a atualidade dos dados do OpenCorporates variam muito por
jurisdição. Algumas fontes têm atraso de meses. Dados de officer podem
estar desatualizados para empresas que não atualizam filings anualmente.

---

## 4. Limitações do pipeline em si

### Não é em tempo real

O pipeline executa buscas no momento em que é rodado. Dados que mudam
após a execução (empresa que incorporou ontem, contribuição que foi
registrada esta semana) não aparecem nos resultados.

Para investigações de eventos recentes (últimas 72h), verificar as bases
diretamente em vez de usar o pipeline.

### Não substitui análise editorial

O pipeline produz:
- Achados estruturados com fonte e nível de confiança
- Triangulações entre bases
- Lacunas documentadas

O pipeline **não** produz:
- Interpretação do significado jornalístico dos achados
- Avaliação de se os achados constituem infração legal ou ética
- Recomendação sobre publicar ou não
- Identificação do ângulo de pauta principal

Essas decisões são editoriais e ficam inteiramente com o jornalista.

### Não faz OSINT visual

O pipeline não:
- Reconhece faces em fotos
- Analisa vídeos ou imagens de satélite
- Verifica autenticidade de documentos escaneados
- Cruza perfis de redes sociais

Para OSINT visual, use ferramentas dedicadas (Maltego, Bellingcat toolkit,
TinEye, etc.) em conjunto com os achados deste pipeline.

### Não acessa bases vazadas ou hackeadas

O pipeline usa apenas bases **legalmente públicas**. Não acessa, não
processa e não cruza dados de bases obtidas ilegalmente (Panama Papers,
Pandora Papers, etc.). Para trabalhar com esses dados, use as plataformas
específicas de cada leak (ICIJ Offshore Leaks, etc.).

### Execução sequencial, não em tempo real paralelo

O script `run_pipeline.py` executa buscas em sequência (estágio 3 roda
base por base). Em modo Claude Code com sub-agentes, as buscas podem ser
paralelizadas — mas o script standalone não paraleliza. Para bases lentas
(scraping de Sunbiz, FARA), isso pode levar 10-20 minutos.

---

## 5. Limitações de manutenção

### Scrapers podem quebrar

Os scripts que fazem scraping (Sunbiz, Delaware, Texas Comptroller) dependem
da estrutura HTML dos respectivos portais. Qualquer mudança no layout pode
quebrar o script sem aviso. Sintomas: `status: error` nos findings JSON.

Se um scraper quebrar, verificar se o site mudou e atualizar o seletor
CSS/XPath correspondente em:
- `skills/search-state-corps/scripts/florida_sunbiz.py`
- `skills/search-state-corps/scripts/delaware_corp.py`
- `skills/search-state-corps/scripts/texas_comptroller.py`

### APIs podem mudar rate limits ou endpoints

Especialmente a API do LDA (senate.gov) e do OpenCorporates — ambas
tiveram mudanças não anunciadas no passado.

---

## 6. O que estas limitações implicam na prática

Para uma investigação publicável, o pipeline cobre aproximadamente:

- **80%** dos casos de brasileiros com presença corporativa em FL, DE ou TX
- **60%** dos casos de atividade de lobby em Washington
- **40-50%** dos casos envolvendo FARA (atraso de publicação reduz cobertura)
- **30%** dos casos de contribuições FEC (threshold USD 200 exclui pequenas contribuições)

Esses números são estimativas baseadas na cobertura das bases. Investigações
de alto impacto geralmente requerem complementação com buscas manuais e
acesso a bases pagas.

---

## Changelog de limitações

| Data         | Limitação identificada                              | Status          |
|--------------|-----------------------------------------------------|-----------------|
| 2026-05-01   | OFAC SDN List não implementada                      | Pendente        |
| 2026-05-01   | Cobertura apenas FL/DE/TX (sem NV, NY, WY)          | Conhecido       |
| 2026-05-01   | PACER/CourtListener não implementados               | Pendente        |
| 2026-05-01   | Paralelização não disponível no script standalone   | Conhecido       |
