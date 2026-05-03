# Metodologia — Due Diligence Transnacional

Documentação completa da metodologia aplicada no pipeline. Este arquivo
descreve *como* e *por que* o pipeline funciona da forma que funciona,
para que jornalistas possam avaliar sua adequação editorial antes de usar.

---

## 1. Princípio fundamental

**Toda afirmação produzida pelo pipeline deve ser rastreável a uma transação,
registro ou documento específico em uma base pública.** O modelo nunca gera
texto sobre fatos de investigação — ele formata dados que vieram das bases.

Corolário: se a base não retornou dado, o pipeline diz "não encontrado" com
metodologia documentada. Nunca inventa. Nunca infere além do dado.

---

## 2. Fluxo dos 5 estágios

```
[target.yaml] → Estágio 1: Carregar contexto
                     ↓
              Estágio 2: Expandir variações de nome
                     ↓
           REVISÃO HUMANA OBRIGATÓRIA (aprovação das variações)
                     ↓
              Estágio 3: Buscas em paralelo por base
                     ↓
              Estágio 4: Triangular achados
                     ↓
           REVISÃO HUMANA OBRIGATÓRIA (aprovação dos achados)
                     ↓
              Estágio 5: Gerar dossiê PDF
```

As duas revisões humanas não são contornáveis — o pipeline para e espera
confirmação explícita antes de avançar.

---

## 3. Por que variações de nome são obrigatórias

Bases americanas foram preenchidas por terceiros (agentes imobiliários,
secretárias de escritório, balconistas de estado) que transliteraram
nomes brasileiros de forma inconsistente. Padrões documentados:

| Nome original       | Variações encontradas em bases americanas       |
|---------------------|-------------------------------------------------|
| João                | Joao, J., John, Jhon                            |
| Magalhães           | Magalhaes, Magalhaes Jr, Magalhaes-Jr           |
| Ricardo             | Richard, R., Ric                                |
| Sobrenome composto  | Apenas primeiro elemento, apenas último         |

Sem expandir variações antes de buscar, o pipeline produz **falso-negativo
sistemático** — a pessoa existe na base mas não é encontrada.

### Variações mínimas geradas pelo Estágio 2

Para qualquer nome, o script `expand_identity.py` gera:

1. Nome completo como fornecido
2. Nome completo sem acentos (transliteração ASCII)
3. Primeiro nome + último sobrenome
4. Último sobrenome + primeiro nome (ordem americana)
5. Iniciais + último sobrenome (ex: "C.E. Ferreira")
6. Último sobrenome isolado (busca ampla — alto ruído, necessário para
   variações irrecuperáveis pelas anteriores)
7. Para cada parente fornecido: variações 1-6 aplicadas ao parente
8. Para cada apelido fornecido: registrado como variação independente

### Após a revisão humana

O jornalista deve:
- Remover variações que visivelmente não se aplicam (ex: apelidos incorretos)
- Adicionar variações que o script não gerou (ex: alcunha conhecida)
- Confirmar que variações de parentes estão corretas

Só após aprovação explícita o Estágio 3 começa.

---

## 4. Ordem de busca por base e justificativa

| Prioridade | Base            | Justificativa                                                    |
|------------|-----------------|------------------------------------------------------------------|
| 1          | FEC             | Mais rápida (API via MCP); contexto legal § 30121 bem definido  |
| 2          | LDA             | senate.gov tem API pública; lobby é pista de influência direta  |
| 3          | FARA            | Agente estrangeiro é achado de alta gravidade jornalística       |
| 4          | FL-SUNBIZ       | Maior comunidade brasileira nos EUA; maior concentração de casos |
| 5          | DE-CORPS        | Delaware é jurisdição preferida de holdings; revela estrutura    |
| 6          | TX-COMPTROLLER  | Petróleo e agronegócio — setores com forte presença BR           |
| 7          | OpenCorporates  | Cobertura global; cross-check de registros estaduais             |
| 8          | Imprensa BR     | Valida achados e fornece contexto editorial                      |
| 9          | Imprensa EUA    | Cobertura americana pode revelar ângulos não visíveis em BR      |

A ordem é recomendada, não obrigatória. O campo `bases_prioritarias` no
`target.yaml` permite ao jornalista customizar.

---

## 5. Triangulação — como funciona

Triangulação é o cruzamento de achados de bases diferentes para elevar a
confiança de uma informação. O script `triangulate.py` detecta 4 tipos:

### 5.1 entity_match

Detecta quando o mesmo nome de empresa aparece em ≥ 2 bases.

**Normalização:** sufixos legais (LLC, INC, CORP, LTD, LP, LLP, PLLC) são
removidos antes da comparação. "Fontana Energy Partners LLC" e "Fontana
Energy Partners" são tratados como a mesma entidade.

