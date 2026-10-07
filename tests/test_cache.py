import hashlib
import json

import pytest

from app.cache.service import CacheService, cache_key


class MemoryRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value
        self.ttls[key] = ex


@pytest.mark.asyncio
async def test_cache_key_is_sha256_of_canonical_triple() -> None:
    messages = [{"role": "user", "content": "hi"}]
    key = cache_key(messages, 0.2, 32)
    payload = json.dumps(
        {"messages": messages, "max_tokens": 32, "temperature": 0.2},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    assert key == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert "gpt" not in key
    other = cache_key(messages, 0.3, 32)
    assert other != key
    assert cache_key(messages, 0.2, 32, top_p=None) == key
    assert cache_key(messages, 0.2, 32, top_p=0.5) != key
    assert cache_key(messages, 0.2, 32, stop=["END"]) != key
    assert cache_key(messages, 0.2, 32, model="gemini-2.5-pro") != key


@pytest.mark.asyncio
async def test_cache_get_returns_stored_completion() -> None:
    redis = MemoryRedis()
    cache = CacheService(redis, ttl_seconds=3600)
    messages = [{"role": "user", "content": "hi"}]
    await cache.store(messages, 0.0, 8, {"content": "pong", "provider": "local"})
    hit = await cache.get(messages, 0.0, 8)
    assert hit == {"content": "pong", "provider": "local"}
    assert redis.ttls[cache_key(messages, 0.0, 8)] == 3600


class _DownRedis(MemoryRedis):
    async def get(self, key: str) -> str | None:
        raise ConnectionError("redis down")

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis down")


@pytest.mark.asyncio
async def test_cache_read_failure_is_a_miss() -> None:
    cache = CacheService(_DownRedis(), ttl_seconds=60)
    assert await cache.get([{"role": "user", "content": "hi"}], 0.0, 8) is None


@pytest.mark.asyncio
async def test_cache_write_failure_does_not_raise() -> None:
    cache = CacheService(_DownRedis(), ttl_seconds=60)
    await cache.store(
        [{"role": "user", "content": "hi"}],
        0.0,
        8,
        {"content": "pong", "provider": "local"},
    )


@pytest.mark.asyncio
async def test_cached_non_object_json_is_a_miss() -> None:
    redis = MemoryRedis()
    cache = CacheService(redis, ttl_seconds=60)
    messages = [{"role": "user", "content": "hi"}]
    redis.data[cache_key(messages, 0.0, 8)] = "[1]"
    assert await cache.get(messages, 0.0, 8) is None


@pytest.mark.asyncio
async def test_invalid_cached_json_is_a_miss() -> None:
    redis = MemoryRedis()
    cache = CacheService(redis, ttl_seconds=60)
    messages = [{"role": "user", "content": "hi"}]
    redis.data[cache_key(messages, 0.0, 8)] = "not-json"
    assert await cache.get(messages, 0.0, 8) is None


@pytest.mark.asyncio
async def test_cache_does_not_store_error_payloads() -> None:
    redis = MemoryRedis()
    cache = CacheService(redis, ttl_seconds=60)
    messages = [{"role": "user", "content": "hi"}]
    await cache.store(messages, 0.0, 8, {"error": "nope"}, status_code=502)
    await cache.store(messages, 0.0, 8, {"error": "timeout"}, timed_out=True)
    await cache.store(messages, 0.0, 8, {"error": "bad"}, status_code=400)
    assert await cache.get(messages, 0.0, 8) is None
    assert redis.data == {}
