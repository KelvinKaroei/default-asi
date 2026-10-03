# Preparar o ambiente desktop

O desenvolvimento foi validado em Windows x64. Ainda não foi reproduzido em uma instalação limpa do Windows. Os scripts de empacotamento usam caminhos e ferramentas desse sistema.

## Dependências

- Node.js e npm (ambiente validado: Node 24).
- Python 3.14 x64 para o conjunto de dependências fixadas.
- Rust com alvo MSVC, Visual Studio C++ Build Tools e Windows SDK.
- WebView2 Runtime.
- Ollama portátil para Windows extraído em `.tools/ollama`, contendo `ollama.exe` e a pasta de bibliotecas distribuída com ele.

As ferramentas e os modelos não acompanham o repositório. Instale-os a partir das distribuições oficiais. Consulte os detalhes históricos em [Ambiente e modelos](ambiente-e-modelos.md).

## Preparar e verificar

Na raiz do projeto, em PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
npm.cmd ci
npm.cmd test
npm.cmd run build
```

Para os testes Python:

```powershell
Set-Location backend
../.venv/Scripts/python.exe -m pytest -q
Set-Location ..
```

Com Ollama portátil disponível, prepare os recursos e gere o aplicativo:

```powershell
npm.cmd run backend:package
npm.cmd run desktop:build
```

Para gerar também o instalador, use `npm.cmd run desktop:package`. O build pode baixar componentes do instalador; reserve espaço para ferramentas, recursos e arquivos temporários.

Os modelos são separados. O ambiente de desenvolvimento usa `qwen3:8b` e `embeddinggemma:300m`, previamente baixados no cache do Ollama. Outros modelos ou contextos exigem avaliar a memória disponível. O aplicativo não baixa modelos automaticamente.

## Limitações da primeira publicação

Sem teste em Windows limpo, assinatura digital ou validação em outras placas de vídeo. A prévia web não substitui o aplicativo desktop. Não publique históricos, documentos pessoais ou capturas contendo conversas em relatos de erro. Os scripts de migração e instalação são ferramentas de manutenção; não são etapas necessárias para experimentar a interface.