**Por quê:** registros estaduais diferentes usam variações de sufixo.
Sem normalização, o cruzamento falha sistematicamente.

### 5.2 address_match

Detecta quando o mesmo endereço aparece em ≥ 2 achados.

**Normalização:** primeiros 20 caracteres do endereço em minúsculas, após
remoção de pontuação. Endereços com < 20 caracteres (muito genéricos, como
"Miami FL") são ignorados para evitar falsos positivos.

**Por quê:** o complemento ("Suite 500" vs "Ste 500") varia entre bases,
mas número e logradouro são consistentes.

### 5.3 person_match

Detecta quando o mesmo nome de pessoa aparece como vinculado em ≥ 2 achados
(ex: como officer, lobbyist, ou contato).

**Normalização:** lowercase, sem acentos.

### 5.4 date_match

Detecta quando a mesma entidade tem datas de incorporação em ≥ 2 bases com
diferença de ≤ 30 dias.

**Por quê:** a sequência típica de uma holding é: Delaware incorpora ~2
semanas antes do registro estadual (ex: DE 28/02/2021 → FL 15/03/2021 =
15 dias). Threshold de 30 dias captura essa variação normal.

---

## 6. Escala de confiança

A escala é aplicada a cada afirmação individual no dossiê, não ao alvo
como um todo:

| Nível          | Critério                                               |
|----------------|--------------------------------------------------------|
| `confirmado`   | ≥ 3 fontes primárias concordantes                     |
| `provavel`     | 2 fontes primárias concordantes                       |
| `indicio`      | 1 fonte primária ou circunstancial                    |
| `nao-encontrado` | Busca executada, zero resultados                   |

**Fontes primárias:** FEC, LDA, FARA, FL-SUNBIZ, DE-CORPS, TX-COMPTROLLER,
OpenCorporates.

**Fontes corroborativas (não primárias):** NEWS-BR, NEWS-US — elevam
contexto mas não elevam o nível de confiança sozinhas.

Para definição completa, ver
`skills/due-diligence-transnacional/references/confidence-levels.md`.

---

## 7. Documentação de ausências

Quando uma base retorna zero resultados, o pipeline registra:

- Todas as variações testadas (lista completa)
- Data e hora da consulta
- Versão da base (quando disponível)
- Contexto legal que explica a ausência (quando aplicável)

Exemplo: ausência no FEC para cidadão brasileiro sem green card é explicada
por 52 U.S.C. § 30121 — não é achado negativo, é resultado esperado.

**`nao-encontrado` nunca significa "inocente" ou "limpo".** Significa que
esta metodologia, nesta data, não localizou rastro nesta base.

---

## 8. Lacunas (gaps)

O pipeline distingue 4 tipos de lacuna:

| Tipo           | Significado                                         |
|----------------|-----------------------------------------------------|
| `no_hits`      | Busca executada corretamente, zero resultados       |
| `error`        | Erro de acesso à base (timeout, HTTP 5xx, etc.)    |
| `partial`      | Busca parcial (ex: apenas algumas variações)       |
| `not_searched` | Base esperada mas não buscada nesta execução       |

Lacunas aparecem explicitamente no dossiê com `suggested_action` — o que
o jornalista pode fazer manualmente para fechar a lacuna.

---

## 9. Revisões humanas — protocolo

### Revisão 1 — Variações de identidade (antes do Estágio 3)

O jornalista deve verificar:
- [ ] Variações sem acentos estão corretas?
- [ ] Sobrenomes compostos foram tratados corretamente?
- [ ] Parentes incluídos são os corretos?
- [ ] Há apelidos ou nomes de empresa que deveriam ser adicionados?

### Revisão 2 — Achados consolidados (antes do Estágio 5)

O jornalista deve verificar:
- [ ] Todos os hits pertencem realmente ao alvo (não a homônimos)?
- [ ] Os níveis de confiança parecem adequados?
- [ ] Há contexto externo que o pipeline não capturou?
- [ ] Há achado sensível que deve ser redigido antes do PDF?

Pular qualquer revisão invalida a metodologia e o dossiê não deve ser
usado para publicação.

---

## 10. Reprodutibilidade

Cada execução do pipeline registra:
- Timestamp de cada consulta (campo `consulted_at` nos findings JSON)
- Variações buscadas em cada base
- Versão do software (`consolidated_at` no findings.json consolidado)

Para reproduzir um resultado, use os arquivos JSON de achados originais:

```bash
python scripts/run_pipeline.py \
    --target cases/meu-alvo/target.yaml \
    --skip-search \
    --findings-dir cases/meu-alvo/findings/
```

Isso regenera apenas os Estágios 4 e 5 (triangulação e PDF) a partir dos
mesmos dados, sem refazer as buscas.
