# Fase 12 — Distribuição Windows

O sidecar Python já foi gerado e testado fora da pasta do código, com dados temporários. O instalador NSIS reúne a aplicação e seus recursos. Consulte o README do projeto para o estado mais recente da validação. Ainda não houve teste em máquina Windows limpa; não confundir teste neste computador com certificação de compatibilidade em outros ambientes.

## Arquivos e decisões

- `backend/launcher.py`: entrada do executável; escolhe servidor ou extrator isolado antes de carregar o backend.
- `scripts/package-backend.mjs`: chama PyInstaller para incluir Python e dependências numa pasta autocontida e prepara o Ollama com CPU, Vulkan e CUDA 12. CUDA 13 não é duplicado no pacote, evitando exceder o limite do instalador.
- `desktop/src/backend.rs`: localiza sidecar e runtime nos recursos instalados. Uma compilação de produção não recorre ao Python do projeto. Recebe porta efêmera e mantém credencial somente na sessão.
- `desktop/src/process_job.rs`: agrupa backend e descendentes num Windows Job Object com encerramento ao fechar o último handle. O backend continua tentando encerrar normalmente primeiro; o grupo é a proteção contra processos órfãos em falha abrupta.
- `desktop/tauri.conf.json`: instalador por usuário, sem necessidade de instalar Python/Node/Rust no computador de destino. Inclui o instalador offline do WebView2.
- `scripts/smoke-package.py`: teste funcional isolado de extração, indexação, geração com fonte, curso, memória desligada e fechamento do sidecar.

Sidecar é um executável auxiliar iniciado pelo aplicativo. PyInstaller empacota o interpretador Python junto das bibliotecas; não traduz todo Python para código nativo. O NSIS reúne a aplicação e esses recursos em um instalador. Modelos não são embutidos: o Ollama usa o cache do usuário em `.ollama/models`. Instale/copie modelos antes de trabalhar offline; o aplicativo não baixa modelos automaticamente.

## Reproduzir

Com Python 3.14 x64 e as ferramentas de desenvolvimento da Fase 3:

```powershell
.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
npm.cmd ci
npm.cmd run desktop:package
```

O runtime portátil do Ollama deve estar em `.tools/ollama` antes de empacotar. O build pode baixar NSIS e o redistribuível WebView2 de fontes oficiais. A execução normal usa somente endpoints locais. `npm.cmd run desktop:build` compila sem gerar instalador e exige o sidecar já preparado.

## Dados e atualização

Instalação fica separada de `%LOCALAPPDATA%/CyberAITutor`, onde ficam bancos e configurações. Atualizar os binários não precisa sobrescrever esses dados. O cache dos modelos também permanece separado. Feche o tutor e aguarde o histórico salvo antes de atualizar. Não há atualização automática nem assinatura digital configurada nesta versão.

## Limitações observadas

A primeira tentativa de NSIS falhou ao incluir os dois runtimes CUDA, com erro de mapeamento do bloco de dados. O pacote foi reduzido para CUDA 12. O sidecar gerou a resposta com a fonte esperada, mas o modelo extrapolou detalhes quando a pergunta não limitava a resposta: fontes não tornam todas as afirmações automaticamente verdadeiras. O teste passou a pedir uma frase objetiva para verificar o fato, sem tratar isso como avaliação geral de qualidade.

O requisito de validação em Windows limpo ainda está pendente. Um instalador sem assinatura pode produzir aviso de reputação; não desative proteções do Windows para executá-lo. A distribuição comercial ainda exige revisão de qualidade, licenças de todos os componentes e dos modelos, além de testes em outros ambientes.

Referências técnicas: [distribuição Windows no Tauri](https://v2.tauri.app/distribute/windows-installer/), [PyInstaller](https://www.pyinstaller.org/en/stable/), [Job Objects no Windows](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

## Resultados locais adicionais

O sidecar com CUDA 12 passou extração, indexação, resposta curta com fonte associada, curso e memória desligada. Encerramento normal verificado após aguardar os filhos terminarem. O teste `scripts/smoke-job.py` também passou: encerrar abruptamente a janela principal encerrou backend e Ollama iniciados por ela. Não foram encerrados processos de outros aplicativos. Interface de cursos inspecionada na janela nativa, histórico anterior preservado.

## Instalar e usar em outro computador

Execute o instalador `Cyber AI Tutor_0.12.0_x64-setup.exe`. O pacote é destinado a Windows x64 e contém o runtime CUDA 12; aceleração NVIDIA requer driver compatível. Modelos são separados: antes de ficar offline, com o aplicativo aberto para iniciar o servidor local, use o `ollama.exe` da pasta instalada para baixar o modelo de conversa e `embeddinggemma:300m`. O Qwen3 8B ocupa aproximadamente 5,2 GB de disco; reserve também memória e espaço para o modelo de busca e materiais. No computador de desenvolvimento esses dois modelos já estão instalados. Em Configurações, selecione Qwen3 8B e rode o teste de conexão.

O executável principal depende das pastas de recursos que o instalador fornece. Não mover apenas o EXE. Para backup completo manual, feche o aplicativo e copie toda a pasta de dados CyberAITutor; o botão Criar backup cobre somente conversas. Não existe atualização automática nem migração entre versões futuras garantida.

## Resultado do instalador em 1º de outubro de 2026

Build NSIS concluído com sucesso. Tamanho: 1.158,9 MiB (aproximadamente 1,21 GB). Instalação e reinstalação silenciosas executadas neste Windows com retorno de sucesso. `scripts/smoke-install.py` comparou SHA-256 dos bancos e configurações antes/depois: todos preservados. Sidecar e runtime presentes na pasta instalada, sem duplicação de CUDA 13. Manifesto e hash do instalador em `release-0.12.0.json`.

Total automatizado: 32 testes Python e 33 testes da interface aprovados. Compilação de produção e verificação de formatação passaram. Avisos remanescentes: pacote JavaScript acima de 500 kB e aviso de depreciação httpx/TestClient nos testes. Validação em Windows limpo, assinatura digital e avaliação ampla da qualidade do modelo permanecem pendentes.
