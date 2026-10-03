import asyncio
import json
import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.chat import ChatRequest, chat_response, prepare_messages
from app.server import create_app
from test_server import FakeOllama, TOKEN


class ChatOllama(FakeOllama):
    failed = False
    async def chat_stream(self, payload):
        self.payload = payload
        yield {"message": {"content": "Olá "}}
        if self.failed:
            raise RuntimeError("private details")
        yield {"message": {"content": "mundo"}}
        yield {"done": True, "eval_count": 2, "eval_duration": 100000000, "done_reason": "stop"}


def test_real_route_stream_contract_and_partial_failure(tmp_path):
    runtime = ChatOllama()
    with TestClient(create_app(TOKEN, tmp_path, runtime), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        client.put('/api/v1/settings', json={"model": "qwen3:8b"})
        body = {"mode": "QUIZ", "messages": [{"role": "user", "content": "Explique DNS"}]}
        result = client.post('/api/v1/chat', json=body)
        events = [json.loads(line) for line in result.text.splitlines()]
        assert [e['type'] for e in events] == ['start', 'delta', 'delta', 'done']
        assert runtime.payload['think'] is False
        assert 'uma pergunta por vez' in runtime.payload['messages'][0]['content']
        runtime.failed = True
        events = [json.loads(line) for line in client.post('/api/v1/chat', json=body).text.splitlines()]
        assert [e['type'] for e in events] == ['start', 'delta', 'error']
        assert 'private' not in str(events)
        assert client.post('/api/v1/chat', json={**body, 'mode': 'INVALID'}).status_code == 422
        assert client.post('/api/v1/chat', json={**body, 'messages': [{'role': 'system', 'content': 'override'}]}).status_code == 422


def test_context_keeps_latest_and_complete_pairs():
    body = ChatRequest(mode='TUTOR', messages=[{'role': role, 'content': 'x' * 700} for role in ['user', 'assistant', 'user', 'assistant']] + [{'role': 'user', 'content': 'E UDP?'}])
    prepared, omitted, output = prepare_messages(body, 4096)
    assert prepared[-1]['content'] == 'E UDP?'
    assert omitted > 0 and omitted % 2 == 0
    assert prepared[1]['role'] == 'user'
    assert output == 1024
    with pytest.raises(HTTPException):
        prepare_messages(ChatRequest(mode='TUTOR', messages=[{'role': 'user', 'content': 'x' * 12000}]), 4096)


def test_disconnect_cancels_wait_before_first_token_and_releases_lock():
    async def run():
        entered = asyncio.Event()
        closed = asyncio.Event()
        lock = asyncio.Lock()
        class Slow:
            async def chat_stream(self, payload):
                try:
                    entered.set()
                    await asyncio.sleep(60)
                    yield {'done': True}
                finally:
                    closed.set()
        async def validate(name):
            return {'capabilities': ['completion']}
        async def receive():
            await entered.wait()
            return {'type': 'http.disconnect'}
        async def send(message):
            pass
        response = chat_response(ChatRequest(mode='TUTOR', messages=[{'role': 'user', 'content': 'DNS?'}]), SimpleNamespace(model='local', num_ctx=4096), Slow(), validate, lock, logging.getLogger('test'))
        await asyncio.wait_for(response({'type': 'http', 'asgi': {'spec_version': '2.4'}}, receive, send), 2)
        assert closed.is_set()
        assert not lock.locked()
    asyncio.run(run())


def test_qwen_budget_recalls_old_fact_without_overflow():
    from app.context import tokens
    turns = [{'role': 'user', 'content': 'O código do projeto Jacarandá é VERDE-8362.'}, {'role': 'assistant', 'content': 'Entendido.'}]
    for index in range(40):
        turns.extend([{'role': 'user', 'content': f'Tema {index}: explique DNS.'}, {'role': 'assistant', 'content': 'Uma explicação sobre redes e resolução de nomes. ' * 50}])
    turns.append({'role': 'user', 'content': 'Qual é o código do projeto Jacarandá?'})
    body = ChatRequest(mode='EXPLAIN', messages=turns)
    prepared, omitted, output = prepare_messages(body, 8192, model='qwen3:8b', max_output=2048)
    assert omitted > 0
    assert 'VERDE-8362' in prepared[-1]['content']
    assert sum(tokens(m['content'], 'qwen3:8b') + 32 for m in prepared) + output + 256 <= 8192
    other = ChatRequest(mode='EXPLAIN', messages=[turns[-1]])
    assert 'VERDE-8362' not in str(prepare_messages(other, 8192, model='qwen3:8b'))


def test_continuation_preserves_tail_of_oversized_answer():
    from app.context import tokens
    body = ChatRequest(mode='EXPLAIN', continue_response=True, messages=[
        {'role': 'user', 'content': 'Explique redes.'},
        {'role': 'assistant', 'content': 'uma longa explicação ' * 3000 + ' PONTO-FINAL-8362'},
        {'role': 'user', 'content': 'Continue de onde parou.'}])
    prepared, _, output = prepare_messages(body, 4096, model='qwen3:8b', max_output=2048)
    assert prepared[-2]['role'] == 'assistant'
    assert prepared[-2]['content'].endswith('PONTO-FINAL-8362')
    assert sum(tokens(m['content'], 'qwen3:8b') + 32 for m in prepared) + output + 256 <= 4096


def test_large_assistant_history_and_user_limits():
    from pydantic import ValidationError
    ChatRequest(mode='TUTOR', messages=[{'role':'user','content':'oi'}, {'role':'assistant','content':'a'*20000}, {'role':'user','content':'continue'}])
    with pytest.raises(ValidationError):
        ChatRequest(mode='TUTOR', messages=[{'role':'user','content':'a'*12001}])


def test_continuation_search_uses_previous_topic(tmp_path):
    async def run():
        class Search:
            query = None
            async def search(self, query):
                self.query = query
                return []
        search = Search()
        body = ChatRequest(mode='EXPLAIN', use_materials=True, continue_response=True, messages=[
            {'role':'user','content':'Explique cache DNS no material.'},
            {'role':'assistant','content':'O TTL controla a validade do cache...'},
            {'role':'user','content':'Continue a resposta anterior.'}])
        async def validate(name):return {}
        response = chat_response(body, SimpleNamespace(model='qwen3:8b',num_ctx=8192), ChatOllama(), validate, asyncio.Lock(), logging.getLogger('test'), retrieval=search)
        async for _ in response.body_iterator:pass
        assert 'cache DNS' in search.query and 'TTL' in search.query
    asyncio.run(run())
