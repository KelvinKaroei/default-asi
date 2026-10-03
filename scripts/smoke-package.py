"""Validação do sidecar distribuível, sem utilizar o histórico do usuário."""
import base64,json,os,subprocess,tempfile,time,secrets
from pathlib import Path
import httpx,psutil
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='cyber-package-') as folder:
 env={**os.environ,'LOCALAPPDATA':folder,'CYBER_OLLAMA_PATH':str(root/'build/ollama-package/ollama.exe')}
 binary=root/'build/sidecar/cyber-backend/cyber-backend.exe'
 with open(root/'build/sidecar-smoke.log','w',encoding='utf-8') as log:
  process=subprocess.Popen([str(binary)],cwd=folder,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  token=secrets.token_hex(32);process.stdin.write((json.dumps({'token':token})+'\n').encode());process.stdin.flush()
  children=[]
  try:
   line=process.stdout.readline();assert line, 'Backend não forneceu porta; confira log local.'
   port=json.loads(line)['port']
   with httpx.Client(base_url=f'http://127.0.0.1:{port}/api/v1',headers={'Authorization':f'Bearer {token}'},trust_env=False,timeout=180) as api:
    assert api.get('/health').json()['ollama']=='ready'
    assert api.get('/history').status_code==200
    assert api.put('/settings',json={'model':'qwen3:8b'}).status_code==200
    material=api.post('/materials',json={'name':'smoke.txt','content':base64.b64encode(b'Laboratorio Orion codigo AZUL-7429.').decode()});assert material.status_code==200,material.text
    assert api.post('/retrieval/index').status_code==200
    for _ in range(120):
     status=api.get('/retrieval').json()
     if not status['running']:break
     time.sleep(.5)
    assert status['ready'],status
    response=api.post('/chat',json={'mode':'EXPLAIN','messages':[{'role':'user','content':'Qual codigo do laboratorio Orion? Responda somente em uma frase.'}],'use_materials':True})
    events=[json.loads(line) for line in response.text.splitlines()]
    answer=''.join(e.get('content','') for e in events)
    assert 'AZUL-7429' in answer,(events,answer)
    assert events[0]['sources'] and events[-1]['type']=='done'
    assert api.put('/learning/lessons/ip',json={'complete':True}).status_code==200
    assert api.get('/memory').json()['enabled'] is False
    children=psutil.Process(process.pid).children(recursive=True)
    print(json.dumps({'backend':'ok','extraction':'ok','rag':'ok','sources':len(events[0]['sources']),'course':'ok','memory_default':'off','answer':answer},ensure_ascii=False))
  finally:
   process.stdin.close()
   try:process.wait(timeout=15)
   except subprocess.TimeoutExpired:process.kill();process.wait();raise
  _, remaining=psutil.wait_procs(children,timeout=5)
  survivors=[p.pid for p in remaining if p.is_running()]
  assert not survivors, survivors
  print('Encerramento normal: nenhum processo filho restante.')
