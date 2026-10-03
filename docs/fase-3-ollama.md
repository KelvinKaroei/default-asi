# Fase 3 — backend e conexão local

Esta fase acrescenta detecção de hardware, seleção de modelos instalados, configuração de contexto e um teste de inferência com frase fixa. O chat permanece uma demonstração: respostas livres e streaming pertencem à Fase 4.

## Comunicação entre componentes

```text
Janela React
  → comando Tauri backend_connection
  → Python/FastAPI em 127.0.0.1:porta efêmera
  → Ollama em 127.0.0.1:11434
  → modelo local (CPU/GPU)
```

O Rust gera uma credencial aleatória por sessão, entrega-a ao Python pelo stdin e recebe somente a porta pelo stdout. A janela local recebe endereço e credencial pelo IPC restrito do Tauri. Cada requisição HTTP ao backend envia `Authorization: Bearer …`. O token fica na memória; não aparece na URL, linha de comando, arquivo de configuração ou logs.

IPC é a comunicação entre processos. REST é a organização dos pedidos HTTP em recursos: consultar hardware usa GET; salvar configurações usa PUT; executar diagnóstico usa POST. Nesta etapa a resposta é um JSON completo. Streaming significa receber fragmentos antes do fim da geração e será implementado na próxima fase.

O Ollama iniciado pelo aplicativo usa `OLLAMA_NO_CLOUD=1`, uma geração por vez e no máximo um modelo carregado. A API da aplicação não oferece download, execução de comandos nem encaminhamento de URLs arbitrárias. Uma instância desconhecida ocupando a porta 11434 não é assumida nem encerrada automaticamente.

## Arquivos e funções

| Arquivo | Responsabilidade e funções principais |
|---|---|
| `desktop/src/backend.rs` | `Backend::connect` inicia Python, transmite a credencial e aguarda a porta; `backend_connection` atende somente a janela principal; `stop` fecha stdin e aguarda o processo terminar. A inicialização fica fora da thread da interface. |
| `desktop/src/main.rs` | Registra o estado e o comando; encerra o backend na saída do aplicativo. |
| `desktop/build.rs`, `desktop/capabilities/main.json` | Geram e concedem somente a permissão de obter a conexão local. Nenhum comando de shell é exposto à interface. |
| `backend/app/__main__.py` | `main` lê a credencial, abre o socket em loopback e inicia Uvicorn; `Server.startup` informa a porta após inicializar; `watch_parent` encerra o servidor quando o aplicativo fecha seu canal stdin. |
| `backend/app/server.py` | `create_app` monta as rotas e o ciclo de vida; `SessionGuard` verifica Host, Origin, credencial e tamanho máximo de 8 KiB; `Settings` valida modelo/contexto; `validate_model` exige modelo local instalado com capacidade de geração; `probe` executa uma única frase fixa e calcula a velocidade. |
| `backend/app/runtime.py` | `Ollama.start` serializa inicializações; `_start` verifica arquivo/porta e abre o runtime portátil sem janela; `call` faz HTTP somente ao endereço fixo local; `stop_process` encerra apenas o processo próprio e seus descendentes; `close` também fecha HTTPX. |
| `backend/app/hardware.py` | `detect_hardware` combina psutil, registro do Windows e nvidia-smi. Falha na detecção NVIDIA não impede consultar RAM, CPU e disco. |
| `backend/app/diagnostics.py` | `local_logger` grava eventos operacionais com rotação de até quatro arquivos de aproximadamente 1 MB. Não grava prompts, respostas, tokens de sessão ou cabeçalhos. |
| `frontend/src/services/backend.ts` | `request` obtém a conexão via Tauri, acrescenta autenticação e timeout e converte falhas em mensagens. A prévia no navegador não recebe a credencial do aplicativo. |
| `frontend/src/features/useLocalBackend.ts` | Mantém estados de conexão, hardware, modelos e diagnóstico. `refresh`, `save`, `start` e `test` ligam as ações da tela às rotas. |
| `frontend/src/features/Settings.tsx` | Mostra dados reais, permite salvar modelo/contexto e apresenta resultado e consumo observado no teste. Alterações não salvas impedem testar uma configuração diferente da selecionada. |
| `scripts/install-ollama.py` | Download retomável do ZIP oficial fixado na versão 0.34.4, verificação SHA-256 e extração no projeto. Não configura inicialização automática do Windows. |
| `scripts/prefetch-qwen3.py` | Alternativa de instalação explícita para adiantar o modelo enquanto o runtime baixa: usa o registro oficial, verifica tamanho/SHA-256 de cada blob e publica o manifesto no cache padrão somente ao terminar. No uso comum, prefira `ollama pull`. |
| `scripts/download_parts.py` | Auxiliar do pré-download: divide o arquivo em intervalos HTTP, retoma partes e reúne o resultado para verificação final. Não é chamado pela interface. |
| `scripts/verify-backend.py` | Verificação real de hardware, autenticação, seleção, inferência, endereços de escuta e encerramento de processos. Requer `qwen3:8b` já instalado; não baixa modelos. |
| `backend/tests/`, `frontend/src/features/Settings.test.tsx` | Testes de autenticação/origem/tamanho, estados offline, seleção, persistência, modelos remotos, hardware indisponível e fluxo visual de salvar/testar. |

