from fastapi.testclient import TestClient
from app.server import create_app
from app.memory import MemoryStore
from test_server import FakeOllama,TOKEN
from test_chat import ChatOllama
import json

def client(folder,runtime=None):
 return TestClient(create_app(TOKEN,folder,runtime or FakeOllama()),base_url='http://127.0.0.1',headers={'Authorization':f'Bearer {TOKEN}'})

def test_course_quiz_and_labs_survive_restart(tmp_path):
 with client(tmp_path) as api:
  course=api.get('/api/v1/learning/course').json()
  assert 'answer' not in course['modules'][0]['lessons'][0]['quiz']
  assert api.put('/api/v1/learning/lessons/ip',json={'complete':True}).status_code==200
  assert not api.post('/api/v1/learning/lessons/ip/quiz',json={'choice':0}).json()['correct']
  assert api.post('/api/v1/learning/lessons/ip/quiz',json={'choice':1}).json()['correct']
  assert api.post('/api/v1/learning/lessons/ip/quiz',json={'choice':9}).status_code==400
  assert api.put('/api/v1/learning/lessons/missing',json={'complete':True}).status_code==404
  assert api.put('/api/v1/learning/labs/loopback/steps/0',json={'complete':True}).status_code==200
  assert api.put('/api/v1/learning/labs/loopback/steps/99',json={'complete':True}).status_code==404
 with client(tmp_path) as api:
  progress=api.get('/api/v1/learning/course').json()['modules'][0]['lessons'][0]['progress']
  assert progress=={'complete':True,'attempts':2,'passed':True}
  assert api.get('/api/v1/learning/labs').json()[0]['completed']==[0]
  assert api.post('/api/v1/learning/labs/loopback/execute').status_code in (404,405)

def test_memory_optin_edit_clear_and_user_isolation(tmp_path):
 one=tmp_path/'one';two=tmp_path/'two'
 with client(one) as api:
  assert api.get('/api/v1/memory').json()=={'enabled':False,'items':[]}
  assert api.post('/api/v1/memory',json={'text':'Redes'}).status_code==409
  api.put('/api/v1/memory/enabled',json={'enabled':True})
  state=api.post('/api/v1/memory',json={'text':'Prefiro exemplos curtos.'}).json()
  identifier=state['items'][0]['id']
  api.put('/api/v1/memory/'+identifier,json={'text':'Estou estudando DNS.'})
  assert MemoryStore(one).context()==['Estou estudando DNS.']
  api.put('/api/v1/memory/enabled',json={'enabled':False})
  assert MemoryStore(one).context()==[]
  assert api.put('/api/v1/memory/'+identifier,json={'text':'Alteração'}).status_code==409
 with client(two) as api:
  assert api.get('/api/v1/memory').json()['items']==[]
 with client(one) as api:
  assert len(api.get('/api/v1/memory').json()['items'])==1
  assert api.delete('/api/v1/memory').json()['items']==[]

def test_only_enabled_memory_reaches_model(tmp_path):
 runtime=ChatOllama()
 with client(tmp_path,runtime) as api:
  api.put('/api/v1/settings',json={'model':'qwen3:8b'})
  api.put('/api/v1/memory/enabled',json={'enabled':True})
  api.post('/api/v1/memory',json={'text':'Prefiro exemplos com diagramas.'})
  body={'mode':'TUTOR','messages':[{'role':'user','content':'Explique DNS'}]}
  result=api.post('/api/v1/chat',json=body)
  assert json.loads(result.text.splitlines()[0])['memory_used']
  assert 'diagramas' in runtime.payload['messages'][-1]['content']
  api.put('/api/v1/memory/enabled',json={'enabled':False})
  api.post('/api/v1/chat',json=body)
  assert 'diagramas' not in str(runtime.payload)
