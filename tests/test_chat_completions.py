import pytest
from httpx import ASGITransport, AsyncClient

from app.cache.service import CacheService
from app.main import create_app
from app.providers.base import ProviderError
from app.providers.fake import FakeProvider
from app.routing.router import Router
from app.settings import Settings


class MemoryRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value
        self.ttls[key] = ex


def _app(local: FakeProvider, cloud: FakeProvider) -> tuple:
    settings = Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        openai_api_key="sk-test",
        cache_ttl_seconds=3600,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
    )
    redis = MemoryRedis()
    cache = CacheService(redis, settings.cache_ttl_seconds)
    router = Router(local, cloud, word_threshold=settings.complexity_word_threshold)
    app = create_app(
        settings=settings,
        cache=cache,
        router=router,
        redis=redis,
        local=local,
        cloud=cloud,
    )
    return app, local, cloud, redis


@pytest.mark.asyncio
async def test_valid_completion_cache_miss_calls_local() -> None:
    app, local, cloud, redis = _app(FakeProvider("local", content="hello"), FakeProvider("cloud"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "temperature": 0.0,
                "max_tokens": 8,
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["cached"] is False
    assert body["provider"] == "local"
    assert body["choices"][0]["message"]["content"] == "hello"
    assert local.calls == 1
    assert cloud.calls == 0
    assert redis.data


@pytest.mark.asyncio
async def test_cache_hit_skips_providers() -> None:
    app, local, cloud, _redis = _app(FakeProvider("local", content="hello"), FakeProvider("cloud"))
    transport = ASGITransport(app=app)
    payload = {
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.0,
        "max_tokens": 8,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/v1/chat/completions", json=payload)
        second = await client.post("/v1/chat/completions", json=payload)
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert second.headers["x-cache"] == "true"
    assert second.headers["x-provider"] == "local"
    assert "x-latency-ms" in second.headers
    assert local.calls == 1


@pytest.mark.asyncio
async def test_invalid_body_returns_422_without_provider_calls() -> None:
    app, local, cloud, redis = _app(FakeProvider("local"), FakeProvider("cloud"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", json={"temperature": 0.2})
    assert response.status_code == 422
    assert local.calls == 0
    assert cloud.calls == 0
    assert redis.data == {}


@pytest.mark.asyncio
async def test_stream_true_returns_422() -> None:
    app, local, _cloud, _redis = _app(FakeProvider("local"), FakeProvider("cloud"))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "temperature": 0.0,
                "max_tokens": 8,
                "stream": True,
            },
        )
    assert response.status_code == 422
    assert local.calls == 0


@pytest.mark.asyncio
async def test_dual_provider_failure_returns_502_without_cache_write() -> None:
    app, local, cloud, redis = _app(
        FakeProvider("local", error=ProviderError("down", status_code=500)),
        FakeProvider("cloud", error=ProviderError("down", status_code=500)),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "temperature": 0.0,
                "max_tokens": 8,
            },
        )
    assert response.status_code == 502
    assert redis.data == {}
