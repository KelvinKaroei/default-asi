import asyncio
import os
import json
from pathlib import Path
import socket
import subprocess

import httpx
import psutil


class Ollama:
    """Gerencia exclusivamente o processo iniciado por este aplicativo."""

    def __init__(self):
        self.process = None
        self.error = "Ollama ainda não iniciado."
        self.start_lock = asyncio.Lock()
        self.stop_lock = asyncio.Lock()
        self.owned = {}
        self.watcher = None
        self.client = httpx.AsyncClient(base_url="http://127.0.0.1:11434", trust_env=False,
                                       timeout=5, follow_redirects=False)

    async def start(self):
        async with self.start_lock:
            await self._start()

    async def _start(self):
        if self.process and self.process.poll() is None:
            return
        await self.stop_process()
        binary = Path(os.environ["CYBER_OLLAMA_PATH"]) if os.environ.get("CYBER_OLLAMA_PATH") else Path(__file__).resolve().parents[2] / ".tools/ollama/ollama.exe"
        if not binary.exists():
            self.error = "O runtime portátil do Ollama ainda não foi instalado."
            return
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", 11434)) == 0:
                self.error = "A porta 11434 está ocupada. Feche o outro Ollama e tente novamente."
                return
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP",
                                  "USERPROFILE", "LOCALAPPDATA", "APPDATA", "HOME"}}
        env.update(OLLAMA_HOST="127.0.0.1:11434", OLLAMA_NO_CLOUD="1",
                   OLLAMA_NUM_PARALLEL="1", OLLAMA_MAX_LOADED_MODELS="1",
                   OLLAMA_FLASH_ATTENTION="1", OLLAMA_KV_CACHE_TYPE="q8_0",
                   OLLAMA_CONTEXT_LENGTH="32768", OLLAMA_MODELS=str(Path.home() / ".ollama/models"))
        try:
            self.process = subprocess.Popen([str(binary), "serve"], env=env,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.remember_processes()
            self.watcher = asyncio.create_task(self.watch_processes())
            for _ in range(30):
                try:
                    await self.call("GET", "/api/version", timeout=0.2)
                    self.error = ""
                    return
                except (httpx.HTTPError, RuntimeError):
                    await asyncio.sleep(0.2)
            self.error = "Ollama não respondeu a tempo. Tente iniciar novamente."
            await self.stop_process()
        except OSError:
            self.error = "Não foi possível executar o runtime portátil do Ollama."

    async def call(self, method, path, **kwargs):
        if not self.process or self.process.poll() is not None:
            raise RuntimeError(self.error or "O processo Ollama foi encerrado.")
        response = await self.client.request(method, path, **kwargs)
        response.raise_for_status()
        try:
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except ValueError:
            raise RuntimeError("Ollama retornou uma resposta inválida. Reinicie o aplicativo.")

    def remember_processes(self):
        """Retém identidades dos filhos antes que o pai possa desaparecer."""
        if self.process and self.process.poll() is None:
            try:
                parent = psutil.Process(self.process.pid)
                for process in [parent] + parent.children(recursive=True):
                    self.owned[(process.pid, process.create_time())] = process
            except psutil.NoSuchProcess:
                pass

    async def watch_processes(self):
        while self.process and self.process.poll() is None:
            self.remember_processes()
            await asyncio.sleep(0.2)

    async def stop_process(self):
        async with self.stop_lock:
            if self.watcher:
                self.watcher.cancel()
                await asyncio.gather(self.watcher, return_exceptions=True)
                self.watcher = None
            self.remember_processes()
            owned = list(reversed(self.owned.values()))
            for process in owned:
                try:
                    # psutil verifica a identidade antes de enviar o sinal.
                    process.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = await asyncio.to_thread(psutil.wait_procs, owned, timeout=3)
            for process in alive:
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
            if alive:
                await asyncio.to_thread(psutil.wait_procs, alive, timeout=3)
            self.owned.clear()
            self.process = None

    async def chat_stream(self, payload):
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("Ollama não está em execução.")
        async with self.client.stream("POST", "/api/chat", json=payload,
                                      timeout=httpx.Timeout(120, connect=5)) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                self.remember_processes()
                if line:
                    if len(line) > 262144:
                        raise ValueError("Evento excedeu o limite")
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        raise ValueError("Evento inválido")
                    yield item

    async def close(self):
        await self.stop_process()
        await self.client.aclose()
