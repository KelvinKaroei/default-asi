# Fase 2 — interface desktop

## O que esta entrega faz

A interface tem tema escuro, uma área central de conversa e uma barra lateral com novo chat, categorias, busca na sessão, base de conhecimento e configurações. Há quatro sugestões para começar um estudo; escolher uma preenche o campo, seleciona assunto/modo e permite editar antes de enviar.

Os sete modos estão disponíveis no seletor: Tutor, Explicar, Laboratório, Quiz, Depurar, Analisar e Curso. Nesta fase, selecionar um modo apenas altera o estado da interface e o rótulo da mensagem; ainda não executa um comportamento de IA.

Enter insere uma nova linha; Ctrl+Enter envia. Enviar em branco está desabilitado. Cada conversa guarda seu próprio rascunho, modo e mensagens. A busca encontra título e conteúdo das mensagens da sessão e pode ser combinada com as categorias.

**Ainda é uma demonstração:** a resposta é um texto fixo explicitamente identificado. Não há Ollama conectado, geração, streaming, importação de arquivos ou SQLite. Nenhuma mensagem é enviada para a rede; fechar ou recarregar a janela perde as conversas. As telas de materiais e configurações mostram os recursos futuros como indisponíveis, sem fingir importações ou detecção de modelos.

## Por que estas tecnologias

- React divide a tela em componentes e atualiza apenas a representação necessária quando o estado muda.
- TypeScript verifica se dados e funções seguem contratos, por exemplo os sete valores possíveis de `Mode`.
- Vite serve a interface durante desenvolvimento e produz HTML/CSS/JavaScript para distribuição. O servidor de desenvolvimento fica apenas em `127.0.0.1`.
- Tauri cria a janela Windows e mostra os arquivos da interface usando WebView2. O executável compilado usa os arquivos embutidos; não precisa manter o Vite aberto.
- Rust compila a camada nativa do Tauri. Não é o modelo de IA nem o backend Python.
- Lucide fornece ícones SVG empacotados com o código, sem buscar imagens externas.
- Vitest, Testing Library e jsdom validam comportamentos da interface em um ambiente de teste. Não substituem abrir a janela real.
- Prettier organiza a formatação para tornar a leitura do código consistente.

## Arquivos e responsabilidades

| Arquivo | Responsabilidade |
|---|---|
| `package.json` | Dependências JavaScript e comandos de desenvolvimento, build e testes |
| `package-lock.json` | Versões exatas resolvidas para repetir a instalação com `npm ci` |
| `frontend/index.html` | Documento inicial com idioma, título e ponto de montagem do React |
| `frontend/vite.config.ts` | Diretório frontend, portas locais, saída `dist` e ambiente de testes |
| `frontend/tsconfig.json` | Configuração de tipagem estrita e compilação TypeScript |
| `frontend/src/main.tsx` | Monta `App` no elemento `root` e carrega os estilos |
| `frontend/src/App.tsx` | Coordena tela atual, filtros, navegação e ligação dos componentes |
| `frontend/src/types.ts` | Define `Chat`, `Message`, `Mode`, `Category`, `Page` e catálogo dos modos |
| `frontend/src/components/Sidebar.tsx` | Barra lateral, lista filtrada, pesquisa e navegação |
| `frontend/src/features/chat/useChatSession.ts` | Estado das conversas, criação, alteração e envio simulado |
| `frontend/src/features/chat/Welcome.tsx` | Tela inicial com sugestões de perguntas |
| `frontend/src/features/chat/Composer.tsx` | Campo de mensagem, atalhos, seleção de modo e botão enviar |
| `frontend/src/features/chat/MessageList.tsx` | Exibição das mensagens como texto e rolagem até a última |
| `frontend/src/features/Knowledge.tsx` | Estado vazio da base e indicação das fases de importação/RAG |
| `frontend/src/features/Settings.tsx` | Estado do modelo, tema, atalhos, memória e persistência |
| `frontend/src/styles.css` | Importa os estilos separados por responsabilidade |
| `frontend/src/styles/base.css` | Variáveis de cor, tipografia, controles e foco visível |
| `frontend/src/styles/sidebar.css` | Estrutura da janela e barra lateral |
| `frontend/src/styles/chat.css` | Cabeçalho, tela inicial, mensagens, campo e rodapé |
| `frontend/src/styles/pages.css` | Telas de materiais e configurações |
| `frontend/src/styles/responsive.css` | Adaptação a tamanhos menores e preferência por menos animação |
| `frontend/src/App.test.tsx` | Testes de comportamento observável pelo usuário |
| `frontend/src/test/setup.ts` | Limpeza entre testes e substituição de rolagem não implementada pelo jsdom |
| `desktop/Cargo.toml` / `Cargo.lock` | Dependências Rust declaradas e versões resolvidas |
| `desktop/build.rs` | Executa a preparação de recursos do Tauri na compilação |
| `desktop/src/main.rs` | Inicializa e mantém o loop de eventos da janela nativa |
| `desktop/tauri.conf.json` | Nome, tamanho da janela, frontend, política de conteúdo e permissões |
| `desktop/icon.svg` e `desktop/icons/` | Ícone original vetorial e versões geradas para Windows |
| `scripts/desktop.mjs` | Inicia o Tauri na pasta correta e reconhece o Rust isolado deste projeto |
| `.prettierrc.json` / `.prettierignore` | Regras de formatação e arquivos gerados que não devem ser formatados |

