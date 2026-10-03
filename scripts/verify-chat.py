"""Verificação real do streaming e cancelamento; feche o tutor antes de executar."""
import json
from pathlib import Path
import secrets
import subprocess
import time

import httpx
import psutil

root = Path(__file__).resolve().parents[1]
token = secrets.token_hex(32)
process = subprocess.Popen([str(root / '.venv/Scripts/python.exe'), '-m', 'app'],
    cwd=root / 'backend', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
owned = []
try:
    process.stdin.write(json.dumps({'token': token}) + '\n')
    process.stdin.flush()
    port = json.loads(process.stdout.readline())['port']
    with httpx.Client(base_url=f'http://127.0.0.1:{port}/api/v1', headers={'Authorization': f'Bearer {token}'}, trust_env=False, timeout=180) as client:
        assert client.get('/health').json()['ollama'] == 'ready'
        client.put('/settings', json={'model': 'qwen3:8b', 'num_ctx': 4096}).raise_for_status()
        start = time.monotonic()
        events = []
        with client.stream('POST', '/chat', json={'mode': 'EXPLAIN', 'messages': [{'role': 'user', 'content': 'Explique em até 100 palavras a diferença entre TCP e UDP e dê um exemplo de uso de cada um.'}]}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                item = json.loads(line)
                if item['type'] == 'delta' and not any(e['type'] == 'delta' for e in events):
                    print('Primeiro fragmento em segundos:', round(time.monotonic() - start, 2), flush=True)
                events.append(item)
        assert events[-1]['type'] == 'done', events[-1]
        answer = ''.join(e['content'] for e in events if e['type'] == 'delta')
        print('Resposta:', answer, flush=True)
        print('Fragmentos:', sum(e['type'] == 'delta' for e in events), 'Conclusão:', events[-1], flush=True)
        assert 'TCP' in answer and 'UDP' in answer
        with client.stream('POST', '/chat', json={'mode': 'COURSE', 'messages': [{'role': 'user', 'content': 'Crie um curso detalhado de redes com dez módulos e exercícios.'}]}) as response:
            for line in response.iter_lines():
                if json.loads(line)['type'] == 'delta':
                    break
        cancelled = time.monotonic()
        # Uma nova geração deve ser aceita logo após fechar o stream anterior.
        for _ in range(20):
            response = client.post('/chat', json={'mode': 'QUIZ', 'messages': [{'role': 'user', 'content': 'Faça uma pergunta curta sobre DNS.'}]})
            followup = [json.loads(line) for line in response.text.splitlines()]
            if followup[0]['type'] != 'error':
                break
            time.sleep(0.1)
        assert followup[-1]['type'] == 'done', followup
        print('Nova geração após cancelamento concluída em:', round(time.monotonic() - cancelled, 2), 's', flush=True)
        owned = psutil.Process(process.pid).children(recursive=True)
        failed = []
        stopped = False
        with client.stream('POST', '/chat', json={'mode': 'COURSE', 'messages': [{'role': 'user', 'content': 'Elabore dez módulos detalhados de Linux com exercícios e explicações.'}]}) as response:
            for line in response.iter_lines():
                item = json.loads(line)
                failed.append(item)
                if item['type'] == 'delta' and not stopped:
                    # Somente os processos Ollama descendentes deste backend de teste.
                    runtime_processes = [p for p in owned if p.is_running() and p.name().lower().startswith('ollama')]
                    for runtime_process in reversed(runtime_processes):
                        try:
                            runtime_process.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    stopped = True
        assert any(item['type'] == 'delta' for item in failed)
        assert failed[-1]['type'] == 'error', failed[-1]
        print('Falha real do Ollama: fragmentos recebidos preservados e erro explícito no stream.', flush=True)
finally:
    process.stdin.close()
    process.wait(timeout=15)
    _, survivors = psutil.wait_procs(owned, timeout=10)
    print('Processos sobreviventes:', [(p.pid, p.name()) for p in survivors], flush=True)
    assert not survivors
    print('Backend e processos próprios encerrados.', flush=True)
