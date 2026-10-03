"""Pré-download explícito do Qwen3 8B do registro oficial, sem executar o runtime."""
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request
from download_parts import download_parts

root = Path(__file__).resolve().parents[1]
cache = root / ".tools/downloads/qwen3"
cache.mkdir(parents=True, exist_ok=True)
models = Path.home() / ".ollama/models"
blobs = models / "blobs"
blobs.mkdir(parents=True, exist_ok=True)
base = "https://registry.ollama.ai/v2/library/qwen3"
manifest_file = cache / "manifest.json"
if not manifest_file.exists():
    with urllib.request.urlopen(f"{base}/manifests/8b", timeout=60) as response:
        manifest_file.write_bytes(response.read())
manifest_bytes = manifest_file.read_bytes()
manifest = json.loads(manifest_bytes)
layers = [*manifest["layers"], manifest["config"]]
assert sum(layer["size"] for layer in layers) < 5_300_000_000, "Modelo maior que o tamanho informado"


def valid(path, size, digest):
    if not path.exists() or path.stat().st_size != size:
        return False
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest() == digest.split(":")[1]


for layer in layers:
    digest, size = layer["digest"], layer["size"]
    assert re.fullmatch(r"sha256:[a-f0-9]{64}", digest)
    target = blobs / digest.replace(":", "-")
    if valid(target, size, digest):
        continue
    if target.exists():
        raise RuntimeError("Blob existente inválido; preservado para diagnóstico.")
    partial = cache / (target.name + ".partial")
    if size > 100_000_000:
        download_parts(f"{base}/blobs/{digest}", partial, size)
    for attempt in range(4):
        have = partial.stat().st_size if partial.exists() else 0
        if have == size:
            break
        if have > size:
            raise RuntimeError("Download parcial maior que o esperado.")
        request = urllib.request.Request(f"{base}/blobs/{digest}",
            headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if have and (response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {have}-")):
                    raise RuntimeError("Servidor não confirmou a retomada.")
                last = time.monotonic()
                with partial.open("ab") as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
                        have += len(block)
                        if time.monotonic() - last > 30:
                            print(f"Qwen3: {have / 1e9:.2f} / {size / 1e9:.2f} GB", flush=True)
                            last = time.monotonic()
            break
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2)
    if not valid(partial, size, digest):
        raise RuntimeError("SHA-256 ou tamanho do modelo incorreto. Arquivo não instalado.")
    partial.replace(target)
    print(f"Blob verificado: {digest[:19]} ({size} bytes)", flush=True)
destination = models / "manifests/registry.ollama.ai/library/qwen3/8b"
destination.parent.mkdir(parents=True, exist_ok=True)
temporary = destination.with_suffix(".tmp")
temporary.write_bytes(manifest_bytes)
temporary.replace(destination)
print("Qwen3 8B instalado no cache padrão do Ollama, todos os SHA-256 verificados.", flush=True)
