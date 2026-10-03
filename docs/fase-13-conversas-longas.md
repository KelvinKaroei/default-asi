# Fase 13 — Conversas longas e respostas completas

Melhorias locais gratuitas da versão 0.13:

- Contexto padrão de 32.768 tokens, limite de resposta de 8.192 tokens (sempre limitado a metade do contexto selecionado). Configurações permitem reduzir ambos.
- Tokenizador oficial do Qwen3 8B incluído no pacote. Contagem do texto mais margem para o template; outros modelos usam contagem conservadora por bytes. Nenhuma consulta online durante o uso.
- Removido o corte fixo de dez pares de mensagens. O transporte aceita até 8 MiB; a interface reserva margem e envia os pares completos que cabem. O contexto do modelo continua finito.
- Recuperação local por palavras de trechos originais antigos da mesma conversa. Não cruza chats e não gera fatos novos. Não é memória perfeita nem resumo acumulado: referências vagas e mudanças de assunto podem não recuperar o trecho desejado.
- Botão **Continuar resposta** preserva a resposta anterior e o rascunho, acrescenta uma nova parte e inclui o final da resposta anterior mesmo quando ela ultrapassa o contexto. Também serve para respostas antigas e parciais.
- Respostas anteriores com mais de 12 mil caracteres agora podem voltar ao contexto. Perguntas continuam limitadas a 12 mil caracteres.
- Prazo total de geração ampliado para 15 minutos, com cancelamento e preservação do texto parcial.
- Flash Attention e cache KV q8_0 no processo Ollama gerenciado pelo aplicativo. Não altera configurações globais do Windows.

## Verificação no computador de desenvolvimento

Ryzen 5 5600G, RTX 3060 12 GB, 16 GB RAM, Qwen3 8B Q4_K_M. Teste curto com 128 tokens:

| Contexto | VRAM do modelo reportada pelo Ollama | Velocidade de geração |
|---|---:|---:|
| 8.192 | 5,34 GiB | 14,1 tokens/s (primeiro carregamento) |
| 16.384 | 5,95 GiB | 48,2 tokens/s |
| 32.768 | 7,11 GiB | 48,1 tokens/s |

Medições pontuais; outras aplicações e prompts longos afetam desempenho. A VRAM reportada pelo Ollama não inclui toda a memória gráfica do sistema. O cache quantizado pode alterar ligeiramente as respostas. Um limite maior não força respostas longas: o modelo ainda decide quando concluiu. O botão de continuação mantém disponível uma saída quando houver corte.

Testes de regressão verificam orçamento, recuperação de fato exclusivo antigo, isolamento entre conversas, continuidade de respostas acima do orçamento, preservação de rascunhos e validação de mensagens. Scripts de teste real usam somente dados fictícios, sem ler conversas do usuário.

## Dependências e procedência

- Tokenizador: https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer.json
- SHA-256: `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`.
- Licença Apache 2.0 em `backend/assets/Qwen3-LICENSE`, incluída no pacote.
- Biblioteca `tokenizers==0.22.2`; dependências fixadas em `backend/requirements.lock.txt`.
- Cache KV e Flash Attention: https://github.com/ollama/ollama/blob/main/docs/faq.mdx

Sem API paga, assinatura ou modelo novo. Resumo incremental gerado, memória semântica de longo prazo e validação em Windows limpo continuam fora desta entrega.

Teste real com 160 pares intermediários: recuperou VERDE-8362 do primeiro turno, embora 246 mensagens estivessem fora do contexto integral. Um guia de DNS com 10.367 caracteres terminou com o marcador final solicitado, motivo `stop`, em 61,1 segundos e 44,8 tokens/s.

Validação automatizada: 36 testes Python e 34 testes da interface aprovados. A continuação com materiais usa o tema e o final da resposta anterior para buscar fontes. O sidecar distribuível passou na consulta com fonte, progresso do curso e encerramento sem processos restantes.

Instalação e atualização concluídas e verificadas em 3 de outubro de 2026, preservando bancos e configurações. Backend e tokenizador conferidos por SHA-256. No executável nativo, a única diferença esperada é o marcador Tauri de três bytes UNK → NSS aplicado pelo NSIS; o restante é idêntico. Após a instalação, os limites autorizados foram aplicados e uma cópia das configurações anteriores foi preservada. A interface confirmou versão 0.13, Ollama conectado, contexto 32.768 e saída 8.192.

Teste pela interface instalada: conexão local funcionando, 42,6 tokens/s, 6,81 segundos totais e 7,11 GiB de VRAM reportada pelo Ollama. Aplicativo deixado aberto para novos testes.
