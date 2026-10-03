import httpx
import pytest
from fastapi.testclient import TestClient

from app.server import create_app

TOKEN = "x" * 64


class FakeOllama:
    error = "Runtime ausente"
    offline = False
    remote = False
    calls = []

    async def start(self):
        pass

    async def close(self):
        pass

    async def call(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if self.offline:
            raise RuntimeError(self.error)
        if path == "/api/version":
            return {"version": "test"}
        if path == "/api/tags":
            return {"models": [{"name": "qwen3:8b", "size": 5200000000, "details": {"format": "gguf"}},
                               {"name": "remote:cloud", "size": 100, "details": {"format": "gguf"}}]}
        if path == "/api/ps":
            return {"models": []}
        if path == "/api/show":
            return {"capabilities": ["completion", "thinking"], "remote_host": "https://example.test" if self.remote else None}
        if path == "/api/generate":
            return {"response": "conexão local funcionando", "eval_count": 10,
                    "eval_duration": 500000000, "total_duration": 1000000000}
        raise AssertionError(path)


@pytest.fixture
def environment(tmp_path):
    runtime = FakeOllama()
    runtime.calls = []
    app = create_app(TOKEN, tmp_path, runtime)
    with TestClient(app, base_url="http://127.0.0.1:54321", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        yield client, runtime, tmp_path


def test_auth_host_origin_and_size(environment):
    client, _, _ = environment
    assert client.get("/api/v1/health", headers={"Authorization": ""}).status_code == 401
    assert client.get("/api/v1/health", headers={"Host": "attacker.test"}).status_code == 403
    assert client.get("/api/v1/health", headers={"Origin": "https://attacker.test"}).status_code == 403
    assert client.put("/api/v1/settings", content="x" * 8193).status_code == 413
    response = client.options("/api/v1/settings", headers={"Origin": "http://tauri.localhost",
        "Access-Control-Request-Method": "PUT", "Access-Control-Request-Headers": "authorization,content-type", "Authorization": ""})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://tauri.localhost"


def test_offline_keeps_backend_and_settings_available(environment):
    client, runtime, _ = environment
    runtime.offline = True
    assert client.get("/api/v1/health").json()["ollama"] == "offline"
    assert client.get("/api/v1/settings").status_code == 200
    assert client.get("/api/v1/models").status_code == 503


def test_model_selection_persistence_and_fixed_probe(environment):
    client, runtime, directory = environment
    assert len(client.get("/api/v1/models").json()["installed"]) == 1
    assert client.post("/api/v1/probe").status_code == 400
    assert client.put("/api/v1/settings", json={"model": "missing", "num_ctx": 4096}).status_code == 400
    assert client.put("/api/v1/settings", json={"model": "qwen3:8b", "num_ctx": 99999}).status_code == 422
    assert client.put("/api/v1/settings", json={"model": "qwen3:8b", "num_ctx": 4096}).status_code == 200
    assert "qwen3:8b" in (directory / "settings.json").read_text()
    result = client.post("/api/v1/probe").json()
    assert result["tokens_per_second"] == 20
    payload = next(kwargs["json"] for _, path, kwargs in runtime.calls if path == "/api/generate")
    assert payload["think"] is False
    assert payload["options"]["num_ctx"] == 4096
    assert payload["prompt"] == "Responda apenas: conexão local funcionando."
    assert not any(path == "/api/pull" for _, path, _ in runtime.calls)
    with TestClient(create_app(TOKEN, directory, FakeOllama()), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as reopened:
        assert reopened.get("/api/v1/settings").json()["model"] == "qwen3:8b"


def test_rejects_remote_model_even_with_local_tag(environment):
    client, runtime, _ = environment
    runtime.remote = True
    assert client.put("/api/v1/settings", json={"model": "qwen3:8b", "num_ctx": 4096}).status_code == 400


def test_timeout_returns_actionable_error_without_raw_exception(environment):
    client, runtime, _ = environment
    async def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("private internal details")
    runtime.call = timeout
    response = client.get("/api/v1/models")
    assert response.status_code == 503
    assert "Reduza o contexto" in response.json()["detail"]
    assert "private" not in response.text


def test_corrupt_settings_recover_and_unwritable_not_reported_saved(tmp_path):
    (tmp_path / "settings.json").write_text("broken")
    (tmp_path / "settings.tmp").mkdir()
    with TestClient(create_app(TOKEN, tmp_path, FakeOllama()), base_url="http://127.0.0.1", headers={"Authorization": f"Bearer {TOKEN}"}) as client:
        assert client.get("/api/v1/settings").json()["model"] is None
        assert "Valores padrão" in client.get("/api/v1/health").json()["message"]
        assert client.put("/api/v1/settings", json={"model": "qwen3:8b"}).status_code == 500
        assert client.get("/api/v1/settings").json()["model"] is None
