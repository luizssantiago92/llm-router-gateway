"""API key security dependency: byte comparison, early 401, OpenAPI schemes."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.cache.service import CacheService
from app.deps import get_settings
from app.main import create_app
from app.providers.fake import FakeProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.security import keys_match, require_gateway_key
from app.settings import Settings

API_KEY = "gateway-test"
NON_ASCII_KEY = "chave-ção"
HEADERS = {"X-API-Key": API_KEY}
CHAT = {
    "messages": [{"role": "user", "content": "hi"}],
    "temperature": 0.0,
    "max_tokens": 8,
}


class _Redis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value

    async def incr(self, key: str) -> int:
        value = int(self.data.get(key, "0")) + 1
        self.data[key] = str(value)
        return value

    async def decr(self, key: str) -> int:
        value = int(self.data.get(key, "0")) - 1
        self.data[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> None:
        return None

    async def ping(self) -> bool:
        return True


def _settings(*, gateway_api_key: str = API_KEY) -> Settings:
    return Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        gemini_api_key="gemini-test",
        gateway_api_key=gateway_api_key,
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
        chat_daily_limit=5,
    )


def _app(*, gateway_api_key: str = API_KEY) -> tuple[FastAPI, FakeProvider]:
    settings = _settings(gateway_api_key=gateway_api_key)
    redis = _Redis()
    local = FakeProvider("local", content="hello")
    cloud = FakeProvider("cloud", content="cloud")
    app = create_app(
        settings=settings,
        cache=CacheService(redis, settings.cache_ttl_seconds),
        router=Router(local, cloud, word_threshold=settings.complexity_word_threshold),
        redis=redis,
        local=local,
        cloud=cloud,
        quota=DailyQuota(redis, settings.chat_daily_limit),
    )
    return app, local


def _unauthorized(response_json: dict[str, object]) -> None:
    error = response_json["error"]
    assert isinstance(error, dict)
    assert error["type"] == "unauthorized"
    assert error["message"] == "missing or invalid X-API-Key"


async def _asgi(
    app: FastAPI,
    *,
    headers: list[tuple[bytes, bytes]],
    body: bytes,
) -> tuple[int, dict[str, object]]:
    sent = False

    async def receive() -> dict[str, object]:
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    messages: list[dict[str, object]] = []

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/chat/completions",
        "raw_path": b"/v1/chat/completions",
        "query_string": b"",
        "headers": headers,
        "client": ("test", 123),
        "server": ("test", 80),
    }
    await app(scope, receive, send)
    status = next(
        message["status"] for message in messages if message["type"] == "http.response.start"
    )
    chunks: list[bytes] = []
    for message in messages:
        if message["type"] != "http.response.body":
            continue
        body = message["body"]
        assert isinstance(body, bytes)
        chunks.append(body)
    payload = b"".join(chunks)
    parsed = json.loads(payload) if payload else {}
    assert isinstance(status, int)
    assert isinstance(parsed, dict)
    return status, parsed


def _latin1(name: str, value: str) -> tuple[bytes, bytes]:
    return name.encode("ascii"), value.encode("latin-1")


def test_keys_match_compares_utf8_bytes_and_rejects_an_empty_gateway_key() -> None:
    assert keys_match(NON_ASCII_KEY, NON_ASCII_KEY) is True
    assert keys_match("other", NON_ASCII_KEY) is False
    assert keys_match("", API_KEY) is False
    assert keys_match(API_KEY, "") is False


def test_openapi_lists_api_key_and_bearer_schemes_on_chat_only() -> None:
    schema = create_app().openapi()
    schemes = schema["components"]["securitySchemes"]
    assert schemes["APIKeyHeader"] == {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"
    chat_security = schema["paths"]["/v1/chat/completions"]["post"]["security"]
    assert {"APIKeyHeader": []} in chat_security
    assert {"HTTPBearer": []} in chat_security
    assert "security" not in schema["paths"]["/health"]["get"]


@pytest.mark.asyncio
async def test_non_ascii_api_key_and_bearer_return_401() -> None:
    app, local = _app()
    body = json.dumps(CHAT).encode("utf-8")
    status, payload = await _asgi(
        app,
        headers=[
            _latin1("x-api-key", NON_ASCII_KEY),
            _latin1("content-type", "application/json"),
        ],
        body=body,
    )
    assert status == 401
    _unauthorized(payload)

    status, payload = await _asgi(
        app,
        headers=[
            _latin1("authorization", f"Bearer {NON_ASCII_KEY}"),
            _latin1("content-type", "application/json"),
        ],
        body=body,
    )
    assert status == 401
    _unauthorized(payload)
    assert local.calls == 0


@pytest.mark.asyncio
async def test_matching_non_ascii_key_is_accepted() -> None:
    app, local = _app(gateway_api_key=NON_ASCII_KEY)
    status, payload = await _asgi(
        app,
        headers=[
            _latin1("x-api-key", NON_ASCII_KEY),
            _latin1("content-type", "application/json"),
        ],
        body=json.dumps(CHAT).encode("utf-8"),
    )
    assert status == 200
    assert payload["provider"] == "local"
    assert local.calls == 1


@pytest.mark.asyncio
async def test_missing_credential_is_401_before_body_validation() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid_json = await client.post(
            "/v1/chat/completions",
            content=b"{",
            headers={"content-type": "application/json"},
        )
        invalid_schema = await client.post("/v1/chat/completions", json={})
        health = await client.get("/health")
    assert invalid_json.status_code == 401
    _unauthorized(invalid_json.json())
    assert invalid_schema.status_code == 401
    _unauthorized(invalid_schema.json())
    assert health.status_code == 200
    assert local.calls == 0


@pytest.mark.asyncio
async def test_valid_key_still_validates_the_body() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid_json = await client.post(
            "/v1/chat/completions",
            content=b"{",
            headers={**HEADERS, "content-type": "application/json"},
        )
        invalid_schema = await client.post("/v1/chat/completions", headers=HEADERS, json={})
    assert invalid_json.status_code == 422
    assert invalid_schema.status_code == 422
    assert local.calls == 0


@pytest.mark.asyncio
async def test_bearer_token_authorizes_chat() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=CHAT,
        )
    assert response.status_code == 200
    assert response.json()["provider"] == "local"
    assert local.calls == 1


@pytest.mark.asyncio
async def test_wrong_header_can_fall_through_to_a_matching_bearer() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers={"X-API-Key": "wrong", "Authorization": f"Bearer {API_KEY}"},
            json=CHAT,
        )
    assert response.status_code == 200
    assert local.calls == 1


@pytest.mark.asyncio
async def test_empty_gateway_key_is_rejected() -> None:
    app, local = _app(gateway_api_key="")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
    assert response.status_code == 401
    _unauthorized(response.json())
    assert local.calls == 0


@pytest.mark.asyncio
async def test_settings_override_runs_before_body_validation() -> None:
    app, local = _app()

    async def other() -> Settings:
        return _settings(gateway_api_key="other-key")

    app.dependency_overrides[get_settings] = other
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        rejected = await client.post(
            "/v1/chat/completions",
            content=b"{",
            headers={**HEADERS, "content-type": "application/json"},
        )
    assert rejected.status_code == 401
    _unauthorized(rejected.json())
    assert local.calls == 0

    app.dependency_overrides[get_settings] = lambda: "not-settings"
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        broken = await client.post("/v1/chat/completions", headers=HEADERS, json=CHAT)
    assert broken.status_code == 500


@pytest.mark.asyncio
async def test_security_dependency_override_is_honored_before_the_body() -> None:
    app, local = _app()

    async def allow() -> str:
        return API_KEY

    app.dependency_overrides[require_gateway_key] = allow
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        allowed = await client.post("/v1/chat/completions", json=CHAT)
    assert allowed.status_code == 200
    assert local.calls == 1

    app.dependency_overrides[require_gateway_key] = lambda: None
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        rejected = await client.post(
            "/v1/chat/completions",
            content=b"{",
            headers={"content-type": "application/json"},
        )
    assert rejected.status_code == 401
    _unauthorized(rejected.json())
