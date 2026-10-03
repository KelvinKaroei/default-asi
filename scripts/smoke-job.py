"""Teste de desligamento abrupto do aplicativo e da árvore de processos própria."""
import os,subprocess,time,tempfile
from pathlib import Path
import psutil
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='cyber-job-',ignore_cleanup_errors=True) as folder:
 app=subprocess.Popen([str(root/'desktop/target/release/cyber-ai-tutor.exe')],env={**os.environ,'LOCALAPPDATA':folder},cwd=folder)
 parent=psutil.Process(app.pid)
 descendants=[]
 try:
  for _ in range(80):
   if app.poll() is not None:raise RuntimeError('Aplicativo encerrou antes do teste')
   descendants=parent.children(recursive=True)
   if any(p.name().lower()=='ollama.exe' for p in descendants):break
   time.sleep(.5)
  assert any(p.name().lower()=='cyber-backend.exe' for p in descendants), 'Sidecar não iniciou'
  assert any(p.name().lower()=='ollama.exe' for p in descendants), 'Ollama não iniciou'
  time.sleep(2)
  descendants=parent.children(recursive=True)
  owned=[p for p in descendants if p.name().lower() in ('cyber-backend.exe','ollama.exe','llama-server.exe')]
  app.kill();app.wait(timeout=10)
  _,alive=psutil.wait_procs(owned,timeout=10)
  assert not alive,[(p.pid,p.name()) for p in alive]
  print('Encerramento abrupto verificado: backend e Ollama encerrados pelo grupo do Windows.')
 finally:
  if app.poll() is None:app.kill();app.wait(timeout=10)
