"""Startup and shutdown of the default FastAPI lifespan."""

from __future__ import annotations

import pytest

from app.cache.service import CacheService
from app.main import build_default_app, create_app
from app.providers.fake import FakeProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import Settings

_ENV = {
    "REDIS_URL": "redis://localhost:6379/0",
    "OLLAMA_BASE_URL": "http://ollama",
    "GEMINI_API_KEY": "gemini-test",
    "GATEWAY_API_KEY": "gateway-test",
}


class _Closable:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class _BoomRedis(_Closable):
    async def aclose(self) -> None:
        self.closed = True
        raise RuntimeError("redis close failed")


def _settings() -> Settings:
    return Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        gemini_api_key="gemini-test",
        gateway_api_key="gateway-test",
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
    )


def _install_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _ENV.items():
        monkeypatch.setenv(key, value)


@pytest.mark.asyncio
async def test_default_lifespan_opens_and_closes_redis_and_http_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_env(monkeypatch)
    opened: list[_Closable] = []
    clients: list[_Closable] = []

    def from_url(url: str, decode_responses: bool = True) -> _Closable:
        assert url == _ENV["REDIS_URL"]
        assert decode_responses is True
        redis = _Closable()
        opened.append(redis)
        return redis

    def client_factory(*args: object, **kwargs: object) -> _Closable:
        client = _Closable(*args, **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr("app.runtime.Redis.from_url", from_url)
    monkeypatch.setattr("app.runtime.httpx.AsyncClient", client_factory)

    app = build_default_app()
    assert app.state.redis is None
    assert app.state.settings is None

    async with app.router.lifespan_context(app):
        redis = opened[0]
        assert app.state.redis is redis
        assert app.state.settings.redis_url == _ENV["REDIS_URL"]
        assert isinstance(app.state.cache, CacheService)
        assert isinstance(app.state.quota, DailyQuota)
        assert isinstance(app.state.router, Router)
        assert isinstance(app.state.local, OllamaProvider)
        assert isinstance(app.state.cloud, GeminiProvider)
        assert app.state.local._client is clients[0]
        assert app.state.cloud._client is clients[1]
        assert clients[0].kwargs["timeout"] == 30
        assert clients[1].kwargs["timeout"] == 30
        assert app.state.local._base_url == "http://ollama"
        assert app.state.cloud._model == "gemini-3.5-flash"
        assert app.state.cache._ttl_seconds == 3600
        assert app.state.quota._limit == 5
        assert app.state.router._word_threshold == 150

    assert opened[0].closed is True
    assert [client.closed for client in clients] == [True, True]
    assert app.state.redis is None
    assert app.state.local is None
    assert app.state.cloud is None
    assert app.state.settings is None


@pytest.mark.asyncio
async def test_lifespan_closes_http_clients_when_redis_close_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_env(monkeypatch)
    clients: list[_Closable] = []
    redis = _BoomRedis()
    monkeypatch.setattr("app.runtime.Redis.from_url", lambda *args, **kwargs: redis)

    def client_factory(*args: object, **kwargs: object) -> _Closable:
        client = _Closable(*args, **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr("app.runtime.httpx.AsyncClient", client_factory)
    app = build_default_app()

    with pytest.raises(RuntimeError, match="redis close failed"):
        async with app.router.lifespan_context(app):
            assert app.state.redis is redis

    assert redis.closed is True
    assert [client.closed for client in clients] == [True, True]
    assert app.state.redis is None
    assert app.state.settings is None


@pytest.mark.asyncio
async def test_lifespan_does_not_replace_or_close_injected_resources() -> None:
    redis = _Closable()
    local = FakeProvider("local")
    cloud = FakeProvider("cloud")
    settings = _settings()
    app = create_app(
        settings=settings,
        cache=CacheService(redis, 60),
        router=Router(local, cloud),
        redis=redis,
        local=local,
        cloud=cloud,
        quota=DailyQuota(redis, 5),
    )

    async with app.router.lifespan_context(app):
        assert app.state.redis is redis
        assert app.state.local is local
        assert app.state.cloud is cloud
        assert app.state.settings is settings

    assert redis.closed is False
    assert app.state.redis is redis
    assert app.state.settings is settings


@pytest.mark.asyncio
async def test_partial_injection_is_not_replaced_by_the_default_runtime() -> None:
    settings = _settings()
    app = create_app(settings=settings)

    async with app.router.lifespan_context(app):
        assert app.state.settings is settings
        assert app.state.redis is None

    assert app.state.settings is settings


@pytest.mark.asyncio
async def test_default_lifespan_fails_closed_without_required_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in _ENV:
        monkeypatch.delenv(key, raising=False)
    app = build_default_app()

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        async with app.router.lifespan_context(app):
            pass

    assert app.state.redis is None
    assert app.state.settings is None
