import pytest
from httpx import ASGITransport, AsyncClient

from app.cache.service import CacheService
from app.main import create_app
from app.providers.fake import FakeProvider
from app.routing.router import Router
from app.settings import Settings


class MemoryRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        return None

    async def ping(self) -> bool:
        if self.fail:
            raise ConnectionError("redis down")
        return True


def _client_app(redis, local, cloud):
    settings = Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        openai_api_key="sk-test",
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
    )
    cache = CacheService(redis, 60)
    router = Router(local, cloud)
    app = create_app(
        settings=settings,
        cache=cache,
        router=router,
        redis=redis,
        local=local,
        cloud=cloud,
    )
    return app


@pytest.mark.asyncio
async def test_health_ok_when_redis_and_upstreams_up() -> None:
    app = _client_app(MemoryRedis(), FakeProvider("local"), FakeProvider("cloud"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_degraded_when_upstream_down() -> None:
    app = _client_app(
        MemoryRedis(),
        FakeProvider("local", healthy=False),
        FakeProvider("cloud"),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_health_503_when_redis_down() -> None:
    app = _client_app(MemoryRedis(fail=True), FakeProvider("local"), FakeProvider("cloud"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 503
