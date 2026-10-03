# Fase 7 — Acervo local

Importação de PDF textual, TXT, Markdown, código e anotações. O original e o texto extraído ficam em `materials.sqlite3`, dentro de `%LOCALAPPDATA%/CyberAITutor`. Nenhum arquivo importado é executado. PDF digitalizado exige OCR externo; o protótipo informa quando não encontra texto.

## Arquivos e fluxo

- `frontend/src/features/Knowledge.tsx`: lê o arquivo selecionado com FileReader, codifica em base64, envia à API local, lista, filtra pelo nome, visualiza páginas e confirma remoção. Anotações viram Markdown UTF-8.
- `backend/app/materials.py`: valida extensão/nome/tamanho, identifica duplicatas por SHA-256, controla extração em subprocesso e grava original e páginas em transação SQLite. `extract_bounded` limita tempo e memória; `materials_router` reúne rotas protegidas pela sessão.
- `backend/app/extract_material.py`: interpreta texto e PDF com pypdf. O subprocesso separa falhas do leitor de PDF da API; não é um sandbox de segurança completo.

Interface → POST local → validação → extrator separado → SQLite → lista e prévia. pypdf dispensa aplicativo externo para PDFs textuais; SQLite mantém extração e original juntos e permite exclusão transacional.

## Limites e testes

Até 5 MiB por arquivo, 200 páginas por PDF, 1 milhão de caracteres extraídos, 200 documentos/100 MiB de originais. A extração tem limite de 15 segundos e 512 MiB. UTF-8 padrão; UTF-16 com BOM detectado; Windows-1252 por seleção explícita. Prévia pagina textos longos em trechos de 30 mil caracteres.

Testes automatizados cobrem texto, encoding, duplicata, exclusão, HTML literal, PDF criptografado/sem texto/excessivo, limites de requisição, tempo e memória do trabalhador. Para testar manualmente, importe um TXT curto, confira a prévia e importe de novo: deve informar duplicata. Remover apaga só a cópia do acervo, não o arquivo de origem.

Falha de encoding: selecione Windows-1252 ou converta para UTF-8. PDF sem texto: forneça uma versão textual. Limite excedido: divida o material. Erros do banco ficam visíveis, sem apagar o banco para tentar corrigir. O backup de conversas não inclui materiais.
