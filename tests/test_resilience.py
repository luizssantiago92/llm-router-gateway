"""Redis failure policy and the HTTP result of provider failover."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.cache.service import CacheService
from app.main import create_app
from app.providers.base import ProviderError
from app.providers.fake import FakeProvider
from app.quota.daily import DailyQuota, QuotaExceededError, QuotaUnavailableError
from app.routing.router import Router
from app.settings import Settings

API_KEY = "gateway-test"
HEADERS = {"X-API-Key": API_KEY}
BODY = {
    "messages": [{"role": "user", "content": "hi"}],
    "temperature": 0.0,
    "max_tokens": 8,
}


class FlakyRedis:
    def __init__(
        self,
        *,
        fail_get: bool = False,
        fail_set: bool = False,
        fail_incr: bool = False,
        fail_decr: bool = False,
    ) -> None:
        self.data: dict[str, str] = {}
        self.fail_get = fail_get
        self.fail_set = fail_set
        self.fail_incr = fail_incr
        self.fail_decr = fail_decr

    async def get(self, key: str) -> str | None:
        if self.fail_get:
            raise ConnectionError("redis down")
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        if self.fail_set:
            raise ConnectionError("redis down")
        self.data[key] = value

    async def incr(self, key: str) -> int:
        if self.fail_incr:
            raise ConnectionError("redis down")
        value = int(self.data.get(key, "0")) + 1
        self.data[key] = str(value)
        return value

    async def decr(self, key: str) -> int:
        if self.fail_decr:
            raise ConnectionError("redis down")
        value = int(self.data.get(key, "0")) - 1
        self.data[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> None:
        return None

    async def ping(self) -> bool:
        return True


def _app(
    local: FakeProvider,
    cloud: FakeProvider,
    redis: FlakyRedis,
):
    settings = Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        gemini_api_key="gemini-test",
        gateway_api_key=API_KEY,
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
        chat_daily_limit=5,
    )
    app = create_app(
        settings=settings,
        cache=CacheService(redis, settings.cache_ttl_seconds),
        router=Router(local, cloud, word_threshold=150),
        redis=redis,
        local=local,
        cloud=cloud,
        quota=DailyQuota(redis, settings.chat_daily_limit),
    )
    return app


async def _post(app, local: FakeProvider, cloud: FakeProvider):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=BODY)
    return response, local, cloud


@pytest.mark.asyncio
async def test_redis_read_failure_returns_the_upstream_completion() -> None:
    local = FakeProvider("local", content="from-local")
    cloud = FakeProvider("cloud")
    response, local, cloud = await _post(
        _app(local, cloud, FlakyRedis(fail_get=True)),
        local,
        cloud,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["message"]["content"] == "from-local"
    assert body["cached"] is False
    assert local.calls == 1


@pytest.mark.asyncio
async def test_redis_write_failure_still_returns_http_200() -> None:
    local = FakeProvider("local", content="from-local")
    cloud = FakeProvider("cloud")
    response, local, _cloud = await _post(
        _app(local, cloud, FlakyRedis(fail_set=True)),
        local,
        cloud,
    )
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "from-local"
    assert local.calls == 1


@pytest.mark.asyncio
async def test_quota_redis_failure_returns_503_without_a_provider_call() -> None:
    local = FakeProvider("local", content="from-local")
    cloud = FakeProvider("cloud")
    response, local, cloud = await _post(
        _app(local, cloud, FlakyRedis(fail_incr=True)),
        local,
        cloud,
    )
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["type"] == "service_unavailable"
    assert error["code"] == "quota_unavailable"
    assert error["message"] == "quota store unavailable"
    assert "redis down" not in response.text
    assert local.calls == 0
    assert cloud.calls == 0


@pytest.mark.asyncio
async def test_non_retryable_primary_returns_502_without_the_secondary() -> None:
    local = FakeProvider("local", error=ProviderError("bad request", status_code=400))
    cloud = FakeProvider("cloud", content="should-not-run")
    response, local, cloud = await _post(_app(local, cloud, FlakyRedis()), local, cloud)
    assert response.status_code == 502
    assert response.json()["error"]["type"] == "upstream_error"
    assert local.calls == 1
    assert cloud.calls == 0


def test_quota_bucket_hides_the_caller_credential() -> None:
    quota = DailyQuota(FlakyRedis(), 5)
    key = quota._bucket_key(API_KEY)
    assert API_KEY not in key
    assert key.startswith("quota:")
    assert quota._bucket_key(API_KEY) == key


@pytest.mark.asyncio
async def test_expire_failure_refuses_the_request() -> None:
    class _ExpireDown(FlakyRedis):
        async def expire(self, key: str, seconds: int) -> None:
            raise ConnectionError("redis down")

    quota = DailyQuota(_ExpireDown(), 5)
    with pytest.raises(QuotaUnavailableError):
        await quota.consume(API_KEY)


@pytest.mark.asyncio
async def test_over_limit_decr_failure_still_rejects() -> None:
    quota = DailyQuota(FlakyRedis(fail_decr=True), 1)
    await quota.consume(API_KEY)
    with pytest.raises(QuotaExceededError):
        await quota.consume(API_KEY)


@pytest.mark.asyncio
async def test_refund_ignores_a_missing_or_invalid_counter() -> None:
    redis = FlakyRedis()
    quota = DailyQuota(redis, 5)
    await quota.refund(API_KEY)
    redis.data[quota._bucket_key(API_KEY)] = "nope"
    await quota.refund(API_KEY)
    redis.data[quota._bucket_key(API_KEY)] = "0"
    await quota.refund(API_KEY)


@pytest.mark.asyncio
async def test_refund_failure_still_returns_502() -> None:
    local = FakeProvider("local", error=ProviderError("down", status_code=500))
    cloud = FakeProvider("cloud", error=ProviderError("down", status_code=500))
    response, local, cloud = await _post(
        _app(local, cloud, FlakyRedis(fail_decr=True)),
        local,
        cloud,
    )
    assert response.status_code == 502
    assert local.calls == 1
    assert cloud.calls == 1
