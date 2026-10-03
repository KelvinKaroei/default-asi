# Plano de implementação e aprendizado

**Estado atual: fases 1–11 implementadas; fase 12 instalada e testada neste computador, validação em Windows limpo pendente.** Os relatórios estão ligados no README. O usuário autorizou em 1º de outubro de 2026 avançar pelas fases restantes sem confirmações de rotina; os guias preservam a explicação de cada etapa.


## Etapas e critérios de conclusão

| Fase | Entrega | Como demonstrar que funciona |
|---|---|---|
| 1 — Arquitetura | Documentos, decisões, dependências, fluxos e limites | Revisão de cobertura da especificação e links locais; sem alegar execução do app |
| 2 — Interface desktop | Tauri/React escuro, sidebar, novo chat, seletor de modos e campo multilinha; dados simulados identificados | Abrir janela no Windows; Enter quebra linha, Ctrl+Enter envia; teclado e estados vazios funcionam |
| 3 — Ollama | Backend local, hardware, lista de modelos, configurações e diagnóstico | Ollama ausente não trava UI; listar modelos sem download; confirmar bind local e modelo local |
| 4 — Chat | Prompt didático, modos, streaming, cancelar e erros | Perguntar e receber fragmentos; cancelar; interromper servidor e preservar erro/texto parcial |
| 5 — SQLite | Chats, mensagens, categorias, busca, migrações e recuperação | Reiniciar e recuperar histórico; pesquisar conteúdo; evitar duplicação após falha; backup/restauração |
| 6 — Markdown | Tabelas, código com realce e copiar | Copiar texto exato; testar várias linguagens, HTML malicioso e imagens remotas bloqueadas |
| 7 — Materiais | PDF textual, TXT, Markdown, código e notas; importação/remoção local | Verificar extração, encoding, duplicados, tamanho máximo e erro em PDF sem texto |
| 8 — RAG | Embeddings, índice persistente, retrieval e fontes | Perguntar sobre fato exclusivo do material e conferir fonte; testar sem resultado, exclusão, reindexação e prompt injection |
| 9 — Cursos | Módulos, lições, quizzes e progresso | Criar curso de redes; concluir lição e preservar progresso; separar proposta gerada de conteúdo validado |
| 10 — Laboratórios | Roteiros guiados com pré-requisitos, isolamento, resultados e defesa | Revisar um laboratório local ponta a ponta, sem executor de comandos |
| 11 — Memória | Opt-in, sugestões confirmadas, consulta, edição e limpeza | Desligar impede leitura/escrita; apagar remove dado; teste de isolamento por usuário |
| 12 — EXE | Sidecar Python, instalador, recursos locais e instruções | Instalar em Windows limpo; iniciar/fechar processos corretamente; operar offline com modelo instalado; verificar atualização e preservação dos dados |

Cursos previstos: Network Fundamentals, Linux Fundamentals, Python for Cybersecurity, Ethical Hacking Fundamentals, Web Security, Wireless Security, Active Directory, Malware Analysis, Reverse Engineering e Digital Forensics. Construir primeiro um curso pequeno para validar o formato, depois ampliar o catálogo.

## O que foi criado na Fase 1

| Arquivo | Por que existe |
|---|---|
| `README.md` | Ponto de entrada do portfólio; informa estado real e compromissos |
| `docs/arquitetura.md` | Explica decisões, camadas, comunicação, dados e privacidade |
| `docs/ambiente-e-modelos.md` | Registra evidências do ambiente, instalações futuras, candidatos e consumo estimado |
| `docs/plano-de-fases.md` | Define sequência e critérios observáveis de conclusão |
| `.gitignore` | Evita versionar dependências, builds e formatos comuns de dados locais; não substitui revisão antes de publicar |

Nenhum desses arquivos executa inferência. Ainda não existem funções Python/TypeScript a explicar. Quando `main.py` for criado, explicaremos suas funções, imports, inicialização e ligação com as rotas; fazer isso agora seria descrever código inexistente.

## Como validar esta fase

Abrir o README e seguir seus três links. Conferir se a arquitetura cobre chat, privacidade, histórico, materiais, RAG, modos, memória, cursos e laboratório. Verificar que dependências futuras estão diferenciadas das ferramentas detectadas e que estimativas de memória não são medições.

No terminal do repositório, `git diff --check` verifica problemas de espaços em alterações rastreadas; arquivos novos também precisam de inspeção própria. `git status --short` mostra o conjunto de arquivos criados. Nenhum teste de aplicação pode passar nesta fase, pois ainda não há aplicação. A validação é documental, não funcional.

Limitações atuais: RAM e pré-requisitos nativos não confirmados; nenhuma inferência medida; nenhuma compatibilidade de build/empacotamento testada. Não abrir uma janela agora é o comportamento esperado desta fase, não falha de instalação.

## Conceitos que aparecerão no código

| Conceito | Significado neste projeto |
|---|---|
| API | Contrato pelo qual a interface pede operações ao backend |
| REST | Organização de operações HTTP em recursos, como chats e documentos |
| Backend | Processo que aplica regras, acessa dados e coordena inferência |
| Streaming | Entrega progressiva de partes da resposta |
| SSE | Formato de eventos enviados pelo servidor em uma resposta HTTP contínua |
| NDJSON | Objetos JSON separados por linhas; formato do stream recebido do Ollama |
| WebSocket | Canal bidirecional persistente; não necessário para este primeiro chat |
| SQLite | Banco relacional embutido, com transações e armazenamento em arquivo |
| RAG | Buscar trechos relevantes e fornecê-los ao modelo antes de responder |
| Chunk | Trecho de documento, preservando referência à origem |
| Embedding | Vetor numérico usado para comparar significado aproximado |
| Índice vetorial | Estrutura para encontrar vetores próximos; FAISS cuida desta busca |
| Token | Unidade de texto processada pelo modelo; não equivale sempre a uma palavra |
| Janela de contexto | Limite de tokens que participam de uma geração |
| Quantização | Compressão da representação numérica dos pesos do modelo |
| Sidecar | Executável auxiliar iniciado junto do aplicativo principal |
| Migração | Alteração versionada do esquema do banco de dados |

## Relatório obrigatório após cada fase

Cada entrega deve explicar o comportamento criado, listar arquivos e suas responsabilidades, justificar tecnologias novas, apresentar o fluxo entre componentes, mostrar como testar e documentar erros observados/prováveis com diagnóstico e correção. Para código relevante, explicar funções e bibliotecas de forma conectada ao comportamento.

Separar sempre: o que foi implementado, o que foi testado e o que permanece planejado. Registrar resultados reais, nunca declarar teste não executado como aprovado.

A conclusão do protótipo não equivale a um produto comercial validado. O catálogo inicial é pequeno; resumos de conversas longas foram adiados. A validação em Windows limpo deve ser registrada separadamente dos testes neste computador.
