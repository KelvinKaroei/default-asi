import asyncio
import socket
import subprocess
import sys
import psutil
from unittest.mock import patch
from app.runtime import Ollama


def test_missing_runtime_has_actionable_error():
    async def run():
        runtime = Ollama()
        with patch("app.runtime.Path.exists", return_value=False):
            await runtime.start()
        assert runtime.process is None
        assert "não foi instalado" in runtime.error
        await runtime.close()
    asyncio.run(run())


def test_existing_listener_is_not_adopted_or_terminated():
    async def run():
        runtime = Ollama()
        with socket.socket() as listener:
            # Sem ocupar a porta real do usuário durante testes unitários.
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            with patch("app.runtime.Path.exists", return_value=True), \
                 patch("app.runtime.socket.socket.connect_ex", return_value=0), \
                 patch("app.runtime.subprocess.Popen") as spawn:
                await runtime.start()
                spawn.assert_not_called()
            assert "ocupada" in runtime.error
            assert runtime.process is None
        await runtime.close()
    asyncio.run(run())


def test_shutdown_only_terminates_owned_process():
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    owned = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], creationflags=flags)
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], creationflags=flags)
    async def run():
        runtime = Ollama()
        runtime.process = owned
        await runtime.close()
        assert owned.wait(timeout=5) is not None
        assert unrelated.poll() is None
    try:
        asyncio.run(run())
    finally:
        for process in (owned, unrelated):
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)


def test_shutdown_remembers_children_after_parent_dies():
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    script = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); print(p.pid,flush=True); time.sleep(60)"
    parent = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE,
                              text=True, creationflags=flags)
    child = psutil.Process(int(parent.stdout.readline()))
    async def run():
        runtime = Ollama()
        runtime.process = parent
        runtime.remember_processes()
        parent.terminate()
        parent.wait(timeout=5)
        assert child.is_running()
        await runtime.close()
        assert not child.is_running()
    try:
        asyncio.run(run())
    finally:
        if parent.poll() is None:
            parent.terminate()
        parent.wait(timeout=5)
        if child.is_running():
            child.kill()
        parent.stdout.close()
