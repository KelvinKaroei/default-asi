# Fase 11 — Memória de aprendizado

Opt-in explícito em Configurações. Você escreve uma preferência ou escolhe uma sugestão, revisa e confirma. Pode consultar, editar, apagar uma memória ou limpar todas. A memória começa desligada; não extrai inferências de conversas e não cria perfis automaticamente.

`backend/app/memory.py`: `MemoryStore` cria banco separado, `read` permite inspecionar, `context` retorna texto somente quando ativo e `router` valida alterações. Desligar impede consulta pelo tutor e novas gravações/edições, mas mantém inspeção e exclusão disponíveis. Até três memórias, 160 caracteres cada e 500 bytes UTF-8 no total. O limite reduz disputa por contexto no computador alvo.

`MemoryPanel.tsx` controla opt-in, sugestões editáveis e confirmação de limpeza. `chat.py` consulta preferências no início da geração e as insere como dados do usuário se couberem. Preferências não podem conferir novas capacidades ao aplicativo. Desativar afeta gerações seguintes; uma geração em andamento já recebeu seu contexto.

Fluxo: confirmar preferência → SQLite → próxima pergunta → contexto limitado → modelo local. Não há envio à nuvem. Cada conta do Windows usa sua própria pasta de dados; não existe login multiusuário interno nem banco criptografado. Backups de conversas não incluem o banco de memória, mas respostas anteriores podem ter refletido preferências e não são reescritas ao apagá-las.

Testes verificam opt-in, bloqueio de edição quando desligado, exclusão, reabertura, pastas de usuários isoladas e ausência do texto no payload enviado ao modelo após desativar. Teste manual: salve uma preferência curta, desative, confira a lista e depois apague.

Esta fase não implementa resumos de conversas longas nem recuperação de diálogos antigos. Essa melhoria foi adiada pelo usuário para depois do protótipo original.
