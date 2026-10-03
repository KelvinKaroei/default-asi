# Fase 5 — histórico persistente com SQLite

Conversas, mensagens, rascunhos, categorias e modos agora permanecem no computador após fechar o tutor. Nenhuma dependência ou modelo novo foi instalado: o módulo `sqlite3` faz parte do Python já usado pelo backend.

## Onde ficam os dados

- Banco: `%LOCALAPPDATA%\CyberAITutor\history.sqlite3`.
- Último backup solicitado: `history.backup.sqlite3`, na mesma pasta.
- Cópia anterior à última restauração: `history.before-restore.sqlite3`.

Esses arquivos contêm o texto das conversas sem criptografia própria. Permanecem locais e não são enviados à nuvem. Não ficam no repositório. A prévia Vite continua temporária e não acessa o banco do desktop. Conversas de janelas da Fase 4 que já foram fechadas não podem ser recuperadas, pois aquela versão não as gravava.

## Fluxo e arquivos

```text
Edição / fragmento da resposta → estado React
    → useHistory (verifica alterações a cada 750 ms)
    → PUT /api/v1/history autenticado
    → transação SQLite → confirmação de revisão
    → indicador “Histórico salvo neste computador”

Reabertura → GET /history → conversas recuperadas → busca e filtros da sidebar
```

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/history.py` | Valida conversas e mensagens com Pydantic; `HistoryStore.connect` cria/migra o esquema, verifica integridade e recupera respostas interrompidas. `read` mantém ordem; `save` grava uma transação; `backup` usa a API de backup SQLite; `restore` valida o backup e preserva uma cópia anterior. |
| `backend/app/server.py` | Rotas autenticadas de leitura, gravação, backup e restauração. Erros SQLite aparecem como falha explícita, sem apagar o banco. |
| `frontend/src/features/useHistory.ts` | Carrega antes de permitir edição, serializa gravações, mantém a última versão confirmada e permite repetir uma gravação que falhou. |
| `frontend/src/features/chat/useChatSession.ts` | Integra o histórico persistente ao streaming, cancelamento, rascunhos e troca de conversa existentes. |
| `frontend/src/App.tsx` | Mostra estado de salvamento, erro, repetição, criação de backup e confirmação de restauração. |
| `frontend/src/components/Sidebar.tsx` | Busca títulos e conteúdo das mensagens e filtra categorias sobre o histórico carregado. |
| `backend/tests/test_history.py` | Reinício, resposta parcial, transação interrompida, repetição, conflito, corrupção, autenticação e restauração. |
| `frontend/src/features/useHistory.test.ts` | Carregamento antes da gravação, resposta de rede perdida e preservação dos dados quando a leitura falha. |

## Banco, migrações e recuperação

O esquema v1 usa `PRAGMA user_version`. As tabelas `chats` e `messages` preservam IDs e posições; mensagens referenciam sua conversa por chave estrangeira. Campos de apresentação ficam em JSON validado. `meta` guarda a revisão e o identificador da última gravação. Versões desconhecidas são rejeitadas, sem tentar converter ou recriar o arquivo.

A gravação substitui o snapshot completo dentro de uma transação: ou todas as alterações entram, ou o histórico anterior permanece. O banco não recebe um DELETE isolado fora dessa transação. A busca atual acontece na interface, incluindo mensagens, e não usa índice FTS.

A interface envia a revisão que leu. Se outra janela gravou antes, recebe conflito e não sobrescreve silenciosamente. Se a gravação foi confirmada no banco, mas a resposta se perdeu, a nova tentativa reutiliza o identificador original: isso evita duplicação. Alterações feitas enquanto a requisição estava em andamento são enviadas em seguida.

Respostas salvas com estado `generating` são recuperadas como canceladas ao iniciar uma nova instância do backend. O texto parcial fica disponível, e Tentar novamente continua sendo uma ação explícita. Para evitar conflitos, use uma janela do tutor por vez.

## Como usar e testar

1. Abra o EXE v0.5 e envie uma pergunta.
2. Escolha uma categoria, altere o modo e escreva um rascunho para a próxima pergunta.
3. Aguarde “Histórico salvo neste computador”. Feche e reabra o EXE: mensagens, categoria, modo e rascunho devem reaparecer.
4. Busque uma palavra que exista apenas na resposta; a conversa deve aparecer na lista. Confira também os filtros de categoria.
5. Clique Criar backup. Modifique um rascunho, aguarde salvar e escolha Restaurar backup. A confirmação substitui o histórico pelo último backup e guarda uma cópia do estado anterior.
6. Cancele uma geração e reabra: o texto parcial e o estado de cancelamento devem permanecer.

Não feche enquanto aparecer “Salvando histórico”. Existe uma janela de até 750 ms, mais o tempo da requisição, entre uma alteração e sua gravação. Uma queda abrupta pode perder os fragmentos ou caracteres ainda não confirmados; o indicador diferencia o que já foi salvo. Não há promessa de recuperação de texto que nunca chegou ao banco.

## Erros e limites

- **Falha ao carregar:** a tela impede edição e oferece nova tentativa; nunca substitui o histórico ilegível por uma conversa vazia.
- **Falha ao salvar:** as alterações permanecem na janela; use Tentar salvar novamente e confira espaço/permissões antes de fechar.
- **Conflito entre janelas:** o banco preserva a versão mais recente. Copie qualquer texto ainda não salvo antes de fechar a janela em conflito e reabrir.
- **Backup ausente:** crie um backup antes de tentar restaurar. Criar outro backup substitui o backup anterior.
- **Banco corrompido:** o arquivo original é preservado. Com o tutor fechado, guarde uma cópia do arquivo danificado e restaure uma cópia conhecida de `history.backup.sqlite3` com o nome `history.sqlite3`. Não mova nem substitua arquivos com o aplicativo aberto.
- **Volume:** esta etapa carrega e salva o histórico completo, com limite de 8 MiB por gravação, 500 conversas e 10.000 mensagens por conversa. A interface mostra falha se o limite HTTP for excedido. Paginação, gravação incremental e FTS são melhorias futuras para grandes históricos.
- **Privacidade:** backup inclui rascunhos e respostas parciais. O botão de restauração só atua nos arquivos fixos do próprio aplicativo, sem aceitar caminhos arbitrários.

## Validação

Em 30/09/2026, passaram 19 testes Python e 17 testes React/TypeScript (36 no total), a verificação Prettier e o build nativo v0.5.0. Na janela do Windows, uma resposta real do Qwen3 foi cancelada; o texto parcial, a categoria Linux e um rascunho foram salvos. Após fechar e reabrir o EXE, todos reapareceram com o estado de cancelamento preservado. O botão Criar backup confirmou o arquivo local. Restauração e rollback foram verificados nos testes com bancos temporários, sem substituir o histórico real do usuário.

Os testes verificam SQLite real em diretórios temporários, reinício do backend com o mesmo banco, falha durante a transação e preservação de arquivos corrompidos. Testes da interface verificam reenvio idempotente após perda de resposta, carregamento e bloqueio de sobrescrita após erro. Os testes anteriores de streaming, cancelamento, isolamento entre conversas e busca continuam na suíte.

Comandos na pasta do projeto:

```powershell
npm.cmd test
npm.cmd run format:check
npm.cmd run desktop:build
Push-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Pop-Location
```

SQLite persiste histórico; não aumenta a janela de contexto do Qwen3 e não treina o modelo. O orçamento de contexto da Fase 4 continua valendo. A Fase 6 adicionará renderização Markdown, realce de código e copiar.
