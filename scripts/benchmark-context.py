import asyncio,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.runtime import Ollama
async def main():
 runtime=Ollama()
 try:
  await runtime.start()
  assert not runtime.error,runtime.error
  results=[]
  for context in (8192,16384,32768):
   start=time.monotonic()
   result=await runtime.call('POST','/api/chat',json={'model':'qwen3:8b','messages':[{'role':'user','content':'Explique em um parágrafo como funciona o DNS.'}],'stream':False,'think':False,'keep_alive':'2m','options':{'num_ctx':context,'num_predict':128}},timeout=240)
   loaded=await runtime.call('GET','/api/ps')
   row={'context':context,'seconds':round(time.monotonic()-start,2),'tokens':result.get('eval_count'),'tokens_per_second':round(result.get('eval_count',0)/(result.get('eval_duration',1)/1e9),1),'vram_gib':round(sum(m.get('size_vram',0) for m in loaded['models'])/2**30,2),'loaded':loaded['models'][0].get('context_length')}
   results.append(row);print(json.dumps(row),flush=True)
  Path('build/context-benchmark.json').write_text(json.dumps(results,indent=2))
 finally:await runtime.close()
asyncio.run(main())
