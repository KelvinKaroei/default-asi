# Fase 14 — Tema terminal e personagem

Interface inspirada na referência fornecida pelo usuário: fundo preto, verde menta, fonte monoespaçada local, molduras duplas finas e controles retangulares. A barra superior mantém navegação funcional entre chat, cursos, laboratórios, acervo e configurações.

A personagem é exibida diretamente da imagem fornecida, por um viewport SVG que mostra somente seu retrato, sem modificar o arquivo raster. Ocupa 87 × 121 px no rodapé esquerdo, ou 63 × 88 px em janelas baixas. A navegação rola independentemente para manter o retrato no rodapé. Em janelas estreitas, acompanha o menu lateral recolhível.

A animação CSS move exclusivamente duas pequenas regiões dos olhos em um ciclo de nove segundos, sem movimento da cabeça ou do corpo. A preferência de movimento reduzido desliga a animação. A imagem é decorativa e não entra na leitura de telas nem intercepta cliques. Não há dependência nova, API paga, fonte remota ou serviço externo.

A composição foi adaptada às funções do tutor; não reproduz os slogans ou a marca do cartaz na interface. A imagem original fornecida fica em `frontend/src/assets/terminal-reference.jpg` e acompanha o código publicado. Durante o uso do aplicativo, a imagem é carregada localmente.

Validação: build TypeScript/Vite e os 34 testes existentes da interface passaram. Revisão visual em 1280 × 900 e 800 × 620; retrato fixo no rodapé do menu e navegação acessível em janela compacta. Backend e limites de contexto permanecem os da versão 0.13.

Instalação e atualização verificadas com hashes dos arquivos e preservação dos bancos/configurações. Revisão nativa confirmou versão 0.14, personagem no rodapé, nova conversa funcional e Ollama conectado. O aplicativo foi deixado aberto.
