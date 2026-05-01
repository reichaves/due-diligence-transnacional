# Ética — Guardrails para Uso Responsável

Este pipeline foi desenhado para jornalismo investigativo de interesse público.
Usar ferramentas de investigação de forma irresponsável causa dano real a
pessoas e prejudica a credibilidade do jornalismo. Este documento descreve
quando usar, quando recusar, e como usar de forma ética.

---

## 1. Quando o pipeline PODE ser usado

O alvo deve se enquadrar em pelo menos uma das categorias abaixo:

- **Gestor ou sócio de empresa com contratos públicos** (BR ou EUA) cujo
  valor ou objeto justifica investigação
- **Doador político identificado em bases públicas** com valor acima de
  threshold de reporte (USD 200 na FEC)
- **Agente registrado no FARA ou LDA** — sua atividade de lobby/influência
  é por definição de interesse público
- **Pessoa investigada por autoridade pública** — processo judicial, CPI,
  inquérito policial, procedimento administrativo
- **Figura pública exercendo função de interesse coletivo** — cargo eletivo,
  nomeado em cargo de confiança, dirigente de entidade com recursos públicos

**Em dúvida:** a pergunta-teste é "esse dado seria publicado em um jornal de
referência com interesse público claro?" Se não, não use o pipeline.

---

## 2. Quando o pipeline deve ser RECUSADO

### 2.1 Pessoa sem relevância pública

Se o alvo não se enquadra nas categorias acima, o pipeline não deve ser
iniciado. Cidadãos comuns têm direito à privacidade mesmo que dados sobre
eles existam em bases públicas. A legalidade do acesso não equivale à
legitimidade do uso.

Resposta padrão ao usuário:
> "Este pipeline é destinado a investigação de pessoas com relevância
> pública documentada. Não consigo prosseguir sem essa condição."

### 2.2 Contexto de perseguição, assédio ou doxxing

Sinais de alerta que devem pausar o pipeline:
- Alvo é ex-parceiro, vizinho, colega de trabalho ou familiar
- Tom da solicitação é pessoal ou vingativo, não jornalístico
- Não há razão investigativa documentável
- Usuário pergunta por endereço residencial ou rotina

Resposta padrão:
> "Não consigo usar este pipeline para investigar pessoas em contexto
> pessoal ou de perseguição."

### 2.3 Perseguição política documentável

Se a solicitação visar suprimir dissidência, assediar ativistas, ou
produzir dossiê para fins políticos não jornalísticos, recusar.

### 2.4 Jurisdições não cobertas

O pipeline cobre Brasil ↔ Estados Unidos. Não iniciar buscas em outras
jurisdições — não há metodologia validada para elas.

---

## 3. Tratamento de dados pessoais sensíveis (PII)

### 3.1 O que NÃO incluir no dossiê sem justificativa clara

- **Endereço residencial** — incluir apenas se for elemento do achado
  jornalístico (ex: empresa cadastrada em endereço residencial)
- **Data de nascimento completa** (DD/MM/AAAA) de pessoa física —
  incluir apenas quando necessário para identificação inequívoca
- **CPF, SSN, número de passaporte** — mesmo que apareçam em base pública,
  redigir no dossiê. Registrar apenas a existência ("dado de identificação
  confirmado em [base]"), não o valor
- **Informações de saúde** — nunca incluir, independentemente de fonte
- **Informações sobre menores de idade** — nunca incluir, independentemente
  de relevância investigativa

### 3.2 Regra de mínimo necessário

Incluir apenas o dado pessoal estritamente necessário para o propósito
jornalístico. Se o endereço da empresa serve para o propósito, não incluir
o endereço residencial. Se o nome do sócio serve, não incluir CPF.

### 3.3 Redação no dossiê

Quando um dado sensível precisar ser citado para fins de verificação,
usar a forma:
- `[ENDEREÇO REDACTED — disponível no arquivo de trabalho do repórter]`
- `[CPF REDACTED — confirmado em [base], disponível para verificação editorial]`

---

## 4. Uso e compartilhamento dos resultados

### 4.1 O dossiê é material de trabalho, não acusação

O pipeline produz leads e achados estruturados. A interpretação editorial
— o que é relevante, o que é conclusivo, o que merece publicação — é
responsabilidade do jornalista e da redação.

### 4.2 Verificação adicional obrigatória antes de publicar

Achados com nível `indicio` ou `provavel` **devem ser confirmados por meios
editoriais tradicionais** antes de publicação:
- Contato com o alvo para direito de resposta
- Confirmação com segunda fonte independente
- Revisão por editor responsável

Achados `confirmado` (≥ 3 fontes primárias) ainda requerem revisão editorial
— o pipeline automatiza a pesquisa, não a verificação editorial.

### 4.3 Dossiês de casos reais não devem estar em repositórios públicos

O arquivo `cases/` está no `.gitignore`. **Nunca commitar dossiês de casos
reais no repositório.** Os arquivos em `examples/` são fictícios
(case-fictional) ou sanitizados (case-magro-redacted) — não contêm dados
sensíveis reais.

### 4.4 Compartilhamento interno

Ao compartilhar dossiês dentro da redação:
- Usar canais internos seguros (não e-mail pessoal, não Telegram pessoal)
- Registrar quem teve acesso ao material de investigação
- Seguir a política editorial da publicação para material pré-publicação

---

## 5. Direito de resposta

Antes de publicar qualquer achado, o alvo tem direito de resposta. Mesmo que
o dossiê contenha apenas dados de bases públicas, o princípio ético e legal
do contraditório se aplica.

O protocolo mínimo:
1. Apresentar os principais achados ao alvo em formato claro
2. Conceder prazo razoável para resposta (geralmente 48-72h para reportagens
   investigativas; verificar política editorial da publicação)
3. Incluir a resposta ou a confirmação de "não quis comentar" na reportagem

O pipeline não gera contato com o alvo — esse passo é inteiramente manual
e editorial.

---

## 6. Referências normativas

### Internacionais

- **SPJ Code of Ethics** (Society of Professional Journalists) —
  minimizar danos, agir de forma independente, ser responsável
- **Declaração de Princípios da IFJ** (International Federation of Journalists) —
  respeito à privacidade, direito de resposta, separação de fatos e opinião

### Brasileiras

- **Código de Ética dos Jornalistas Brasileiros** (FENAJ, 2007) —
  Art. 7 (verificação), Art. 8 (direito de resposta), Art. 11 (privacidade)
- **LGPD — Lei 13.709/2018** — dados de pessoas físicas brasileiras;
  mesmo dados em bases públicas podem ter restrições de uso sob LGPD
  quando reprocessados para fins diferentes do original

### Americanas

- **Privacy Act (5 U.S.C. § 552a)** — dados em registros federais
- **FOIA (5 U.S.C. § 552)** — acesso a registros governamentais
- **First Amendment protections** — proteção da atividade jornalística,
  mas não isenção de responsabilidade civil por dano à reputação (defamação)

---

## 7. Quando reportar uso indevido

Se você acreditar que este pipeline está sendo usado de forma antiética
ou para fins que violam estas diretrizes, reporte ao mantenedor:

Reinaldo Chaves — reichaves@gmail.com

Inclua: contexto da solicitação, indicadores de uso problemático, e
qualquer output que tenha sido gerado indevidamente.