## Por que essas bibliotecas

FastAPI organiza as rotas e valida JSON por meio do Pydantic. Uvicorn é o servidor HTTP que executa a aplicação. HTTPX faz chamadas assíncronas ao Ollama, sem proxy herdado do ambiente. psutil mede memória e acompanha processos próprios. pytest e Vitest verificam comportamento sem precisar carregar um modelo a cada teste.

Foi aproveitado o Python 3.14.7 já instalado. As dependências ficaram isoladas em `.venv`, com versões reproduzíveis em `backend/requirements.lock.txt`. Não é necessário instalar outro Python para esta etapa. SQLite ainda não foi introduzido; somente modelo/contexto são persistidos em JSON por troca atômica de arquivo.

## Dados e execução

- Configuração: `%LOCALAPPDATA%/CyberAITutor/settings.json`.
- Logs: `%LOCALAPPDATA%/CyberAITutor/logs/backend.log` e arquivos rotacionados.
- Modelos: `%USERPROFILE%/.ollama/models`, compatível com o armazenamento padrão do Ollama.
- Runtime portátil: `.tools/ollama/ollama.exe`.
- Executável: `desktop/target/release/cyber-ai-tutor.exe`.

O executável desta fase contém a interface, mas ainda depende do Python, backend e runtime dentro deste projeto. O caminho do projeto é incorporado na compilação: mover somente o EXE para outra pasta/máquina não o transforma em distribuição independente. O instalador e o empacotamento Python são da Fase 12.

Para reproduzir as dependências em uma cópia de desenvolvimento:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
npm.cmd ci
.venv\Scripts\python.exe scripts/install-ollama.py
npm.cmd run desktop:build
```

O script de instalação baixa aproximadamente 1,46 GB de runtime. O Qwen3 8B Q4_K_M representa aproximadamente 5,2 GB adicionais. As estimativas iniciais foram 6–9 GB de VRAM com contexto 4096, margem de 8–10 GB de RAM livre e cerca de 20 GB de disco para runtime, modelo e temporários. São estimativas; não representam memória medida durante inferência.

Para instalar explicitamente o modelo, abra o aplicativo, entre em Configurações e confirme que o Ollama está conectado. Em um terminal na pasta do projeto:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
.\.tools\ollama\ollama.exe pull qwen3:8b
```

`pull` baixa o modelo para o armazenamento local; precisa de internet nessa instalação. Depois do download, a geração usa os arquivos locais. Clique em **Atualizar diagnóstico**, escolha `qwen3:8b`, mantenha 4096 tokens, salve e use **Testar inferência local**.

Um token é uma unidade de texto processada pelo modelo, não necessariamente uma palavra. A janela de contexto limita o texto considerado durante a geração. Quantização reduz a precisão numérica dos pesos para diminuir memória/disco; `Q4_K_M` identifica o formato quantizado deste modelo. Modelos menores e contextos menores geralmente usam menos memória, com possíveis perdas de qualidade/capacidade.

