"""Instala/atualiza silenciosamente o pacote local e verifica preservação dos bancos."""
from pathlib import Path
import hashlib,os,subprocess,json
root=Path(__file__).resolve().parents[1]
config=json.loads((root/'desktop/tauri.conf.json').read_text(encoding='utf-8'))
setup=root/'desktop/target/release/bundle/nsis'/f"{config['productName']}_{config['version']}_x64-setup.exe"
installed=Path(os.environ['LOCALAPPDATA'])/config['productName']
data=Path(os.environ['LOCALAPPDATA'])/'CyberAITutor'
def snapshot():
 return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data.glob('*') if p.is_file() and (p.suffix=='.sqlite3' or p.name=='settings.json')}
before=snapshot()
for attempt in range(2):
 result=subprocess.run([str(setup),'/S',*(['/UPDATE'] if attempt else [])],timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
 assert result.returncode==0,('installer',result.returncode)
 assert (installed/'cyber-ai-tutor.exe').exists(),'Executável instalado ausente'
 assert (installed/'backend/cyber-backend.exe').exists(),'Sidecar ausente'
 assert (installed/'ollama/ollama.exe').exists(),'Runtime ausente'
 assert not (installed/'ollama/lib/ollama/cuda_v13').exists(),'Runtime duplicado'
 assert snapshot()==before,'A instalação alterou dados pessoais'
 for relative, source in [('cyber-ai-tutor.exe',root/'desktop/target/release/cyber-ai-tutor.exe'),('backend/cyber-backend.exe',root/'build/sidecar/cyber-backend/cyber-backend.exe'),('backend/_internal/assets/qwen3-tokenizer.json',root/'backend/assets/qwen3-tokenizer.json')]:
  expected=source.read_bytes()
  if relative=='cyber-ai-tutor.exe':
   # Tauri patches this marker for NSIS, then restores the build artifact.
   marker=b'__TAURI_BUNDLE_TYPE_VAR_UNK'
   assert expected.count(marker)==1,'Marcador Tauri inesperado'
   expected=expected.replace(marker,b'__TAURI_BUNDLE_TYPE_VAR_NSS',1)
  assert hashlib.sha256((installed/relative).read_bytes()).digest()==hashlib.sha256(expected).digest(),relative
 print('Instalação' if attempt==0 else 'Atualização', 'verificada; bancos e configurações preservados.')
print('Pacote instalado com sidecar e runtime locais.')
