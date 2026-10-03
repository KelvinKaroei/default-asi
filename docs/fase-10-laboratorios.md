# Fase 10 — Laboratórios guiados

Dois roteiros iniciais: conectividade com loopback no Windows e integridade de arquivo com SHA-256. Cada um apresenta objetivo, pré-requisitos, isolamento, passos explicados, resultados esperados, erros comuns, defesa, limpeza e pergunta de compreensão.

`curriculum.py` armazena roteiros. `learning.py` valida IDs e números de etapas e persiste checklist. `Labs.tsx` apresenta comandos com o componente Markdown/copiar já existente. Não há endpoint de execução, terminal integrado ou verificação automática da máquina. Marcar uma etapa é uma declaração do estudante.

Fluxo: selecionar laboratório → ler e copiar → executar manualmente se desejar → marcar etapa → SQLite. O botão para discutir com o tutor prepara uma pergunta no chat. As mesmas tecnologias de cursos e Markdown evitam duplicar armazenamento e renderização.

Testes verificam checklist persistente, etapa inválida e ausência de endpoint executor. Para testar manualmente, marque/desmarque uma etapa e reabra. No laboratório de loopback, a conectividade local não demonstra acesso à internet. No de hash, use arquivo descartável próprio e compare antes/depois de editar; hash sozinho não prova autenticidade. O aplicativo não instala ferramentas nem altera a rede para realizar os exercícios.
