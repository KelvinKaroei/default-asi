"""Extrator isolado: stdin recebe bytes; stdout retorna apenas JSON de texto."""
import io
import json
import sys

MAX_TEXT = 1_000_000
EXTENSIONS = {'.txt', '.md', '.markdown', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.log', '.csv', '.sql', '.sh', '.ps1', '.c', '.h', '.cpp', '.rs', '.go', '.java', '.css', '.html', '.xml'}


def extract(raw, extension, encoding='utf-8'):
    if extension == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError('PDF protegido por senha. Importe uma cópia sem senha.')
        if len(reader.pages) > 200:
            raise ValueError('Limite de 200 páginas por PDF. Divida o documento.')
        pages, total = [], 0
        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ''
            total += len(text)
            if total > MAX_TEXT:
                raise ValueError('Texto extraído excedeu 1 milhão de caracteres. Divida o material.')
            pages.append({'page': index + 1, 'text': text})
        if not any(page['text'].strip() for page in pages):
            raise ValueError('PDF sem texto extraível. Pode ser digitalizado; OCR não está disponível nesta fase.')
        empty = sum(not page['text'].strip() for page in pages)
        return pages, f'{empty} página(s) sem texto extraível.' if empty else ''
    if extension not in EXTENSIONS:
        raise ValueError('Formato não suportado. Use PDF textual, TXT, Markdown ou código.')
    try:
        if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
            text = raw.decode('utf-16')
        else:
            text = raw.decode('utf-8-sig' if encoding == 'utf-8' else encoding)
    except UnicodeError:
        raise ValueError('Codificação incompatível. Se o arquivo for antigo, selecione Windows-1252 ou salve como UTF-8.')
    if any(ord(c) < 32 and c not in '\n\r\t\f' for c in text):
        raise ValueError('Arquivo contém dados binários ou caracteres de controle não suportados.')
    if not text.strip():
        raise ValueError('Arquivo vazio ou sem texto útil.')
    if len(text) > MAX_TEXT:
        raise ValueError('Texto excedeu 1 milhão de caracteres. Divida o material.')
    return [{'page': 1, 'text': text}], ''


def main():
    try:
        pages, warning = extract(sys.stdin.buffer.read(5 * 1024 * 1024 + 1), sys.argv[1], sys.argv[2])
        result = {'pages': pages, 'warning': warning}
    except ValueError as error:
        result = {'error': str(error)}
    except Exception:
        result = {'error': 'Não foi possível ler este PDF. O arquivo pode estar danificado ou usar recursos incompatíveis.'}
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))


if __name__ == '__main__':
    main()
