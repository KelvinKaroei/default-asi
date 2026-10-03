import json
import sqlite3
from uuid import uuid4

import pytest
from fastapi import HTTPException
from app.history import History, HistoryStore


def payload(revision=0):
    return History(revision=revision, mutation=uuid4(), chats=[{
        'id': str(uuid4()), 'title': 'Permissões Linux', 'category': 'Linux', 'mode': 'TUTOR',
        'draft': 'próxima pergunta', 'messages': [
            {'id': str(uuid4()), 'role': 'user', 'content': 'chmod?', 'mode': 'TUTOR'},
            {'id': str(uuid4()), 'role': 'assistant', 'content': 'Texto parcial çã', 'mode': 'TUTOR', 'status': 'generating'}]}])


def test_restart_recovers_partial_draft_category_and_order(tmp_path):
    store = HistoryStore(tmp_path)
    original = payload()
    assert store.save(original)['revision'] == 1
    recovered = HistoryStore(tmp_path).read()
    chat = recovered['chats'][0]
    assert chat['draft'] == 'próxima pergunta' and chat['category'] == 'Linux'
    assert [m['content'] for m in chat['messages']] == ['chmod?', 'Texto parcial çã']
    assert chat['messages'][1]['status'] == 'cancelled'
    assert recovered['revision'] == 2


def test_repeated_save_is_idempotent_and_stale_writer_rejected(tmp_path):
    store = HistoryStore(tmp_path)
    value = payload()
    assert store.save(value) == store.save(value) == {'revision': 1}
    assert len(store.read()['chats'][0]['messages']) == 2
    with pytest.raises(HTTPException) as error:
        store.save(payload())
    assert error.value.status_code == 409
    assert store.read()['chats'][0]['id'] == str(value.chats[0].id)


def test_transaction_rolls_back_and_backup_restores(tmp_path):
    store = HistoryStore(tmp_path)
    value = payload()
    store.save(value)
    store.backup()
    with sqlite3.connect(store.path) as db:
        db.execute("CREATE TRIGGER reject_insert BEFORE INSERT ON chats BEGIN SELECT RAISE(ABORT,'test failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        store.save(payload(1))
    assert store.read()['chats'][0]['id'] == str(value.chats[0].id)
    with sqlite3.connect(store.path) as db:
        db.execute('DROP TRIGGER reject_insert')
    store.save(payload(1))
    restored = store.restore(2)
    assert restored['chats'][0]['id'] == str(value.chats[0].id)
    assert restored['chats'][0]['messages'][1]['status'] == 'cancelled'
    assert (tmp_path / 'history.before-restore.sqlite3').exists()


def test_corruption_is_not_replaced(tmp_path):
    path = tmp_path / 'history.sqlite3'
    path.write_bytes(b'not a sqlite database')
    with pytest.raises(sqlite3.DatabaseError):
        HistoryStore(tmp_path).read()
    assert path.read_bytes() == b'not a sqlite database'


def test_history_routes_require_auth_and_survive_backend_recreation(tmp_path):
    from fastapi.testclient import TestClient
    from app.server import create_app
    from test_server import FakeOllama, TOKEN
    value = payload()
    for step in range(2):
        with TestClient(create_app(TOKEN, tmp_path, FakeOllama()), base_url='http://127.0.0.1', headers={'Authorization': f'Bearer {TOKEN}'}) as client:
            assert client.get('/api/v1/history', headers={'Authorization': ''}).status_code == 401
            if step == 0:
                assert client.put('/api/v1/history', json=value.model_dump(mode='json')).status_code == 200
                assert client.post('/api/v1/history/backup').status_code == 200
            else:
                result = client.get('/api/v1/history').json()
                assert result['chats'][0]['title'] == 'Permissões Linux'
                assert result['chats'][0]['messages'][1]['status'] == 'cancelled'
                assert client.post('/api/v1/history/restore', json={'revision': result['revision']}).status_code == 200
