# Ambiente, dependências e modelos

## Estado atual — Fase 3

O backend confirmou Ryzen 5 5600G, RTX 3060 com 12 GiB de VRAM e 15,4 GiB de RAM utilizável. Python 3.14.7 foi mantido, com FastAPI/Uvicorn/HTTPX/psutil em `.venv`; as versões exatas estão em `backend/requirements.lock.txt`. Ollama 0.34.4 foi instalado de forma portátil em `.tools/ollama`, com ZIP oficial verificado por SHA-256. O backend e o Ollama reais já passaram no teste de conexão e encerramento em loopback. A medição do Qwen3 consta no [relatório da Fase 3](fase-3-ollama.md).

As tabelas e propostas abaixo preservam o planejamento inicial; use o relatório da fase atual para comandos e resultados da instalação.

## Inspeção inicial em 24/09/2026 — Fase 1

| Item | Resultado observado |
|---|---|
| GPU | NVIDIA GeForce RTX 3060, 12288 MiB de VRAM via nvidia-smi |
| CPU | Registro retornou AMD Ryzen 5 5600G with Radeon Graphics, mas também erro de conversão ao ler outras propriedades |
| RAM | 16 GB informados pelo usuário; consulta CIM bloqueada por acesso negado |
| Windows | API do sistema retornou NT 10.0.26200.0; edição comercial não confirmada |
| Node/npm | v24.19.0 / 11.17.0 |
| Python | 3.14.7, instalação 64 bits |
| Git | Disponível no ambiente desta tarefa; verificar disponibilidade no terminal pessoal |
| Rust/Cargo/Ollama | Não encontrados no PATH desta sessão; isso não prova ausência de instalação |
| Build Tools/WebView2/espaço livre | Ainda não verificados |

As consultas CIM foram somente leitura. A negativa provavelmente decorre das restrições desta sessão. Não alteramos permissões. A RAM pode ser confirmada pelo Gerenciador de Tarefas; o aplicativo futuro usará detecção com fallback e mostrará “desconhecido” quando necessário.

### Atualização após a Fase 2

Em 24/09/2026, instalamos as dependências npm do projeto, Rust 1.98.1 isolado em `.tools` (sem alterar o PATH global) e Visual Studio Build Tools 2022 17.14.41 com C++/Windows SDK 10.0.26100.0. WebView2 153.0.4234.48 já estava presente. A interface e o executável Tauri foram compilados e a janela nativa foi aberta e testada. Ollama, modelos, backend Python, SQLite e FAISS continuam para as fases seguintes. O diagnóstico inicial da tabela acima registra o estado anterior a essas instalações.

## O que será necessário instalar e por quê

Nada foi instalado na Fase 1. Antes de qualquer instalação futura, explicaremos os pacotes concretos e seu propósito. Não executar comandos de download abaixo automaticamente — esta fase contém apenas planejamento.

| Programa | Quando | Função |
|---|---|---|
| Node.js LTS + npm | Fase 2 | Compilar React/TypeScript; o Node já disponível será validado com a versão escolhida do Vite |
| Rust estável, alvo MSVC | Fase 2 | Compilar a camada desktop Tauri |
| Microsoft C++ Build Tools + Windows SDK | Fase 2 | Linker e bibliotecas nativas exigidos pelo Tauri no Windows |
| Microsoft Edge WebView2 Runtime | Fase 2 | Renderizar a interface dentro da janela; verificar antes de instalar |
| Python 3.12 64 bits, proposta inicial | Fase 3 | Ambiente conservador para bibliotecas nativas de IA e empacotamento; validar wheels antes de escolher |
| Ollama para Windows | Fase 3 | Servir modelos locais na GPU/CPU |
| Modelo de chat escolhido | Fase 3 | Pesos necessários à inferência offline |
| Modelo de embeddings | Fase 8 | Vetorizar materiais e perguntas localmente |

Python 3.14 não será removido. Se adotarmos 3.12, será em paralelo com ambiente `.venv` do projeto. A compatibilidade real será testada; não estamos afirmando que 3.14 seja incompatível com todas as bibliotecas.

Docker, WSL, Kali, VirtualBox e VMware não são necessários para o chat. Um ambiente de laboratório será escolhido depois, conforme exercício e memória disponível. CUDA Toolkit completo não é uma dependência inicial proposta; verificar primeiro o funcionamento do Ollama com o driver NVIDIA existente.

## Bibliotecas por fase

| Fase | Dependências propostas | Responsabilidade |
|---|---|---|
| 2 | react, react-dom, typescript, vite, @vitejs/plugin-react, @tauri-apps/api, @tauri-apps/cli; crates tauri/tauri-build | Interface, tipos, build e janela |
| 3–4 | fastapi, uvicorn, httpx, pydantic-settings, psutil | API, servidor, cliente Ollama, configuração e hardware |
| 5 | sqlite3 da biblioteca padrão Python | Persistência; migrações SQL pequenas e versionadas |
| 6 | react-markdown, remark-gfm, react-syntax-highlighter e tipos correspondentes | Markdown, tabelas e blocos de código |
| 7 | pypdf, python-multipart | Extração de PDF textual e upload com limites |
| 8 | faiss-cpu, numpy | Busca vetorial; embeddings por HTTP ao Ollama |
| Validação | pytest, pytest-asyncio, ruff; vitest, Testing Library, Playwright conforme necessidade | Testes de comportamento, contratos, UI e análise estática |
| 12 | PyInstaller; bundler Tauri/NSIS | Executável auxiliar e instalador Windows |

Versões exatas serão resolvidas e fixadas em lockfiles na fase em que forem usadas, após teste no Windows. FAISS CPU e o backend empacotado precisam de prova de compatibilidade antecipada na Fase 8; não deixar esse risco para o último dia. Não precisamos de LangChain, serviço de nuvem, chave de API ou treinamento para o MVP.

