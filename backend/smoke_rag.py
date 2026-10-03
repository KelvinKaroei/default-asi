import asyncio, base64, json, tempfile
from pathlib import Path
import httpx
from fastapi.testclient import TestClient
from app.server import create_app
from app.retrieval import Retrieval
class ExistingLocal:
    error=''
    async def start(self): pass
    async def close(self): pass
    async def call(self,method,path,**kwargs):
        async with httpx.AsyncClient(base_url='http://127.0.0.1:11434',trust_env=False,timeout=180) as client:
            response=await client.request(method,path,**kwargs);response.raise_for_status();return response.json()
    async def chat_stream(self,payload):
        async with httpx.AsyncClient(base_url='http://127.0.0.1:11434',trust_env=False,timeout=180) as client:
            async with client.stream('POST','/api/chat',json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line: yield json.loads(line)
with tempfile.TemporaryDirectory() as temporary:
    folder=Path(temporary);runtime=ExistingLocal();token='test-local-rag-only'
    with TestClient(create_app(token,folder,runtime),base_url='http://127.0.0.1',headers={'Authorization':'Bearer '+token}) as client:
        client.put('/api/v1/settings',json={'model':'qwen3:8b'})
        value=client.post('/api/v1/materials',json={'name':'Manual Orion.txt','content':base64.b64encode('No laboratório fictício Orion, o código de identificação do roteador é AZUL-7429. O laboratório usa somente máquinas virtuais locais.'.encode()).decode()})
        assert value.status_code==200,value.text
        retrieval=Retrieval(folder,runtime,asyncio.Lock());asyncio.run(retrieval.build());assert retrieval.status()['ready'],retrieval.status()
        found=asyncio.run(retrieval.search('Qual é o código do roteador do laboratório Orion?'))
        print('RECUPERACAO',json.dumps(found,ensure_ascii=False))
        result=client.post('/api/v1/chat',json={'mode':'EXPLAIN','messages':[{'role':'user','content':'Qual é o código do roteador do laboratório Orion? Responda brevemente.'}],'use_materials':True})
        print('CHAT',result.text)
        assert 'AZUL-7429' in result.text and 'sources' in result.text,result.text
