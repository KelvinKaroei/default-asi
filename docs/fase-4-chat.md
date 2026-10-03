# Fase 4 — conversa real, streaming e cancelamento

O chat agora envia perguntas ao Qwen3 instalado neste computador. A resposta aparece progressivamente, pode ser interrompida e mantém o texto recebido caso o servidor falhe. Nenhuma dependência nova foi instalada nesta fase.

## Fluxo e conceitos

```text
Composer → useChatSession → POST /api/v1/chat autenticado
         → FastAPI → POST /api/chat do Ollama → Qwen3 na GPU
         ← eventos NDJSON ← fragmentos de texto
```

Streaming significa receber partes da resposta antes de ela terminar. NDJSON é uma sequência de objetos JSON separados por quebras de linha. Um pacote de rede não corresponde necessariamente a um objeto nem a um caractere completo: `TextDecoder` preserva caracteres UTF-8 divididos entre pacotes e o leitor junta linhas antes de interpretar JSON.

Os eventos da aplicação são `start` (modelo e contexto omitido), `delta` (texto novo), `done` (fim e métricas) e `error` (falha explícita). Fechar a conexão sem receber `done` é tratado como interrupção, não sucesso. O histórico e os tokens de autenticação não entram nos logs.

## Arquivos e funções

| Arquivo | O que faz e como se conecta |
|---|---|
| `backend/app/chat.py` | `ChatRequest` e `Turn` validam modo e mensagens; não aceitam mensagens de sistema vindas do cliente. `prepare_messages` constrói o prompt didático e escolhe pares recentes que cabem no orçamento. `chat_response` coordena uma geração, traduz eventos e trata erros. `CancellableResponse` observa a desconexão mesmo durante a espera pelo primeiro token e fecha o gerador. |
| `backend/app/server.py` | Registra `POST /api/v1/chat`, usa uma cópia da configuração selecionada e compartilha a trava de geração com o diagnóstico. Permite até 64 KiB nesta rota; as outras mantêm 8 KiB. |
| `backend/app/runtime.py` | `chat_stream` abre o stream HTTP local do Ollama e interpreta seus eventos. Sair do contexto fecha a resposta HTTP, inclusive quando o usuário cancela. |
| `frontend/src/services/backend.ts` | `localFetch` reutiliza a sessão autenticada do Tauri. Não envia perguntas a serviços externos. |
| `frontend/src/services/chat.ts` | `streamChat` envia modo/histórico com sinal de cancelamento; `consumeStream` recompõe UTF-8/NDJSON, entrega fragmentos e exige um evento final. |
| `frontend/src/features/chat/useChatSession.ts` | `generate` cria o par pergunta/resposta e fixa os IDs da conversa e mensagem. Cada fragmento atualiza esses IDs, mesmo que o usuário navegue para outra conversa. `cancel` aborta a requisição; `retry` substitui a última tentativa incompleta por uma nova tentativa da mesma pergunta. |
| `frontend/src/features/chat/Composer.tsx` | Ctrl+Enter envia uma vez; durante a geração, o botão vira Parar. O rascunho continua editável para preparar a próxima pergunta. |
| `frontend/src/features/chat/MessageList.tsx` | Exibe texto real, estado de geração, cancelamento, erro, contexto omitido e velocidade. HTML recebido permanece texto, sem execução. |
| `frontend/src/App.tsx` | Liga os controles ao estado da conversa; permite parar também ao navegar para Configurações ou Materiais. |
| `scripts/verify-chat.py` | Testa geração real fragmentada, cancelamento, nova geração e interrupção intencional apenas dos processos Ollama criados por esse teste. |

FastAPI/Pydantic continuam responsáveis pelo contrato HTTP; HTTPX mantém a conexão assíncrona com o Ollama; AnyIO, já instalado como dependência do FastAPI, coordena streaming e desconexão. React mantém o estado visível e `AbortController` comunica o cancelamento ao navegador. A aplicação ainda não executa comandos sugeridos pelo modelo.

## Modos do tutor

| Modo | Instrução principal |
|---|---|
| Explicar | Conceito, motivo, funcionamento, exemplo e erros comuns. |
| Tutor | Etapas curtas e pergunta de compreensão. |
| Laboratório | Objetivo, requisitos, passos explicados, resultados, limpeza e defesa. |
| Quiz | Uma pergunta por vez; aguarda resposta antes da solução. |
| Depurar | Evidências, hipóteses verificáveis e correção explicada. |
| Analisar | Distingue evidência, hipótese, impacto e mitigação. |
| Curso | Propõe módulos e exercícios; não afirma salvar progresso inexistente. |

Esses modos são instruções ao modelo, não sete modelos diferentes. Eles não garantem precisão. O prompt pede português, explicação de comandos, transparência sobre incertezas e exercícios em ambientes próprios/autorizados. Não há executor de ferramentas ou terminal nesta fase.

## Contexto e memória

As conversas continuam somente na memória da janela. Trocar de conversa preserva mensagens e rascunhos; fechar ou recarregar ainda apaga a sessão. A persistência SQLite pertence à Fase 5.

Cada envio inclui somente pares concluídos da conversa atual. Respostas canceladas ou com erro não são usadas como se fossem conclusões válidas. O transporte leva no máximo dez pares recentes, com redução adicional de tamanho; o backend aplica o orçamento final e informa quantas mensagens ficaram fora. Isso não apaga o histórico visível.