## Três modelos para comparar

São candidatos adequados ao orçamento proposto, não uma classificação dos modelos mais recentes. Tamanhos são os publicados no catálogo consultado; as estimativas de memória são nossas hipóteses de engenharia e não benchmarks deste PC.

| Modelo local | Download aproximado | VRAM estimada, contexto 4K | RAM livre sugerida antes de carregar | Disco livre reservado para um modelo | Vantagens e limitações |
|---|---:|---:|---:|---:|---|
| Qwen3 8B Q4_K_M (`qwen3:8b`) | 5,2 GB | 6–9 GB | 8–10 GB | 10–12 GB | Primeira opção para tutoria geral e raciocínio; maior custo e possível latência extra no modo thinking |
| Gemma 3 4B Q4_K_M (`gemma3:4b`) | 3,3 GB | 4–6 GB | 6–8 GB | 7–8 GB | Alternativa menor e multilíngue; menor capacidade pode exigir dividir problemas complexos |
| Qwen2.5-Coder 7B Q4_K_M (`qwen2.5-coder:7b`) | 4,7 GB | 5–8 GB | 8–10 GB | 9–11 GB | Foco em programação e depuração; qualidade como professor geral deve ser comparada |

Fontes dos tamanhos e características: [Qwen3 8B](https://ollama.com/library/qwen3:8b), [Gemma 3 e quantizações](https://ollama.com/library/gemma3/tags), [Qwen2.5-Coder e quantizações](https://ollama.com/library/qwen2.5-coder/tags).

Quantização reduz a precisão numérica dos pesos para ocupar menos memória, com possível perda de qualidade. Q4 usa representações próximas de quatro bits por peso com detalhes adicionais de armazenamento; o tamanho total não é simplesmente parâmetros multiplicados por quatro bits.

RAM livre sugerida é uma margem de planejamento para carregamento, buffers e aplicação, não consumo medido nem requisito oficial. VRAM guarda pesos, cache de contexto e buffers. RAM e VRAM são recursos diferentes: memória mapeada, cache do sistema e offload impedem somar números como se fossem uma conta exata. Com modelo parcialmente na CPU, a pressão na RAM e a latência podem aumentar bastante.

Reservar aproximadamente 1–2 GB de RAM para UI/backend/base pequena como orçamento inicial a medir, além do Windows e demais programas. Com 16 GB totais, evitar executar VMs grandes junto com a inferência. Índices maiores exigem novo orçamento. O armazenamento dos três modelos soma aproximadamente 13,2 GB de pesos, sem ferramentas, cache e materiais; instalar somente um inicialmente.

Escolha proposta: começar com Qwen3 8B, `num_ctx=4096`, uma geração por vez e saída inicialmente limitada a cerca de 1024 tokens. Contexto é o espaço para instruções, conversa, fontes e geração; 128K anunciado pelo modelo não significa que 128K caiba confortavelmente nesta GPU. Aumentar para 8K somente após medir.

O modelo de embeddings será uma aquisição separada na Fase 8. [EmbeddingGemma](https://ollama.com/library/embeddinggemma) é candidato, mas tamanho, memória, qualidade em português e licença serão revistos antes do download. Não manter vários modelos carregados sem medir a memória; indexar materiais em lotes antes de gerar respostas.

## Como medir na Fase 3

1. Anotar tag, digest, quantização, contexto, versão do Ollama e aplicativos abertos.
2. Registrar RAM/VRAM antes, durante o carregamento e durante geração, usando Gerenciador de Tarefas e `nvidia-smi`.
3. Consultar `ollama ps` para distinguir GPU, CPU e divisão entre elas.
4. Separar tempo de carregamento, tempo até o primeiro fragmento e velocidade de geração. Calcular tokens/s pelos contadores reais de avaliação/duração do Ollama, não pelos fragmentos recebidos na UI.
5. Repetir um pequeno conjunto fixo: TCP versus UDP, permissões Linux, erro Python e análise de log sintético. Avaliar precisão, português, didática, comando explicado e capacidade de admitir incerteza.
6. Testar sem internet depois de instalar os pesos. Confirmar ausência de recursos cloud e acesso externo da aplicação.

Não prometemos tokens/s antes dessa medição.

## Erros previstos e diagnóstico

| Sintoma | Causa provável | Diagnóstico e correção |
|---|---|---|
| `ollama` não reconhecido | Ausente ou PATH desatualizado | Verificar instalação e abrir novo terminal; não baixar automaticamente |
| Conexão recusada | Servidor parado ou porta errada | Verificar processo e `127.0.0.1:11434`; iniciar somente após configurar modo local |
| Modelo não encontrado | Tag não instalada | Listar modelos e escolher existente; mostrar orçamento antes de oferecer download |
| VRAM insuficiente/lentidão | Contexto grande, concorrência ou outros programas | Conferir nvidia-smi/ollama ps, reduzir contexto e usar modelo menor |
| Falta de wheel Python | Versão/arquitetura sem pacote compatível | Conferir matriz do pacote e usar ambiente Python compatível, sem substituir o Python global |
| Falha de compilação Tauri | Build Tools/Rust/WebView2 ausentes | Seguir pré-requisitos oficiais e identificar componente faltante |
| Porta ocupada | Outro processo escutando | Selecionar outra porta local para o backend; não finalizar processo desconhecido |
| PDF sem texto | Arquivo digitalizado | Informar que OCR ainda não foi implementado |

Referências: [Tauri no Windows](https://v2.tauri.app/start/prerequisites/), [Ollama: contexto, GPU, modo local e rede](https://docs.ollama.com/faq). As configurações efetivamente aplicadas estão registradas no relatório da Fase 3.
