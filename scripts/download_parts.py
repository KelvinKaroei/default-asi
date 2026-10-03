"""Download por intervalos HTTP para a instalação explícita de modelos."""
from concurrent.futures import ThreadPoolExecutor, wait
import shutil
import threading
import time
import urllib.request


def download_parts(url, partial, size):
    prefix = partial.stat().st_size if partial.exists() else 0
    if prefix == size:
        return
    if prefix > size:
        raise RuntimeError("Arquivo parcial maior que o esperado.")
    chunk = 128 * 1024 * 1024
    ranges = [(start, min(start + chunk - 1, size - 1)) for start in range(prefix, size, chunk)]
    progress = {}
    lock = threading.Lock()

    def transfer(bounds):
        start, end = bounds
        path = partial.with_name(f"{partial.name}.{start}-{end}.part")
        for attempt in range(5):
            have = path.stat().st_size if path.exists() else 0
            with lock:
                progress[start] = have
            if have == end - start + 1:
                return path
            request = urllib.request.Request(url, headers={"Range": f"bytes={start + have}-{end}"})
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    expected = f"bytes {start + have}-{end}/{size}"
                    if response.status != 206 or response.headers.get("Content-Range") != expected:
                        raise RuntimeError("Servidor não confirmou intervalo de download.")
                    with path.open("ab") as output:
                        while block := response.read(256 * 1024):
                            output.write(block)
                            have += len(block)
                            with lock:
                                progress[start] = have
                if have == end - start + 1:
                    return path
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("Parte incompleta; dados preservados.")

    print(f"Retomando modelo: {prefix / 1e9:.2f} / {size / 1e9:.2f} GB, até 16 conexões.", flush=True)
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(transfer, bounds) for bounds in ranges]
        while True:
            _, pending = wait(futures, timeout=30)
            with lock:
                downloaded = prefix + sum(progress.values())
            print(f"Qwen3: {downloaded / 1e9:.2f} / {size / 1e9:.2f} GB", flush=True)
            if not pending:
                break
        paths = [future.result() for future in futures]
    with partial.open("ab") as output:
        for path in paths:
            with path.open("rb") as source:
                shutil.copyfileobj(source, output, 1024 * 1024)
