"""Handlers receive process resources through FastAPI dependencies."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request

from app.cache.service import CacheService
from app.deps import (
    get_cache,
    get_cloud,
    get_local,
    get_quota,
    get_redis,
    get_router,
    get_settings,
)
from app.main import create_app
from app.providers.fake import FakeProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import Settings

API_KEY = "gateway-test"
HEADERS = {"X-API-Key": API_KEY}


class _Redis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
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
        if self.fail:
            raise ConnectionError("redis down")
        return True


class _DownRedis:
    async def ping(self) -> bool:
        raise ConnectionError("redis down")


class _HitCache:
    async def get(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
        **_extra: object,
    ) -> dict[str, str]:
        return {"content": "from-cache", "provider": "cloud"}

    async def store(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("cache hit must not store")


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


def _app() -> tuple[FastAPI, FakeProvider, FakeProvider]:
    settings = _settings()
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
    return app, local, cloud


def _request(app: FastAPI) -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": ("test", 123),
            "server": ("test", 80),
            "app": app,
        }
    )


def test_dependency_providers_read_configured_state() -> None:
    app, local, cloud = _app()
    request = _request(app)
    assert get_settings(request) is app.state.settings
    assert get_redis(request) is app.state.redis
    assert get_cache(request) is app.state.cache
    assert get_router(request) is app.state.router
    assert get_quota(request) is app.state.quota
    assert get_local(request) is local
    assert get_cloud(request) is cloud


def test_dependency_providers_reject_missing_resources() -> None:
    app = create_app()
    request = _request(app)
    assert get_redis(request) is None
    assert get_local(request) is None
    assert get_cloud(request) is None
    assert get_quota(request) is None
    with pytest.raises(RuntimeError, match="settings"):
        get_settings(request)
    with pytest.raises(RuntimeError, match="cache"):
        get_cache(request)
    with pytest.raises(RuntimeError, match="router"):
        get_router(request)

    app.state.quota = "not-a-quota"
    with pytest.raises(RuntimeError, match="quota"):
        get_quota(_request(app))


def test_public_routes_stay_registered() -> None:
    paths = create_app().openapi()["paths"]
    assert "get" in paths["/health"]
    assert "post" in paths["/v1/chat/completions"]


@pytest.mark.asyncio
async def test_chat_uses_settings_dependency_not_app_state() -> None:
    app, local, _cloud = _app()
    app.dependency_overrides[get_settings] = lambda: _settings(gateway_api_key="other-key")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert response.status_code == 401
    assert local.calls == 0


@pytest.mark.asyncio
async def test_chat_uses_cache_dependency() -> None:
    app, local, cloud = _app()
    app.dependency_overrides[get_cache] = lambda: _HitCache()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["cached"] is True
    assert body["provider"] == "cloud"
    assert body["choices"][0]["message"]["content"] == "from-cache"
    assert local.calls == 0
    assert cloud.calls == 0


@pytest.mark.asyncio
async def test_health_uses_redis_and_provider_dependencies() -> None:
    app, _local, _cloud = _app()
    app.dependency_overrides[get_redis] = lambda: _DownRedis()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        down = await client.get("/health")
    assert down.status_code == 503
    assert down.json()["redis"] == "down"

    app.dependency_overrides.pop(get_redis)
    app.dependency_overrides[get_local] = lambda: FakeProvider("local", healthy=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        degraded = await client.get("/health")
    assert degraded.status_code == 200
    assert degraded.json()["status"] == "degraded"
    assert degraded.json()["providers"]["local"] == "down"
    assert degraded.json()["providers"]["cloud"] == "up"


@pytest.mark.asyncio
async def test_unconfigured_chat_does_not_accept_a_key() -> None:
    transport = ASGITransport(app=create_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert response.status_code == 500
