# Default (ASI)

Tutor desktop de cibersegurança, em português, com inferência local e ensino prático em ambientes autorizados.

**Protótipo experimental 0.14.1 para Windows x64.** Chat, consulta a documentos com fontes, cursos e laboratórios locais. Instalação validada no computador de desenvolvimento; validação em Windows limpo ainda pendente. “ASI” faz parte do nome do projeto e não representa uma capacidade comprovada de superinteligência.

## Para conhecer o projeto

- Interface em português com tema de terminal e personagem animada.
- Inferência local via Ollama; não exige API paga.
- Histórico salvo, recuperação de trechos antigos e continuação de respostas.
- Consulta a materiais com indicação de fontes, quizzes e progresso de aprendizado.

O repositório contém código e documentação. Modelos, materiais pessoais, bancos de conversas, ferramentas locais e instaladores não fazem parte do código publicado. O modelo pode errar e a memória de contexto é limitada. O projeto ainda não é uma versão estável para produção.

### Prévia da interface

Com Node.js instalado, execute `npm.cmd ci` e `npm.cmd run dev`, depois abra `http://127.0.0.1:1420`. Esta prévia permite conhecer a interface; a integração com o backend depende do aplicativo desktop.

Para compilar o aplicativo completo, consulte [Preparar o ambiente desktop](docs/desenvolvimento.md). A instalação de dependências e os downloads iniciais dos modelos precisam de internet; a inferência e a consulta aos materiais são locais.

Inclui acervo local com RAG e fontes, curso introdutório de redes, quizzes, laboratórios guiados e memória opt-in. Agora também recupera trechos antigos relevantes da conversa e permite continuar respostas. Resumos gerados de conversas longas permanecem uma melhoria posterior.

O chat conversa com o Qwen3 instalado nesta máquina, mostra a resposta progressivamente e permite cancelar ou tentar novamente após falhas. Configurações detecta hardware, lista modelos locais e salva modelo/contexto. Conversas, respostas parciais e rascunhos são salvos no SQLite local. Aguarde a indicação de histórico salvo antes de fechar.

Teste com Qwen3 8B Q4_K_M e contexto 32.768: aproximadamente 7,11 GiB de VRAM reportada pelo Ollama e 48,1 tokens/s em resposta curta. Um guia de mais de 10 mil caracteres terminou normalmente em 61 segundos. São medições pontuais, não garantia de desempenho. Consulte o [relatório da Fase 13](docs/fase-13-conversas-longas.md).

## Comece aqui

1. [Arquitetura e fluxo dos componentes](docs/arquitetura.md).
2. [Preparação, dependências e modelos](docs/ambiente-e-modelos.md).
3. [Fases, testes e guia de estudo](docs/plano-de-fases.md).
4. [Fase 2 — arquivos, funções, execução e testes](docs/fase-2-interface.md).
5. [Fase 3 — backend, Ollama, hardware e diagnóstico](docs/fase-3-ollama.md).
6. [Fase 4 — chat, modos, cancelamento e limites observados](docs/fase-4-chat.md).
7. [Fase 5 — SQLite, salvamento, backup e restauração](docs/fase-5-historico.md).
8. [Fase 6 — Markdown, código, cópia e limites](docs/fase-6-markdown.md).
9. [Fase 7 — materiais](docs/fase-7-materiais.md).
10. [Fase 8 — busca local e fontes](docs/fase-8-rag.md).
11. [Fase 9 — cursos](docs/fase-9-cursos.md).
12. [Fase 10 — laboratórios](docs/fase-10-laboratorios.md).
13. [Fase 11 — memória](docs/fase-11-memoria.md).
14. [Fase 12 — empacotamento e validação](docs/fase-12-empacotamento.md).
15. [Fase 13 — conversas longas e respostas completas](docs/fase-13-conversas-longas.md).
16. [Fase 14 — tema terminal e personagem](docs/fase-14-design-terminal.md).

