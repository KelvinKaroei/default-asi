"""Credencial recebida por stdin; stdout contém somente a porta efêmera."""
import json
import os
from pathlib import Path
import socket
import sys
import threading

import uvicorn

from .server import create_app


def main():
    initialization = json.loads(sys.stdin.readline())
    token = initialization["token"]
    if len(token) < 32:
        raise ValueError("Credencial de sessão inválida")
    folder = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CyberAITutor"
    app = create_app(token, folder)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)

    class Server(uvicorn.Server):
        async def startup(self, sockets=None):
            await super().startup(sockets)
            print(json.dumps({"port": listener.getsockname()[1]}), flush=True)

    server = Server(uvicorn.Config(app, access_log=False, log_config=None, log_level="critical"))
    def watch_parent():
        sys.stdin.read()
        server.should_exit = True
    threading.Thread(target=watch_parent, daemon=True).start()
    server.run(sockets=[listener])


if __name__ == "__main__":
    main()
