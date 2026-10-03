# Fase 6 — Markdown, código e copiar

As respostas do tutor agora exibem títulos, listas, citações, tabelas, código inline e blocos de código. Mensagens do usuário continuam como texto literal. O SQLite mantém o Markdown original; nenhuma migração ou alteração de mensagens existentes foi necessária.

## Bibliotecas e funcionamento

Foram adicionados `react-markdown`, `remark-gfm` e `prism-react-renderer`, com suas dependências transitivas registradas no `package-lock.json`. Todas entram no bundle local; renderizar uma resposta não consulta a internet nem baixa modelos.

`react-markdown` converte Markdown em elementos React, sem inserir HTML cru. `remark-gfm` acrescenta tabelas, listas de tarefas e texto riscado. Prism fornece tokens coloridos para as linguagens incluídas no pacote, como Python, JavaScript, TypeScript, JSON, SQL, C/C++, CSS e YAML.

| Arquivo | Funções e responsabilidades |
|---|---|
| `frontend/src/features/chat/MarkdownMessage.tsx` | `MarkdownMessage` renderiza a resposta; `CodeBlock` reconhece blocos, mostra a linguagem e aplica realce; `CopyButton` grava texto no clipboard somente ao clicar e comunica sucesso ou falha. |
| `frontend/src/features/chat/MessageList.tsx` | Usa Markdown nas respostas e oferece Copiar mensagem para obter o conteúdo original, incluindo a marcação Markdown. Mantém estados de streaming, cancelamento e erro. |
| `frontend/src/styles/chat.css` | Estilos de tabelas, títulos, citações, código e controles. Tabelas e código largos têm rolagem horizontal própria. |
| `frontend/src/features/chat/MarkdownMessage.test.tsx` | Testa formatação, cópia exata, conteúdo ativo, imagens bloqueadas, blocos incompletos e falha de clipboard. |

Fluxo: fragmentos do Ollama → texto da mensagem → parser Markdown → elementos React → realce local. O salvamento continua recebendo o texto original, não HTML nem tokens coloridos.

## Cópia e conteúdo incompleto

Copiar código copia apenas o conteúdo do bloco, sem cercas Markdown, rótulos ou números de linha. A quebra de linha estrutural acrescentada pelo conversor é removida; espaços, tabulações e linhas vazias internas permanecem. Como parte da interpretação CommonMark, CRLF é normalizado pelo parser e indentação estrutural de blocos Markdown pode ser removida. Copiar mensagem preserva a string completa recebida, incluindo suas cercas e marcação.

O botão informa Copiado depois de concluir. Se o Windows/WebView negar o clipboard, aparece uma orientação para selecionar o texto e usar Ctrl+C. Copiar não executa comandos. Durante o streaming, o botão copia o conteúdo disponível naquele instante. Uma cerca ainda não fechada é renderizada como bloco parcial e atualizada nos próximos fragmentos.

## HTML, imagens e referências

HTML recebido é mostrado como texto, nunca interpretado como elementos ativos. Não usamos `dangerouslySetInnerHTML` nem plugins para habilitar HTML cru. Imagens Markdown viram uma indicação textual, sem criar elementos `img`, inclusive URLs remotas, caminhos locais e dados embutidos. Referências aparecem como texto com endereço, sem navegação automática ou links executáveis. A CSP local existente permanece ativa.

As propriedades e modelos do SQLite continuam iguais; o histórico salvo na Fase 5 passa a ser formatado ao abrir a versão v0.6.

## Como testar

1. Peça ao tutor uma tabela de permissões Linux, uma lista e um exemplo Python em bloco de código.
2. Confira títulos, células e cores. Role horizontalmente um bloco largo sem deslocar a página inteira.
3. Clique Copiar código e cole em um editor de texto: os espaços e tabs devem permanecer, sem as cercas Markdown.
4. Clique Copiar mensagem: o resultado deve incluir o Markdown original.
5. Observe uma resposta em streaming e cancele: o trecho parcial continua legível e copiável.
6. Feche após a indicação de histórico salvo e reabra: a mesma resposta deve continuar formatada.

Comandos:

```powershell
npm.cmd test
npm.cmd run format:check
npm.cmd run desktop:build
```

## Limites e diagnóstico

- Linguagens não incluídas no Prism, como Bash e PowerShell nesta versão, usam texto simples com o mesmo botão Copiar. Nenhum carregamento remoto de gramáticas acontece.
- Blocos acima de 20.000 caracteres também usam texto simples para limitar o custo do realce.
- Fórmulas LaTeX, Mermaid e execução de código não fazem parte desta fase.
- O conteúdo técnico continua dependendo da qualidade do modelo. Formatação não valida comandos nem corrige afirmações.
- O build web informou um chunk de aproximadamente 503 kB minificado (157 kB gzip). É incluído no EXE local; carregamento sob demanda pode ser acrescentado caso medições indiquem necessidade.
- `npm audit` informou dois alertas moderados na cadeia de testes existente (`vitest` / `@vitest/mocker`), sem correção na linha instalada. Não pertencem às dependências de produção adicionadas. Uma atualização de versão principal do Vitest deve ser tratada separadamente; não foi aplicado `audit fix --force`.

## Referências consultadas

- [API e segurança do react-markdown](https://github.com/remarkjs/react-markdown).
- [API e linguagens do prism-react-renderer](https://github.com/FormidableLabs/prism-react-renderer).

A próxima fase adiciona importação local de materiais: PDF textual, TXT, Markdown, código e notas.
## Resultado da validação

Na Fase 6, passaram 25 testes da interface (incluindo oito novos casos de Markdown/cópia), verificação de formatação e compilação nativa v0.6.0. O backend não foi alterado nesta fase. Na janela do Windows, o histórico anterior foi recuperado e exibido com títulos, listas e blocos de código; Copiar código concluiu e exibiu Copiado. As tabelas e a preservação exata do texto copiado foram verificadas nos testes automatizados.

Na atualização, foi encontrado um processo Ollama órfão da sessão anterior ocupando a porta 11434. Ele foi identificado pelo caminho do runtime deste projeto, PID, instante de criação e pai já inexistente, e encerrado individualmente. Não foi encerrada uma instalação externa do Ollama. Isso registra uma limitação de encerramento a investigar se voltar a ocorrer.