O projeto usa Tauri 2, React e TypeScript na interface, Python/FastAPI no backend e Ollama para inferência. SQLite armazena histórico, materiais, progresso e memória; FAISS realiza a busca vetorial local.

O backend inicia junto do aplicativo em uma porta efêmera de `127.0.0.1`, com credencial por sessão. O Ollama gerenciado usa `127.0.0.1:11434`, com nuvem desativada. A prévia visual usa `127.0.0.1:1420` e não recebe acesso ao backend desktop.

## Executar

Nesta máquina, a versão instalada está em `%LOCALAPPDATA%/Default (ASI)/cyber-ai-tutor.exe`. O instalador gerado localmente fica em `desktop/target/release/bundle/nsis/Default (ASI)_0.14.1_x64-setup.exe` (aproximadamente 1,22 GB). Instalação e reinstalação foram testadas sem alteração dos bancos ou configurações. Esse instalador não é incluído no repositório.

O executável de desenvolvimento compilado está em `desktop/target/release/cyber-ai-tutor.exe`. Abra-o pelo Explorador de Arquivos; ele contém a interface e não precisa do Vite. A versão 0.14 usa os recursos `backend` e `ollama` ao lado do executável; não copie somente o EXE. O instalador foi gerado: consulte o [guia da Fase 12](docs/fase-12-empacotamento.md). Modelos ficam no cache local do usuário e não são incluídos no instalador.

Para desenvolver e ver alterações no código:

```powershell
npm.cmd run desktop
```

Para usar apenas a prévia no navegador, execute `npm.cmd run dev` e abra `http://127.0.0.1:1420`. Não execute as duas opções simultaneamente: ambas utilizam a porta 1420. Em outra máquina, instale as dependências com `npm.cmd ci` e confira os pré-requisitos nativos no guia da Fase 2.

```powershell
npm.cmd test
npm.cmd run build
```

Os comandos acima executam os testes da interface e compilam os arquivos web. `npm.cmd run desktop:build` compila o executável local sem criar instalador; `npm.cmd run desktop:package` prepara o sidecar e gera o instalador. Consulte os pré-requisitos no guia da Fase 12.

## Compromissos

- Inferência, documentos e conversas locais; sem analytics ou telemetria da aplicação.
- Modelos de nuvem e recursos externos desabilitados por padrão.
- Comandos são exibidos e copiados; não executados pelo tutor.
- Ensino ofensivo contextualizado em laboratório, CTF, equipamentos próprios ou ambientes autorizados.
- Erros visíveis, fontes rastreáveis e progresso por fases.
- Nenhum download de modelo sem informar tamanho e orçamento de memória/disco.

## Autoria e condições de uso

A personagem foi fornecida pelo criador do projeto, que declarou sua autoria. Uma licença aberta para o código e a arte ainda não foi escolhida; esta publicação é uma apresentação do protótipo. As licenças dos componentes de terceiros permanecem próprias e estão documentadas em [THIRD_PARTY](docs/THIRD_PARTY.md). Os relatórios de fases registram o desenvolvimento histórico e podem mencionar o nome anterior, Cyber AI Tutor.

O conhecimento recuperado dos documentos complementa o modelo; não treina nem altera seus pesos. Respostas e referências ainda precisam ser verificadas.

## Verificação da versão 0.13

36 testes Python e 34 testes da interface passaram. Testes reais adicionais confirmaram recuperação de um fato após centenas de mensagens e resposta longa concluída sem corte. Build, pacote, instalação e atualização foram validados; os bancos e configurações foram preservados durante a instalação. Testes reais cobriram RAG com fato exclusivo de documento, sidecar empacotado, encerramento normal/abrupto e instalação/reinstalação com dados preservados. A inspeção nativa confirmou cursos, laboratórios e acervo. Esses resultados não substituem testes em outro Windows limpo nem uma avaliação extensa da precisão pedagógica do modelo.
