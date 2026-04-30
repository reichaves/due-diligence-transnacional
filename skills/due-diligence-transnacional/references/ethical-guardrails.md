# Guardrails Éticos

## Quando RECUSAR uma investigação

O pipeline deve ser recusado (com explicação ao usuário) nos seguintes casos:

### 1. Pessoa sem relevância pública

Se o alvo não se enquadra em pelo menos uma das categorias abaixo, não
iniciar o pipeline:
- Gestor, sócio ou beneficiário de empresa com contratos públicos (BR ou EUA)
- Doador político identificado em bases públicas
- Agente registrado no FARA ou LDA
- Pessoa investigada por autoridade pública (processo judicial, CPI, etc.)
- Figura pública que exerce função de interesse coletivo

Resposta padrão: "Este pipeline é destinado a investigação de pessoas com
relevância pública documentada. Não consigo prosseguir sem essa condição."

### 2. Contexto de perseguição ou doxxing

Sinais de alerta:
- Usuário menciona ex-parceiro, vizinho, colega de trabalho
- Tom da solicitação é pessoal, não jornalístico
- Não há razão investigativa documentável

Resposta padrão: "Não consigo usar este pipeline para investigar pessoas
em contexto pessoal ou de perseguição."

### 3. Solicitação de PII além do necessário

O pipeline não deve expor:
- Endereço residencial (exceto se é parte do achado jornalístico — ex:
  endereço fantasma de empresa)
- Data de nascimento completa (DD/MM/AAAA) de pessoa física
- CPF ou SSN — mesmo que apareçam em base pública

Se dados acima aparecerem em achado, redigir no dossiê e registrar apenas
a existência do dado, não o valor.

### 4. Jurisdições não cobertas

O pipeline cobre: Brasil (fontes) ↔ Estados Unidos (bases de destino).
Não iniciar buscas em outras jurisdições — não há metodologia validada.

---

## Uso responsável dos achados

- O dossiê é material de trabalho jornalístico, não acusação.
- Toda publicação baseada no dossiê requer verificação editorial adicional.
- O jornalista é responsável pelo uso editorial dos achados.
- Não compartilhar dossiês de casos reais em repositórios públicos.

---

## Referência normativa

- SPJ Code of Ethics (Society of Professional Journalists)
- Código de Ética dos Jornalistas Brasileiros (FENAJ, 2007)
- LGPD — Lei 13.709/2018 (dados de pessoas físicas brasileiras)
- Privacy Act (5 U.S.C. § 552a) para dados de cidadãos americanos
