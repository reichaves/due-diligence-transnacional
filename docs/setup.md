# Setup — Due Diligence Transnacional

Instalação passo a passo para rodar o pipeline no seu ambiente local.

---

## Pré-requisitos

| Componente    | Versão mínima | Como verificar         |
|---------------|---------------|------------------------|
| Python        | 3.11          | `python --version`     |
| Claude Code   | qualquer      | `claude --version`     |
| Git           | qualquer      | `git --version`        |

---

## 1. Clonar o repositório

```bash
git clone https://github.com/reichaves/due-diligence-transnacional.git
cd due-diligence-transnacional
```

---

## 2. Criar ambiente virtual e instalar dependências

### Com uv (recomendado)

```bash
pip install uv          # apenas uma vez, se uv não estiver instalado
uv sync
```

### Com pip (alternativa)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -e .
```

Dependências instaladas: `click`, `pyyaml`, `requests`, `beautifulsoup4`,
`reportlab`, `pydantic`, `jsonschema`.

---

## 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas chaves:

```ini
# Obrigatória para busca FEC via MCP
FEC_API_KEY=sua_chave_aqui

# Obrigatória para busca OpenCorporates
OPENCORPORATES_API_KEY=sua_chave_aqui

# Chave do Claude (se não usar Claude Code com conta Max)
ANTHROPIC_API_KEY=sua_chave_aqui
```

### Obter a chave FEC

1. Acesse https://api.data.gov/signup/
2. Cadastre e-mail — chave chega em minutos
3. Plano gratuito: 1.000 requisições/hora (suficiente para o pipeline)

### Obter a chave OpenCorporates

1. Acesse https://opencorporates.com/api_accounts/new
2. Plano gratuito: 50 requisições/dia (suficiente para investigações pontuais)
3. Plano jornalista: gratuito para veículos credenciados — contate
   `data@opencorporates.com`

---

## 4. Configurar o MCP fec-mcp

O pipeline usa o servidor MCP `fec-mcp` para consultas à FEC. A configuração
já está em `.mcp.json` na raiz do repositório.

Verifique se o arquivo está presente:

```bash
cat .mcp.json
```

Saída esperada:

```json
{
  "mcpServers": {
    "fec-mcp": {
      "command": "uvx",
      "args": ["fec-mcp"]
    }
  }
}
```

Se `uvx` não estiver disponível, instale com:

```bash
pip install uv
```

Para testar o MCP diretamente no Claude Code:

```
/consultar-base fec "Carlos Fontana"
```

---

## 5. Validar a instalação com o caso fictício

O repositório inclui um caso 100% fictício (Carlos Eduardo Fontana) com todos
os arquivos de achados pré-gerados. Use-o para validar o ambiente sem consumir
créditos de API:

```bash
python scripts/run_pipeline.py \
    --target examples/case-fictional/target.yaml \
    --skip-search \
    --findings-dir examples/case-fictional/findings/ \
    --output-dir /tmp/fontana-test/
```

Se a instalação estiver correta, você verá:

```
INFO run_pipeline: === Due Diligence Pipeline: Carlos Eduardo Fontana ===
INFO run_pipeline: --- Stage 2: Expanding identity ...
INFO run_pipeline: --- Stage 4: Triangulating findings
INFO run_pipeline: --- Stage 5: Generating dossier PDF
INFO run_pipeline: === Pipeline complete. Dossier: /tmp/fontana-test/dossier.pdf ===
```

Abra o PDF gerado e confirme que tem 9 seções, 11 triangulações e 2 lacunas.

---

## 6. Rodar os testes automatizados

```bash
pytest tests/ -v
```

Saída esperada: `99 passed` (ou mais, conforme o projeto evolui).

---

## 7. Configurar Claude Code para uso interativo

Dentro do diretório do projeto, inicie o Claude Code:

```bash
claude
```

O arquivo `CLAUDE.md` é carregado automaticamente. Para executar o pipeline
completo em modo interativo:

```
/investigar "Nome do Alvo"
```

O Claude vai solicitar contexto adicional, gerar variações, e executar os
5 estágios com revisões humanas obrigatórias entre eles.

---

## Ferramentas opcionais (MCP)

O pipeline detecta automaticamente e usa estas ferramentas MCP se instaladas.
Sem elas, as sub-skills usam scripts Python como fallback — a cobertura é
equivalente, mas a velocidade e precisão são menores.

### fec-mcp-server (recomendado para buscas FEC)

Fornece as ferramentas `mcp__fec-mcp__*` para consulta direta e estruturada
à API da FEC (contribuições, candidatos, PACs, gastos independentes).

```bash
# Instalar e configurar (já incluso no .mcp.json do repositório)
pip install uv
uvx fec-mcp --help   # testar instalação
```

Repositório: https://github.com/reichaves/fec-mcp-server

### osint-investigation

Fornece ferramentas `mcp__osint-investigation__*` para pesquisa de fontes
abertas — útil como fallback quando fec-mcp não está disponível, ou para
buscas na imprensa e em documentos públicos.

```bash
# Configurar no Claude Code Desktop ou claude_desktop_config.json
# Veja instruções de instalação no repositório:
```

Repositório: https://github.com/reichaves/osint-investigation

### Como verificar se os MCPs estão ativos

No Claude Code, os MCP tools disponíveis aparecem listados no início da sessão.
Para confirmar:

```
/consultar-base fec "Carlos Eduardo Ferreira"
```

Se a busca mencionar "Nível 1 — fec-mcp", o servidor MCP está ativo.
Se mencionar "Nível 3 — script Python", o servidor não foi detectado.

---

## Solução de problemas comuns

| Erro                                  | Causa provável             | Solução                                      |
|---------------------------------------|----------------------------|----------------------------------------------|
| `ModuleNotFoundError: click`          | `.venv` não ativado        | Ativar venv ou rodar `pip install click`     |
| `ModuleNotFoundError: reportlab`      | Dependência faltando       | `pip install reportlab`                      |
| `uvx: command not found`              | uv não instalado           | `pip install uv`                             |
| MCP fec-mcp não responde              | uvx não encontra o pacote  | `uvx fec-mcp --help` para testar             |
| `yaml.YAMLError` ao ler target.yaml   | Encoding incorreto         | Garantir que o arquivo está em UTF-8         |
| PDF gerado com 0 KB                   | ReportLab incompatível     | `pip install --upgrade reportlab`            |

---

## Estrutura de diretórios criada após a instalação

```
due-diligence-transnacional/
├── .venv/                 # ambiente virtual (ignorado pelo git)
├── .env                   # suas chaves de API (ignorado pelo git)
└── cases/                 # criado automaticamente pelo pipeline
    └── <slug-do-alvo>/
        ├── target.yaml
        ├── identity-variations.json
        ├── findings/
        └── dossier.pdf
```
