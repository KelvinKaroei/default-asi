# Fase 9 — Cursos e progresso

Primeiro curso autoral: Fundamentos de redes, com dois módulos, três lições e um quiz por lição. O catálogo amplo da arquitetura permanece uma expansão editorial, não dez cursos completos já produzidos. Planos propostos no modo Curso do chat são identificados como propostas e não entram automaticamente no conteúdo estruturado.

`backend/app/curriculum.py` contém o conteúdo introdutório e gabaritos. `learning.py` expõe curso, conclusão de leitura e tentativa de quiz. Não envia gabarito na leitura inicial; a tentativa retorna correção e explicação. `Courses.tsx` mostra módulos, lições, progresso e alternativas, e prepara um rascunho para aprofundar com o tutor sem enviá-lo automaticamente.

SQLite em `learning.sqlite3` registra conclusão, número de tentativas e se houve acerto. Concluir leitura não aprova quiz. Uma resposta errada posterior não apaga um acerto anterior. O registro é de estudo, não uma certificação. Escolhemos conteúdo estático inicial para testar a estrutura sem misturar geração não revisada com conteúdo do curso.

Fluxo: abrir curso → GET local → ler → PUT de conclusão ou POST de tentativa → transação SQLite → atualizar progresso. O tutor usa o chat existente para dúvidas.

Validação: testes de persistência após reabrir, tentativa incorreta/correta, alternativa inválida, lição inexistente e independência entre leitura e quiz. Teste manual: marque uma leitura, responda ao quiz e reabra o aplicativo. Se salvar falhar, a interface mantém o erro e não declara progresso confirmado. Botão de tentar novamente recarrega o estado persistido.
