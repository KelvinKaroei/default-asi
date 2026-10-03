import asyncio
from contextlib import asynccontextmanager
import hmac
import sqlite3
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse

from .hardware import detect_hardware
from .runtime import Ollama
from .diagnostics import local_logger
from .chat import ChatRequest, chat_response
from .history import History, HistoryStore
from .materials import materials_router
from .retrieval import Retrieval
from .learning import learning_router
from .memory import MemoryStore

ORIGINS = ["http://tauri.localhost", "tauri://localhost", "http://127.0.0.1:1420"]


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str | None = Field(default=None, max_length=200)
    num_ctx: Literal[2048, 4096, 8192, 16384, 32768] = 32768
    max_output: Literal[1024, 2048, 4096, 8192] = 8192


class SessionGuard:
    def __init__(self, app, token):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        host = headers.get(b"host", b"").decode().split(":")[0]
        origin = headers.get(b"origin", b"").decode()
        if host != "127.0.0.1" or (origin and origin not in ORIGINS):
            return await JSONResponse({"detail": "Origem local inválida."}, 403)(scope, receive, send)
        if scope["method"] != "OPTIONS" and not hmac.compare_digest(
                headers.get(b"authorization", b""), f"Bearer {self.token}".encode()):
            return await JSONResponse({"detail": "Sessão não autorizada."}, 401)(scope, receive, send)
        body = b""
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            body += event.get("body", b"")
            limit = 8 * 1024 * 1024 if scope["path"] == "/api/v1/chat" else 8192
            if scope["path"] in ("/api/v1/history", "/api/v1/materials"):
                limit = 8 * 1024 * 1024
            if len(body) > limit:
                return await JSONResponse({"detail": "Requisição muito grande."}, 413)(scope, receive, send)
            if not event.get("more_body"):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body}
            return await receive()
        await self.app(scope, replay, send)