## Verificações reproduzíveis

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run format:check
Push-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Pop-Location
```

Para executar o teste real independente, feche o aplicativo para liberar a porta 11434 e rode:

```powershell
.venv\Scripts\python.exe scripts/verify-backend.py
```

Esse teste seleciona e salva `qwen3:8b` com contexto 4096 e deixa essa preferência no aplicativo. O diagnóstico exibe tokens/s, duração total e VRAM reportada pelo Ollama. A primeira execução inclui carregamento; não é um benchmark de conversas longas. O modelo pode permanecer carregado por dois minutos após o teste.

Use `scripts/verify-backend.py --connection-only` para verificar o servidor antes de ter um modelo instalado. O teste aguarda também o término assíncrono do `conhost` do Windows, que pode acontecer instantes depois da saída do Python.

## Erros e diagnóstico

| Sintoma | Causa provável e correção |
|---|---|
| Abra o aplicativo desktop | A prévia Vite funciona apenas como interface. Abra o EXE para receber a sessão local pelo Tauri. |
| Ambiente Python ausente / backend não inicia | Verifique `.venv/Scripts/python.exe` e instale `requirements.lock.txt`. Confirme que o projeto não foi movido após compilar. |
| Runtime portátil não instalado | Termine `install-ollama.py`. Um download incompleto não é um runtime válido. |
| Porta 11434 ocupada | Outra instância do Ollama ou do tutor está aberta. Feche-a normalmente e tente novamente; o aplicativo não encerra processos desconhecidos. |
| Nenhum modelo instalado | A instalação do runtime não inclui modelos. Faça o download explícito e atualize o diagnóstico. |
| Modelo não oferece geração local | Foi selecionado modelo remoto, ausente ou sem capacidade de completar texto. Escolha um modelo GGUF local compatível. |
| Tempo limite / memória insuficiente | Confira RAM e VRAM livres, feche aplicativos pesados, reduza contexto para 2048 ou teste modelo menor. Não repita várias gerações simultâneas. |
| GPU não detectada | Confira driver NVIDIA e `nvidia-smi`; a medição de RAM/CPU continua funcionando. |
| Não foi possível salvar | Verifique permissões e espaço em `%LOCALAPPDATA%/CyberAITutor`. Uma gravação que falha não é apresentada como salva. |
| SHA-256 incorreto | O instalador não extrai o arquivo. Preserve o erro para diagnóstico e baixe novamente de fonte oficial. |

Os testes Python atualmente emitem um aviso de depreciação do adaptador HTTPX do TestClient da Starlette. Os testes passam; isso não é erro de execução do backend e não exige trocar o cliente HTTP de produção nesta fase.

## Fontes oficiais

- [Ollama no Windows](https://docs.ollama.com/windows)
- [Configuração local e desativação da nuvem](https://docs.ollama.com/faq)
- [Listagem de modelos](https://docs.ollama.com/api/tags)
- [Modelos carregados e memória](https://docs.ollama.com/api/ps)
- [Geração e métricas](https://docs.ollama.com/api/generate)
- [Qwen3 8B](https://ollama.com/library/qwen3:8b)

## Registro de validação desta máquina

Hardware confirmado: Ryzen 5 5600G; RTX 3060 com 12 GiB de VRAM; 15,4 GiB de RAM utilizável. Na detecção inicial havia cerca de 3,9 GiB de RAM livres. A janela compilada apresentou corretamente hardware e runtime ausente. Dez testes Python e nove testes React passaram; build TypeScript/Vite, formatação web e compilação Tauri 0.3.0 passaram. Fechar a janela encerrou todos os processos daquela sessão, inclusive Python e WebView; um teste separado confirmou que um processo independente permanece ativo.

Ollama 0.34.4 e Qwen3 8B foram instalados. O ZIP do runtime e todos os blobs do modelo passaram por SHA-256. O modelo foi baixado antecipadamente pelo registro oficial enquanto o runtime terminava; o Ollama reconheceu normalmente o manifesto e os pesos locais.

Modelo medido: `qwen3:8b`, 8,2 bilhões de parâmetros, GGUF Q4_K_M, contexto 4096, `think=false`. Digest informado pelo Ollama: `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41`. A resposta real foi “Conexão local funcionando.”.

| Medição | Primeira execução após instalação | Nova execução após reiniciar o servidor | Segunda chamada, já carregado |
|---|---:|---:|---:|
| Tempo total | 94,73 s | 6,73 s | 0,15 s |
| Carregamento informado | 52,90 s | 6,31 s | 0,00 s |
| Geração | 0,6 tokens/s | 47,1 tokens/s | 62,7 tokens/s |
| VRAM reportada para modelo/contexto | 5,20 GiB | 5,20 GiB | 5,20 GiB |

Ollama reportou 5.578.204.118 bytes tanto em `size` quanto em `size_vram`, indicando que o modelo coube inteiramente na GPU. Na primeira medição, a RAM livre caiu até 1,33 GiB; havia também compilação em andamento. Na nova rodada sem compilação, começou com aproximadamente 3,5 GiB livres e a menor leitura foi 2,57 GiB. Esses valores são memória livre do sistema inteiro, não RAM exclusiva do modelo.

A grande diferença da primeira chamada é compatível com inicialização de caches/kernels e pressão de memória, mas a causa não foi isolada por profiling. Não trate 0,6 nem 62,7 tokens/s como desempenho garantido: a frase é curta e o segundo pedido reutiliza o mesmo prompt. A Fase 4 permitirá medir respostas maiores, latência do primeiro fragmento e qualidade didática.

O teste real confirmou autenticação e todos os listeners próprios em `127.0.0.1`, incluindo o runner do modelo. Ao fechar stdin, backend, Ollama e descendentes encerraram com sucesso, sem sobreviventes após aguardar a limpeza assíncrona do Windows. A conexão global do Windows não foi desativada durante o teste; a inferência foi feita pelo modelo local instalado, com nuvem desativada na configuração do runtime.

Para repetir as duas gerações, feche a janela do tutor e execute `.venv\Scripts\python.exe scripts/verify-backend.py --warm` na raiz do projeto.

A verificação pela janela Tauri 0.3.0 também passou: o modelo/contexto persistidos apareceram ao reabrir o aplicativo, o botão ficou indisponível durante a geração e o resultado real mostrou 43,1 tokens/s, 7,1 segundos totais e 5,20 GiB de VRAM. A janela foi deixada aberta em Configurações com esse resultado.
