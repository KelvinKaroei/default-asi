"""Real model checks with synthetic history; never reads user conversations."""
import asyncio,json,logging,sys,time
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.runtime import Ollama
from app.chat import ChatRequest,chat_response
async def main():
 runtime=Ollama();results=[]
 try:
  await runtime.start();assert not runtime.error,runtime.error
  async def validate(model):return await runtime.call('POST','/api/show',json={'model':model})
  async def run(messages,continuation=False):
   body=ChatRequest(mode='EXPLAIN',messages=messages,continue_response=continuation)
   response=chat_response(body,SimpleNamespace(model='qwen3:8b',num_ctx=32768,max_output=8192),runtime,validate,asyncio.Lock(),logging.getLogger('smoke'))
   events=[];start=time.monotonic()
   async for line in response.body_iterator:events.append(json.loads(line))
   assert events[-1]['type']=='done',events[-1]
   answer=''.join(e.get('content','') for e in events)
   return answer,{'seconds':round(time.monotonic()-start,1),'characters':len(answer),'reason':events[-1]['reason'],'tps':events[-1].get('tokens_per_second'),'omitted':events[0].get('omitted_messages')}
  turns=[{'role':'user','content':'O código do projeto Jacarandá é VERDE-8362.'},{'role':'assistant','content':'Registrado nesta conversa.'}]
  for i in range(160):turns.extend([{'role':'user','content':f'Explique o tópico {i} sobre redes.'},{'role':'assistant','content':'Redes conectam computadores. DNS traduz nomes para endereços. ' * 30}])
  turns.append({'role':'user','content':'Qual é o código do projeto Jacarandá mencionado anteriormente? Responda só o código.'})
  answer,row=await run(turns);assert 'VERDE-8362' in answer,answer;row['check']='old_fact';results.append(row);print(json.dumps(row),flush=True)
  answer,row=await run([{'role':'user','content':'Escreva um guia de estudo detalhado sobre DNS para iniciantes, com exatamente 16 seções numeradas, cada uma com pelo menos 80 palavras. Explique conceitos, exemplos cotidianos, cache, registros, TTL, recursão, privacidade, resolução de problemas e exercícios. Termine a última seção com FIM-DO-GUIA.'}])
  assert len(answer)>7000 and 'FIM-DO-GUIA' in answer and row['reason']=='stop',(row,answer[-300:]);row['check']='long_complete_answer';results.append(row);print(json.dumps(row),flush=True)
  Path('build/conversation-smoke.json').write_text(json.dumps(results,indent=2))
 finally:await runtime.close()
asyncio.run(main())
