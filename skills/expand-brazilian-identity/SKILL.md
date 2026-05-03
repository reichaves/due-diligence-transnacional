---
name: expand-brazilian-identity
description: >
  Gera variações ortográficas e estruturais do nome do alvo para uso em
  buscas em bases americanas. Funciona para alvos de qualquer nacionalidade
  com nome latino. Use sempre antes de qualquer busca em base dos EUA —
  nomes são transliterados de forma inconsistente (ordem invertida,
  sobrenomes compostos, acentos removidos). Pode ser invocada pelo
  orquestrador ou diretamente via CLI.
---

# Expansão de Identidade do Alvo

## Quando usar

- Sempre antes de qualquer busca em base americana
- Quando o usuário disser `/expandir-nome "Nome Completo"`
- Como sub-skill chamada pelo orquestrador `due-diligence-transnacional`
- O algoritmo é agnóstico à nacionalidade: funciona com qualquer nome
  latino (espanhol, português, italiano). Para nomes não-latinos (asiáticos,
  árabes), as variações de acento e ordem inversa ainda se aplicam, mas
  a cobertura de transliteração é menor.

## Inputs

`target.yaml` com `nome_completo`, `origin_country` (opcional, default "BR"),
`parentes` (opcional), `apelidos` (opcional) — ou via CLI:

```bash
python skills/expand-brazilian-identity/scripts/expand_identity.py \
  --name "Carlos Eduardo Ferreira" \
  --alias "Rick Ferreira" \
  --origin-country BR \
  --relatives '[{"nome": "Carla Ferreira", "relacao": "conjuge"}]'

# Non-Brazilian target (Peruvian):
python skills/expand-brazilian-identity/scripts/expand_identity.py \
  --name "Pablo Vargas Mendoza" \
  --origin-country PE
```

## Variações geradas (mínimo obrigatório)

1. Nome completo conforme fornecido
2. Nome completo sem acentos (`João` → `Joao`, `Ângelo` → `Angelo`)
3. Primeiro nome + último sobrenome (`Carlos Ferreira`)
4. Ordem invertida: último sobrenome + primeiro nome (`Ferreira Carlos`)
   — convenção de alguns formulários americanos
5. Iniciais + último sobrenome (`C. E. Ferreira`, `C. Ferreira`)
6. Sobrenome isolado (`Ferreira`) — busca ampla, alto ruído; marcar como tal
7. Para cada apelido fornecido: registrar como variação do tipo `alias`
8. Para cada parente direto: gerar nome completo sem acentos + sobrenome
   isolado, ambos do tipo `relative`

## Output

`identity-variations.json` validado contra
`schemas/identity-variations.schema.json`.

Exemplo mínimo:
```json
{
  "target_name": "Carlos Eduardo Ferreira",
  "generated_at": "2026-04-30T14:00:00+00:00",
  "approved_by_human": false,
  "variations": [
    {"variation": "Carlos Eduardo Ferreira", "type": "full_name", "note": "..."},
    {"variation": "Carlos Ferreira",         "type": "first_last", "note": "..."},
    {"variation": "Ferreira Carlos",         "type": "last_first", "note": "..."},
    {"variation": "C. E. Ferreira",           "type": "initials_last", "note": "..."},
    {"variation": "Ferreira",                 "type": "surname_only", "note": "..."}
  ]
}
```

## Revisão humana obrigatória

Após gerar as variações, mostrar ao usuário e perguntar:
1. "Há variações incorretas a remover?"
2. "Há variações faltando (apelidos, nome de solteiro/a, nome americanizado)?"

Só avançar para buscas após confirmação explícita. Atualizar
`approved_by_human: true` no JSON antes de passar para as sub-skills.

## Princípios anti-alucinação

- Nunca inventar variações que não derivem do nome fornecido.
- Nunca buscar sem aprovação humana das variações.
- Registrar sempre a versão do script usada (`generated_at` no output).

## Referências

- `references/transliteration-patterns.md` — tabela de substituições de
  caracteres e padrões de transliteração comuns
- Script CLI: `scripts/expand_identity.py`