Pastas `node_modules`, `.tools`, `dist`, `desktop/target` e `desktop/gen` são geradas/locais e ignoradas pelo Git. Não publicar dependências ou compiladores no repositório.

## Como as funções se comunicam

```text
main.tsx → App
             ├── useChatSession → chats + conversa ativa
             ├── Sidebar → callbacks de navegação/filtro/criação
             ├── Welcome → preencher rascunho, assunto e modo
             ├── MessageList → mostrar mensagens recebidas por props
             └── Composer → editar rascunho ou chamar send()

Rust/Tauri → janela WebView2 → HTML/CSS/JS gerados pelo Vite
```

`props` são os dados e funções que um componente recebe. Um callback é uma função passada para ser chamada quando acontece uma ação. O estado fica no React; a interface representa esse estado.

Em `useChatSession.ts`, `createChat()` cria uma conversa vazia com identificador aleatório. `useChatSession()` usa `useState` para guardar a lista e identificar a conversa ativa. `updateActive()` altera somente a conversa atual; `newChat()` adiciona uma conversa independente; `send()` valida o texto, cria a mensagem do usuário e a resposta fixa, define o título na primeira mensagem e limpa o rascunho. Nenhuma dessas funções usa `fetch`, executa shell ou grava banco.

Em `App.tsx`, `navigate()` muda de página e fecha o menu compacto. `startChat()` cria uma conversa no filtro atual e limpa a pesquisa para que a nova conversa apareça. `useRef` mantém uma referência ao campo de texto; uma sugestão consegue colocá-lo em foco sem buscar elementos pelo documento inteiro.

`Composer` usa `forwardRef` para permitir esse foco. Seu `onKeyDown` envia somente com Ctrl+Enter e ignora composição de texto IME. O botão recebe `disabled` se o texto contém apenas espaços. O máximo de 12 mil caracteres é um limite de interface desta demonstração, não a janela de contexto de um modelo.

`MessageList` recebe mensagens, usa `useEffect` para rolar quando a lista muda e deixa o React escapar HTML. Um texto como `<script>` aparece literalmente; não se torna um programa. Markdown completo ficará para a Fase 6.

`Sidebar` filtra a lista por categoria e por texto em português, sem diferenciar maiúsculas/minúsculas. O filtro muda a lista da lateral; a conversa central continua aberta até você selecionar outra. As categorias são organização das conversas, não filtros de conteúdo técnico.

No menu compacto, um efeito coloca o foco no primeiro botão, mantém Tab dentro do menu e fecha com Escape. Ao fechar, devolve o foco ao elemento anterior. `useCallback` estabiliza a função de fechamento para não reiniciar esse efeito a cada letra digitada na busca. Em telas baixas, os detalhes decorativos da barra lateral são ocultados para preservar a navegação.

O `main()` Rust chama `tauri::Builder::default()`, carrega a configuração com `generate_context!()` e inicia o loop com `run()`. Não há comandos Rust expostos à interface nesta fase. A lista de capabilities está vazia: a UI não precisa de acesso a terminal, arquivos ou rede nativa para esta demonstração.

`desktop.mjs` usa apenas bibliotecas nativas do Node: `fs` identifica o Rust local, `path`/`url` resolvem caminhos e `child_process.spawn` inicia a CLI do Tauri com argumentos separados, sem montar comando de shell. As variáveis de ambiente alteradas existem só no processo iniciado, sem mudar o PATH do Windows.

## Como iniciar e testar

Preparação realizada nesta máquina: dependências npm locais, Rust 1.98.1 em `.tools`, Visual Studio Build Tools 2022 com ferramentas C++ MSVC e Windows SDK 10.0.26100.0. O WebView2 153.0.4234.48 já estava instalado. O Rust não foi adicionado ao PATH global; o launcher configura somente o processo filho. Nenhum modelo de IA foi instalado e não foi necessário reiniciar automaticamente o Windows.

Abra um PowerShell na raiz do projeto. Com as dependências já instaladas:

```powershell
npm.cmd run desktop
```

Esse comando compila a camada nativa na primeira execução, inicia o Vite local e abre a janela. Compilações futuras reaproveitam o cache. Use apenas uma instância do servidor de desenvolvimento por vez.

Para inspecionar somente a interface no navegador:

```powershell
npm.cmd run dev
```

Acesse `http://127.0.0.1:1420`. O sufixo `.cmd` evita depender da política de execução de scripts PowerShell; não é preciso desabilitar essa proteção.

Verificações automatizadas:

```powershell
npm.cmd test
npm.cmd run build
```

