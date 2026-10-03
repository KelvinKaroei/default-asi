"""Baixa o runtime oficial fixado, verifica SHA-256 e extrai no projeto."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import shutil
import time
import urllib.request
import zipfile

URL = "https://github.com/ollama/ollama/releases/download/v0.34.4/ollama-windows-amd64.zip"
SIZE = 1461155106
SHA256 = "535193f38f3344e5b08f5d1c171c31ce11aa17f0124ff69ae26d8ec7fe06fa62"
root = Path(__file__).resolve().parents[1]
downloads = root / ".tools/downloads"
downloads.mkdir(parents=True, exist_ok=True)
archive = downloads / "ollama-windows-amd64.zip"
prefix = archive.stat().st_size if archive.exists() else 0
if prefix > SIZE:
    raise RuntimeError("Arquivo maior que o esperado; não foi alterado.")


def download(bounds):
    start, end = bounds
    part = downloads / f"ollama-{start}-{end}.part"
    for attempt in range(4):
        have = part.stat().st_size if part.exists() else 0
        if have == end - start + 1:
            return part
        if have > end - start + 1:
            raise RuntimeError("Parte inválida; não foi alterada.")
        request = urllib.request.Request(URL, headers={"Range": f"bytes={start + have}-{end}"})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start + have}-{end}/{SIZE}":
                    raise RuntimeError("Servidor não confirmou o intervalo solicitado.")
                with part.open("ab") as output:
                    shutil.copyfileobj(response, output, length=1024 * 1024)
            if part.stat().st_size == end - start + 1:
                print(f"Parte concluída: {start}-{end}", flush=True)
                return part
        except OSError:
            if attempt == 3:
                raise
            time.sleep(2)
    raise RuntimeError("Download incompleto; partes preservadas para retomar.")


if prefix < SIZE:
    chunk = (SIZE - prefix + 3) // 4
    ranges = [(start, min(start + chunk - 1, SIZE - 1)) for start in range(prefix, SIZE, chunk)]
    print(f"Retomando {prefix / 1e6:.1f} MB de {SIZE / 1e6:.1f} MB, 4 conexões.", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        parts = list(pool.map(download, ranges))
    with archive.open("ab") as output:
        for part in parts:
            with part.open("rb") as source:
                shutil.copyfileobj(source, output)
with archive.open("rb") as source:
    digest = hashlib.file_digest(source, "sha256").hexdigest()
if digest != SHA256:
    raise RuntimeError("SHA-256 incorreto; o runtime não será extraído nem executado.")
print("SHA-256 confirmado. Extraindo runtime oficial…", flush=True)
destination = root / ".tools/ollama"
with zipfile.ZipFile(archive) as source:
    for name in source.namelist():
        if not (destination / name).resolve().is_relative_to(destination.resolve()):
            raise RuntimeError("Entrada fora da pasta de instalação.")
    source.extractall(destination)
print("Runtime instalado em .tools/ollama.", flush=True)