O orçamento de entrada é deliberadamente conservador: conta bytes UTF-8, reserva margem para o template e deixa até 1024 tokens para saída (512 no contexto 2048). Não há tokenizador específico do modelo nesta etapa. Isso pode descartar histórico antes de atingir a capacidade real do Qwen3. Perguntas que excedem o orçamento recebem orientação para dividir o conteúdo ou aumentar o contexto. Não existe memória ilimitada ou RAG oculto.

Contexto 4096 permanece como padrão. Somente uma geração fica ativa por vez; o teste de diagnóstico usa a mesma trava. Modelo, contexto e modo são capturados no início da requisição: mudanças posteriores valem para o próximo envio.

## Como testar

Abra `desktop/target/release/cyber-ai-tutor.exe` mantendo a pasta do projeto no mesmo local. O EXE ainda depende de `.venv`, `backend` e `.tools/ollama`. A aba Vite é apenas uma prévia visual e não recebe a sessão autenticada do desktop.

1. Confira `qwen3:8b` selecionado em Configurações.
2. Abra uma conversa, escolha Explicar e pergunte “Qual a diferença entre TCP e UDP?”.
3. Use Ctrl+Enter e observe a resposta aparecer progressivamente.
4. Solicite uma explicação longa; pressione Parar e confira o texto parcial e a indicação de cancelamento.
5. Use Tentar novamente para substituir essa tentativa, ou envie outra pergunta.
6. Durante uma geração, abra uma nova conversa. Os fragmentos devem continuar pertencendo à conversa original.

Testes automatizados:

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run format:check
Push-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Pop-Location
```

Para o teste real de falhas, feche o aplicativo e rode:

```powershell
.venv\Scripts\python.exe scripts/verify-chat.py
```

Esse script interrompe intencionalmente o Ollama que ele próprio iniciou. Não use uma janela do tutor simultaneamente, pois ambos precisam da porta 11434. Ele não encerra uma instalação externa do Ollama.

## Erros e limites observáveis

- **Nenhum modelo selecionado:** abra Configurações, selecione um modelo instalado e salve. Use Tentar novamente depois.
- **Já existe uma geração:** aguarde ou cancele a anterior. Após cancelar, o servidor pode precisar de instantes para fechar a conexão e liberar a trava.
- **Pergunta longa para o contexto:** divida a pergunta. Aumentar contexto exige mais memória; os limites de transporte não representam a quantidade que o modelo consegue ler.
- **Falha ou conexão encerrada antes do fim:** o texto parcial fica visível com erro. Nenhuma nova tentativa acontece automaticamente.
- **Tempo limite:** há limite total de cinco minutos no backend e timeout de leitura de dois minutos sem eventos do Ollama. Reduza contexto ou verifique memória/modelo.
- **Saída limitada:** o modelo recebe até 1024 tokens de saída; quando informa esse motivo de término, a interface sinaliza o limite.
- **Formatação crua:** Markdown e realce de código são da Fase 6. Nesta fase, símbolos Markdown podem aparecer literalmente.

## Validação e qualidade das respostas

Quatorze testes Python e quatorze testes React/TypeScript passaram. Eles cobrem contratos, autenticação, contexto, UTF-8 fragmentado, fim inesperado, cancelamento antes do primeiro token, isolamento entre conversas, bloqueio de envio duplicado e nova tentativa sem duplicar a pergunta.

No primeiro teste real, a resposta veio em 68 fragmentos, primeiro fragmento em 6,5 segundos e geração de 35,1 tokens/s. Após cancelar uma geração, a seguinte terminou em 0,53 segundo. Esses números dependem da pergunta e do carregamento e não são garantia de latência constante.

A avaliação de conteúdo encontrou imprecisões: o modelo descreveu TCP como adequado a “transferências seguras”, confundindo confiabilidade com segurança, e em outra resposta chamou UDP genericamente de “ineficiente”. TCP não oferece criptografia por si só; confiabilidade, latência e eficiência dependem de mecanismos e requisitos distintos. O prompt foi reforçado para distinguir esses conceitos, mas isso não eliminou todas as imprecisões. O teste funcional confirma o chat, não certifica domínio técnico do modelo. Validar qualidade em um conjunto maior de perguntas é trabalho adicional, distinto de validar o software.

O backend/runner só usam loopback e o runtime mantém nuvem desativada, conforme a Fase 3. Nenhum peso novo foi baixado nesta fase.

Contrato externo consultado: [API de chat oficial do Ollama](https://docs.ollama.com/api/chat).

### Revalidação em 28/09/2026

Na janela nativa v0.4, Ctrl+Enter enviou uma pergunta sobre `chmod 755`, com resposta real do Qwen3 a 41,6 tokens/s. Uma segunda resposta longa apareceu progressivamente; o botão Parar interrompeu a geração, manteve o texto parcial e exibiu “Geração cancelada” e “Tentar novamente”. Os 28 testes automatizados e a verificação de formatação passaram. O build nativo desta fase já havia sido compilado; a correção final do backend Python é carregada diretamente da pasta do projeto.

O teste real entregou 68 fragmentos, com primeiro fragmento em 7,74 segundos e geração de 45,4 tokens/s. Após cancelar, uma nova geração terminou em 0,36 segundo. A interrupção forçada do Ollama preservou o texto parcial e retornou erro explícito. Ao encerrar o backend, nenhum processo próprio sobreviveu.

Foi corrigido um vazamento observado durante esse teste: se o processo pai do Ollama morresse antes do fechamento, seu processo de inferência podia permanecer ativo. `remember_processes` e `watch_processes` agora guardam as identidades dos descendentes enquanto o pai está vivo; `stop_process` encerra essas identidades mesmo após a morte do pai. Um teste com processos reais cobre esse caso, e outro confirma que processos externos permanecem ativos.
