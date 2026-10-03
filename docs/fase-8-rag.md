# Fase 8 — Consulta local com fontes

O chat agora pode buscar trechos no acervo antes de gerar a resposta. Prepare o índice na Base de conhecimento e marque **Consultar materiais** no chat. A opção começa desmarcada a cada abertura. Fontes mostram nome, página e o trecho efetivamente fornecido ao modelo; não certificam que todas as afirmações geradas estejam corretas.

## Conceitos, funções e fluxo

Embedding é uma representação numérica do texto. FAISS compara vetores por proximidade; similaridade não é prova de relevância. O RAG combina essa busca com a geração do modelo, sem retreinar seus pesos.

`backend/app/retrieval.py` contém `Retrieval`: `build` divide páginas em trechos de 420 caracteres, com sobreposição de 80, calcula embeddings em lotes de 16 e constrói IndexFlatIP normalizado; `search` recupera até dois trechos com similaridade mínima 0,55; `status` acompanha progresso e detecta acervo alterado. Limite de 5.000 trechos. São parâmetros iniciais, não calibrados em um conjunto extenso de avaliação.

O modelo multilíngue local embeddinggemma:300m ocupa cerca de 622 MB em disco. FAISS e NumPy processam o índice na CPU. O Ollama limita modelos simultaneamente carregados; alternar busca e geração pode acrescentar latência. Não há download automático pela interface.

`RetrievalPanel.tsx` inicia indexação e consulta progresso. `chat.py` adiciona trechos como dados não confiáveis, pede citações e aplica o orçamento conservador de contexto. O trecho exibido é o mesmo enviado à geração. Trechos que não cabem são descartados. Sem resultado, o backend informa ausência de fonte sem pedir uma resposta inventada ao modelo. `MessageList.tsx` mostra fontes; `history.py` preserva os trechos na conversa.

Documento → extração → trechos → embedding local → índice FAISS → busca da pergunta → contexto → resposta com fontes.

## Integridade e validação

Índice, metadados e checksum ficam no mesmo SQLite do acervo, numa gravação atômica. Mudança do acervo ou do modelo exige reindexação. Exclusão de material remove o índice derivado na mesma transação. Trechos já citados permanecem no histórico e nos backups históricos; remover a origem não reescreve conversas anteriores.

Testes cobrem persistência, busca, fontes, ausência de resultado, acervo alterado, exclusão, checksum e mudança do modelo. Teste real no Qwen3 8B recuperou o código fictício AZUL-7429 de um documento criado só para validação, citou [S1] e mediu 48 tokens/s na geração curta. `backend/smoke_rag.py` reproduz o teste em dados temporários e requer o Ollama local já iniciado.

O teste de prompt injection valida que instruções do documento ficam em dados, não no prompt de sistema. Isso reduz risco, mas não prova imunidade do modelo. Não existem ferramentas de execução na resposta. Confira conteúdo e fontes.

Modelo ausente: instale o modelo de embeddings informado. Índice desatualizado/corrompido: prepare novamente. Acervo alterado durante indexação: operação não substitui o índice anterior e pede repetição. Falta de memória: feche outros aplicativos e reduza o acervo.

Referências: [EmbeddingGemma no Ollama](https://www.ollama.com/library/embeddinggemma), [API de embeddings](https://github.com/ollama/ollama/blob/main/docs/api.md).
