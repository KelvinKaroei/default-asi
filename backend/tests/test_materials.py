import base64
import io
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from app.server import create_app
from app.extract_material import extract
from app.materials import extract_bounded
from test_server import FakeOllama, TOKEN


def pdf_bytes(text=None, encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 20 200 Td ({text}) Tj ET'.encode('ascii'))
        page[NameObject('/Contents')] = writer._add_object(stream)
    if encrypted:
        writer.encrypt('password')
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_text_encodings_and_binary_rejection():
    assert extract('ação'.encode(), '.md')[0][0]['text'] == 'ação'
    assert extract('ação'.encode('utf-16'), '.txt')[0][0]['text'] == 'ação'
    assert extract('ação'.encode('cp1252'), '.txt', 'cp1252')[0][0]['text'] == 'ação'
    for raw, ext in [(b'\x00\x01', '.py'), (b'', '.txt'), (b'hello', '.exe'), ('ação'.encode('cp1252'), '.txt')]:
        with pytest.raises(ValueError):
            extract(raw, ext)


def test_pdf_text_empty_encrypted_and_page_limit():
    assert 'Linux permissions' in extract(pdf_bytes('Linux permissions'), '.pdf')[0][0]['text']
    with pytest.raises(ValueError, match='sem texto'):
        extract(pdf_bytes(), '.pdf')
    with pytest.raises(ValueError, match='senha'):
        extract(pdf_bytes('secret', True), '.pdf')
    writer = PdfWriter()
    for _ in range(201): writer.add_blank_page(width=10, height=10)
    output = io.BytesIO(); writer.write(output)
    with pytest.raises(ValueError, match='200 páginas'):
        extract(output.getvalue(), '.pdf')


def test_isolated_worker_pdf_and_invalid_file():
    assert extract_bounded(pdf_bytes('local document'), '.pdf', 'utf-8')['pages'][0]['page'] == 1
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        extract_bounded(b'not a PDF', '.pdf', 'utf-8')
    assert error.value.status_code == 400


def test_material_routes_persist_deduplicate_and_remove(tmp_path):
    material_id = None
    for step in range(2):
        with TestClient(create_app(TOKEN, tmp_path, FakeOllama()), base_url='http://127.0.0.1', headers={'Authorization': f'Bearer {TOKEN}'}) as client:
            if step == 0:
                assert client.post('/api/v1/materials', headers={'Authorization': ''}, json={}).status_code == 401
                body = {'name': 'notes.md', 'content': base64.b64encode('Texto <script>literal</script> çã'.encode()).decode()}
                response = client.post('/api/v1/materials', json=body)
                assert response.status_code == 200, response.text
                material_id = response.json()['material']['id']
                body['name'] = 'outro.md'
                duplicate = client.post('/api/v1/materials', json=body).json()
                assert duplicate['duplicate'] and duplicate['material']['id'] == material_id
                assert client.post('/api/v1/materials', json={**body, 'name': '../escape.md'}).status_code == 400
                assert client.post('/api/v1/materials', json={**body, 'content': '!bad!'}).status_code == 400
                assert client.get('/api/v1/history').json()['chats'] == []
            else:
                assert len(client.get('/api/v1/materials').json()) == 1
                value = client.get('/api/v1/materials/' + material_id).json()
                assert value['pages'][0]['text'].endswith('çã')
                assert client.delete('/api/v1/materials/' + material_id).status_code == 200
                assert client.get('/api/v1/materials').json() == []
                assert client.get('/api/v1/materials/' + material_id).status_code == 404


def test_limits_and_failed_import_leave_no_record(tmp_path):
    with TestClient(create_app(TOKEN, tmp_path, FakeOllama()), base_url='http://127.0.0.1', headers={'Authorization': f'Bearer {TOKEN}'}) as client:
        for name, content in [('empty.txt', b''), ('scan.pdf', pdf_bytes()), ('bad.pdf', b'bad'), ('large.txt', b'x' * (5 * 1024 * 1024 + 1))]:
            response = client.post('/api/v1/materials', json={'name': name, 'content': base64.b64encode(content).decode()})
            assert response.status_code in (400, 422), response.text
        assert client.get('/api/v1/materials').json() == []
        assert client.post('/api/v1/materials', content=b'x' * (8 * 1024 * 1024 + 1)).status_code == 413

@pytest.mark.parametrize('limit', ['time', 'memory'])
def test_worker_limits_terminate_owned_process(monkeypatch, limit):
    import app.materials as module
    import sys
    from fastapi import HTTPException
    original = module.subprocess.Popen
    children = []
    def sleeping_worker(args, **kwargs):
        process = original([sys.executable, '-c', 'import time; time.sleep(30)'], **kwargs)
        children.append(process)
        return process
    monkeypatch.setattr(module.subprocess, 'Popen', sleeping_worker)
    if limit == 'time': monkeypatch.setattr(module, 'EXTRACT_TIMEOUT', .2)
    else: monkeypatch.setattr(module, 'MEMORY_BUDGET', 1)
    with pytest.raises(HTTPException) as error:
        module.extract_bounded(b'test', '.txt', 'utf-8')
    assert error.value.status_code == 400
    assert children[0].poll() is not None
