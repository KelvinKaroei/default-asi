"""Teste real opcional. Não baixa modelos. Executar com o Python da .venv."""
import json
import argparse
from pathlib import Path
import secrets
import subprocess
import threading
import time

import httpx
import psutil

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--connection-only", action="store_true", help="Verifica o servidor sem carregar modelo")
parser.add_argument("--warm", action="store_true", help="Repete a inferência com o modelo carregado")
options = parser.parse_args()
token = secrets.token_hex(32)
process = subprocess.Popen([str(root / ".venv/Scripts/python.exe"), "-m", "app"],
    cwd=root / "backend", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
owned = []
try:
    process.stdin.write(json.dumps({"token": token}) + "\n")
    process.stdin.flush()
    port = json.loads(process.stdout.readline())["port"]
    with httpx.Client(base_url=f"http://127.0.0.1:{port}/api/v1", trust_env=False,
                      headers={"Authorization": f"Bearer {token}"}, timeout=190) as client:
        print("Hardware:", client.get("/hardware").json(), flush=True)
        for _ in range(45):
            health = client.get("/health").json()
            if health["ollama"] == "ready":
                break
            time.sleep(0.25)
        print("Health:", health, flush=True)
        assert health["ollama"] == "ready", health
        models = client.get("/models").json()
        print("Modelos:", [m["name"] for m in models["installed"]], flush=True)
        if not options.connection_only:
            result = client.put("/settings", json={"model": "qwen3:8b", "num_ctx": 4096})
            result.raise_for_status()
            samples = []
            sampling = threading.Event()
            def sample_memory():
                while not sampling.is_set():
                    samples.append(psutil.virtual_memory().available)
                    sampling.wait(0.25)
            monitor = threading.Thread(target=sample_memory, daemon=True)
            monitor.start()
            try:
                result = client.post("/probe")
            finally:
                sampling.set()
                monitor.join(timeout=2)
            result.raise_for_status()
            print("Inferência:", json.dumps(result.json(), ensure_ascii=False), flush=True)
            print("Menor RAM livre observada no teste (GiB):", round(min(samples) / 2**30, 2), flush=True)
            if options.warm:
                warmed = client.post("/probe")
                warmed.raise_for_status()
                print("Inferência com modelo carregado:", json.dumps(warmed.json(), ensure_ascii=False), flush=True)
        assert client.get("/health", headers={"Authorization": ""}).status_code == 401
        owned = psutil.Process(process.pid).children(recursive=True)
        listeners = [c for c in psutil.net_connections(kind="tcp") if c.status == "LISTEN"
                     and c.pid in {process.pid, *(p.pid for p in owned)}]
        print("Listeners:", [(c.laddr.ip, c.laddr.port) for c in listeners], flush=True)
        assert all(c.laddr.ip == "127.0.0.1" for c in listeners)
finally:
    process.stdin.close()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        raise
    print("Backend encerrado:", process.returncode, flush=True)
    # Conhost pode terminar instantes depois do processo principal no Windows.
    _, pending = psutil.wait_procs(owned, timeout=5)
    survivors = [p.pid for p in pending if p.is_running()]
    print("Processos auxiliares sobreviventes:", survivors, flush=True)
    assert not survivors