`test` executa os cenários; `build` verifica tipos e gera os arquivos de produção em `dist`. Para compilar um executável local sem criar instalador:

```powershell
npm.cmd run desktop:build
```

O resultado esperado é `desktop/target/release/cyber-ai-tutor.exe`. O instalador, assinatura e distribuição continuam na Fase 12; gerar um binário de desenvolvimento não equivale a entregar o empacotamento final.

Em outra máquina, executar `npm.cmd ci` primeiro instala as versões do lockfile. Rust MSVC, Microsoft C++ Build Tools/Windows SDK e WebView2 também são necessários para compilar no Windows. O Rust dentro de `.tools` é uma conveniência desta máquina e não será distribuído via Git.

Teste manual: preencher uma mensagem multilinha; enviar; trocar de modo; criar outro chat; voltar ao primeiro; buscar uma palavra da mensagem; abrir configurações e materiais. Confirmar que a mensagem da IA diz “demonstração”, que nenhum modelo está carregado e que recarregar elimina a sessão.

## Erros encontrados ou previstos

| Sintoma | Causa/diagnóstico | Correção |
|---|---|---|
| `EACCES` ao baixar dependências nesta sessão | Restrição do ambiente de execução ao registro npm/cache | A instalação foi repetida com autorização de execução; não desabilitar antivírus ou proteções do Windows |
| esbuild não consegue ler diretório ancestral | Restrição de leitura do ambiente desta tarefa | Executar build em terminal autorizado; o TypeScript em si não apresentou erro |
| `cargo` não encontrado | Rust ausente ou fora do PATH | O launcher reconhece `.tools/cargo/bin`; fora desta máquina, instalar Rust MSVC oficialmente |
| npm não encontrado dentro do Tauri | No Windows a variável pode se chamar `Path`, e duplicá-la como `PATH` pode perder os diretórios herdados | Corrigido: o launcher reutiliza a capitalização da chave existente |
| `link.exe` ou biblioteca do Windows ausente | Ferramentas C++/SDK não instaladas por completo | Aguardar/verificar instalação dos componentes oficiais; não copiar DLLs aleatórias |
| Porta 1420 ocupada | Outra prévia Vite em execução | Encerrar a própria prévia com Ctrl+C antes de `npm run desktop`; não encerrar processos desconhecidos |
| Janela sem conteúdo | Build frontend ausente, erro JS ou WebView2 indisponível | Verificar terminal, rodar `npm run build`, confirmar runtime WebView2 |
| Conversas sumiram ao fechar | Estado em memória por decisão da Fase 2 | Persistência será implementada na Fase 5; não usar a demonstração para guardar notas importantes |
| “Não conectado” nas configurações | Integração Ollama ainda não implementada | Estado esperado até a Fase 3 |

Os dois erros iniciais da suíte eram de teste: o nome “Nova conversa” correspondia tanto ao botão de criar quanto ao item da lista; e o matcher de valor não aceitava a comparação parcial utilizada. O botão recebeu nome acessível específico e a comparação foi corrigida. Os sete cenários passaram na execução seguinte.

A primeira tentativa nativa encontrou `link.exe` ausente porque a instalação C++/SDK ainda estava em andamento. Após a conclusão informada pelo instalador e a detecção pelo `vswhere`, a compilação pôde prosseguir. Os downloads Rust foram limitados ao alvo Windows; a compilação seguinte usou `CARGO_NET_OFFLINE=true`, aproveitando os pacotes já baixados.

Logs estruturados em arquivo serão introduzidos com o backend na Fase 3. Nesta etapa, erros de build/teste aparecem no terminal e os estados de indisponibilidade aparecem na interface. Não há registro de conteúdo de mensagens.

## Validação desta entrega

- TypeScript e build Vite: aprovados na primeira compilação com acesso ao diretório.
- Suíte de interface: 7 testes aprovados.
- Navegador local: tela inicial e configurações conferidas visualmente; sugestão + Ctrl+Enter confirmados.
- Build Tauri de produção: aprovado, perfil `release`, sem instalador, usando dependências já baixadas.
- Janela nativa Windows: executável aberto e tela inicial conferida; WebView2 carregou `http://tauri.localhost/`, o endereço interno dos arquivos embutidos, sem usar a URL do Vite.
- Sugestão + Ctrl+Enter na janela nativa: pergunta e resposta fixa de demonstração apareceram corretamente no modo Explicar.
- Layout compacto 760 × 620: navegação conferida; menu fecha com Escape e restaura o foco.
- Formatação e referências locais dos documentos: verificadas.

Executável produzido: `desktop/target/release/cyber-ai-tutor.exe`. A Fase 2 está concluída. A próxima fase adicionará o backend Python, a detecção de hardware e a conexão ao Ollama; nenhum desses recursos foi antecipado nesta entrega.

Fontes oficiais: [Tauri — pré-requisitos](https://v2.tauri.app/start/prerequisites/), [configuração Tauri](https://v2.tauri.app/reference/config/) e [Vite](https://vite.dev/guide/).