def create_app(token: str, data_dir: Path, runtime=None):
    data_dir.mkdir(parents=True, exist_ok=True)
    settings_path = data_dir / "settings.json"
    settings_warning = ""
    try:
        settings = Settings.model_validate_json(settings_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        settings = Settings()
    except (OSError, ValueError):
        settings = Settings()
        settings_warning = "As configurações não puderam ser lidas. Valores padrão foram carregados; salve novamente para corrigir. "
    ollama = runtime or Ollama()
    logger = local_logger(data_dir)
    if settings_warning:
        logger.warning("settings_read_failed_using_defaults")
    probe_lock = asyncio.Lock()
    history_store = HistoryStore(data_dir)
    retrieval = Retrieval(data_dir, ollama, probe_lock)
    memory = MemoryStore(data_dir)

    async def start_runtime():
        await ollama.start()
        logger.info("ollama_start_ready" if not ollama.error else "ollama_start_unavailable")

    @asynccontextmanager
    async def lifespan(app):
        logger.info("backend_start")
        await start_runtime()
        yield
        await retrieval.close()
        await ollama.close()
        logger.info("backend_stop")
        for handler in logger.handlers:
            handler.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=ORIGINS,
                       allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
    app.add_middleware(SessionGuard, token=token)
    app.include_router(materials_router(data_dir))
    app.include_router(learning_router(data_dir))
    app.include_router(memory.router())

    @app.get('/api/v1/retrieval')
    def retrieval_status():
        return retrieval.status()

    @app.post('/api/v1/retrieval/index')
    async def retrieval_index():
        return retrieval.start()

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request, error):
        logger.warning("history_storage_failed")
        return JSONResponse({"detail": "Não foi possível acessar o banco local. Verifique espaço e permissões. O banco existente não foi apagado."}, 503)

    @app.get("/api/v1/history")
    def read_history():
        return history_store.read()

    @app.put("/api/v1/history")
    def save_history(value: History):
        return history_store.save(value)

    @app.post("/api/v1/history/backup")
    def backup_history():
        return history_store.backup()

    class RestoreRequest(BaseModel):
        revision: int = Field(ge=0)

    @app.post("/api/v1/history/restore")
    def restore_history(value: RestoreRequest):
        return history_store.restore(value.revision)

    @app.exception_handler(RuntimeError)
    async def runtime_error(request, error):
        logger.warning("ollama_unavailable")
        return JSONResponse({"detail": str(error)}, 503)

    @app.exception_handler(httpx.HTTPError)
    async def connection_error(request, error):
        logger.warning("ollama_request_failed")
        message = "Ollama indisponível. Verifique o runtime e a memória livre."
        if isinstance(error, httpx.TimeoutException):
            message = "Ollama excedeu o tempo limite. Reduza o contexto ou use um modelo menor."
        return JSONResponse({"detail": message}, 503)

    @app.get("/api/v1/health")
    async def health():
        try:
            version = await ollama.call("GET", "/api/version")
            return {"backend": "ready", "ollama": "ready", "version": version["version"], "message": settings_warning + "Inferência local; nuvem desativada."}
        except (RuntimeError, httpx.HTTPError):
            return {"backend": "ready", "ollama": "offline", "version": None, "message": settings_warning + (ollama.error or "Ollama está iniciando ou indisponível.")}

    @app.post("/api/v1/ollama/start")
    async def start():
        await start_runtime()
        return await health()

    @app.get("/api/v1/hardware")
    def hardware():
        return detect_hardware(data_dir)

    @app.get("/api/v1/models")
    async def models():
        installed = await ollama.call("GET", "/api/tags")
        loaded = await ollama.call("GET", "/api/ps")
        return {"installed": [m for m in installed.get("models", []) if m.get("size", 0) > 0
                              and m.get("details", {}).get("format") == "gguf"
                              and "cloud" not in m.get("name", "").lower()],
                "loaded": loaded.get("models", [])}

    async def validate_model(name):
        available = await models()
        if name not in [m["name"] for m in available["installed"]]:
            raise HTTPException(400, "Selecione um modelo local instalado. Nenhum download é automático.")
        info = await ollama.call("POST", "/api/show", json={"model": name})
        if info.get("remote_model") or info.get("remote_host") or "completion" not in info.get("capabilities", []):
            raise HTTPException(400, "Este modelo não oferece geração de texto local.")
        return info

    @app.get("/api/v1/settings")
    async def get_settings():
        return settings

    @app.put("/api/v1/settings")
    async def save_settings(value: Settings):
        nonlocal settings, settings_warning
        if value.model:
            await validate_model(value.model)
        try:
            temporary = settings_path.with_suffix(".tmp")
            temporary.write_text(value.model_dump_json(indent=2), encoding="utf-8")
            temporary.replace(settings_path)
        except OSError:
            raise HTTPException(500, "Não foi possível salvar as configurações locais.")
        settings = value
        settings_warning = ""
        return settings

    @app.post("/api/v1/probe")
    async def probe():
        if probe_lock.locked():
            raise HTTPException(409, "Já existe um teste de inferência em andamento.")
        async with probe_lock:
            selected = settings.model_copy()
            info = await validate_model(selected.model)
            payload = {"model": selected.model, "prompt": "Responda apenas: conexão local funcionando.",
                       "stream": False, "keep_alive": "2m",
                       "options": {"num_ctx": selected.num_ctx, "num_predict": 64, "temperature": 0}}
            if "thinking" in info.get("capabilities", []):
                payload["think"] = False
            logger.info("inference_probe_started")
            result = await ollama.call("POST", "/api/generate", json=payload, timeout=180)
            logger.info("inference_probe_completed")
            duration = result.get("eval_duration", 0) / 1e9
            return {"answer": result.get("response", ""), "model": selected.model,
                    "tokens_per_second": round(result.get("eval_count", 0) / duration, 1) if duration else None,
                    "total_seconds": round(result.get("total_duration", 0) / 1e9, 2),
                    "load_seconds": round(result["load_duration"] / 1e9, 2) if "load_duration" in result else None,
                    "loaded": (await models())["loaded"]}

    @app.post("/api/v1/chat")
    async def chat(body: ChatRequest):
        return chat_response(body, settings.model_copy(), ollama, validate_model, probe_lock, logger, retrieval, memory)

    return app
