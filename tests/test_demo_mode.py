"""PROVIDER_MODE=demo: in-process providers, cache, and the compose file."""

from pathlib import Path

import pytest
import yaml
from httpx import ASGITransport, AsyncClient

from app.cache.service import CacheService
from app.main import create_app
from app.providers.base import ProviderError
from app.providers.demo import (
    CLOUD_FAILURE_MARK,
    DEMO_LATENCY_SECONDS,
    LOCAL_FAILURE_MARK,
    DemoProvider,
)
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.runtime import build_runtime
from app.settings import DEMO_GATEWAY_API_KEY, Settings

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"X-API-Key": DEMO_GATEWAY_API_KEY}


class MemoryRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        del ex
        self.data[key] = value
        return True

    async def incr(self, key: str) -> int:
        value = int(self.data.get(key, "0")) + 1
        self.data[key] = str(value)
        return value

    async def decr(self, key: str) -> int:
        value = int(self.data.get(key, "0")) - 1
        self.data[key] = str(value)
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        del key, seconds
        return True

    async def ping(self) -> bool:
        return True


def _demo_settings() -> Settings:
    return Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://127.0.0.1:11434",
        gemini_api_key="",
        gateway_api_key=DEMO_GATEWAY_API_KEY,
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
        provider_mode="demo",
    )


def _app(redis: MemoryRedis):
    settings = _demo_settings()
    local = DemoProvider("local")
    cloud = DemoProvider("cloud")
    return create_app(
        settings=settings,
        cache=CacheService(redis, settings.cache_ttl_seconds),
        router=Router(local, cloud, word_threshold=150),
        redis=redis,
        local=local,
        cloud=cloud,
        quota=DailyQuota(redis, settings.chat_daily_limit),
    )


def _body(content: str) -> dict[str, object]:
    return {
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "max_tokens": 16,
    }


@pytest.mark.asyncio
async def test_simple_local_failure_returns_a_cloud_echo() -> None:
    app = _app(MemoryRedis())
    prompt = f"hello {LOCAL_FAILURE_MARK}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=_body(prompt))
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "cloud"
    assert body["choices"][0]["message"]["content"] == prompt
    assert body["cached"] is False
    assert response.headers["X-Provider"] == "cloud"


@pytest.mark.asyncio
async def test_repeated_demo_prompt_returns_a_cache_hit() -> None:
    app = _app(MemoryRedis())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/v1/chat/completions", headers=HEADERS, json=_body("hello"))
        second = await client.post("/v1/chat/completions", headers=HEADERS, json=_body("hello"))
    assert first.status_code == 200
    assert first.json()["cached"] is False
    assert first.json()["provider"] == "local"
    assert first.json()["choices"][0]["message"]["content"] == "hello"
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert second.json()["provider"] == "local"
    assert second.headers["X-Cache"] == "true"


@pytest.mark.asyncio
async def test_cloud_failure_on_a_complex_prompt_returns_the_local_echo() -> None:
    app = _app(MemoryRedis())
    prompt = f"please implement this {CLOUD_FAILURE_MARK}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=_body(prompt))
    assert response.status_code == 200
    assert response.json()["provider"] == "local"
    assert response.json()["choices"][0]["message"]["content"] == prompt


@pytest.mark.asyncio
async def test_both_demo_failures_return_upstream_error() -> None:
    app = _app(MemoryRedis())
    prompt = f"hi {LOCAL_FAILURE_MARK} {CLOUD_FAILURE_MARK}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=_body(prompt))
    assert response.status_code == 502
    assert response.json()["error"]["type"] == "upstream_error"


@pytest.mark.asyncio
async def test_demo_delay_is_awaited(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[float] = []

    async def _sleep(seconds: float) -> None:
        seen.append(seconds)

    monkeypatch.setattr("app.providers.demo.asyncio.sleep", _sleep)
    provider = DemoProvider("cloud", delay_seconds=DEMO_LATENCY_SECONDS)
    completion = await provider.complete(
        [{"role": "user", "content": "hi"}],
        None,
        None,
    )
    assert seen == [DEMO_LATENCY_SECONDS]
    assert completion.model == "demo-cloud"
    assert completion.usage is not None
    assert completion.usage.total_tokens == 2


@pytest.mark.asyncio
async def test_demo_provider_health_returns_true() -> None:
    assert await DemoProvider("local").health() is True


@pytest.mark.asyncio
async def test_empty_messages_echo_an_empty_string() -> None:
    completion = await DemoProvider("local").complete([], None, None)
    assert completion.content == ""


@pytest.mark.asyncio
async def test_non_user_message_is_echoed() -> None:
    provider = DemoProvider("local")
    completion = await provider.complete([{"role": "assistant", "content": "prior"}], None, None)
    assert completion.content == "prior"


def test_unknown_provider_mode_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="PROVIDER_MODE"):
        Settings(
            redis_url="redis://localhost:6379/0",
            ollama_base_url="http://ollama",
            gemini_api_key="gemini",
            gateway_api_key="gateway",
            cache_ttl_seconds=60,
            complexity_word_threshold=150,
            upstream_timeout_seconds=30,
            provider_mode="other",
        )


@pytest.mark.asyncio
async def test_demo_runtime_uses_demo_providers() -> None:
    runtime = build_runtime(_demo_settings())
    try:
        assert isinstance(runtime.local, DemoProvider)
        assert isinstance(runtime.cloud, DemoProvider)
        assert runtime.local.delay_seconds == DEMO_LATENCY_SECONDS
    finally:
        await runtime.aclose()


@pytest.mark.asyncio
async def test_live_runtime_keeps_upstream_providers() -> None:
    settings = Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        gemini_api_key="gemini-test",
        gateway_api_key="gateway-test",
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
        provider_mode="live",
    )
    runtime = build_runtime(settings)
    try:
        assert isinstance(runtime.local, OllamaProvider)
        assert isinstance(runtime.cloud, GeminiProvider)
    finally:
        await runtime.aclose()


@pytest.mark.asyncio
async def test_local_failure_token_is_retryable() -> None:
    provider = DemoProvider("local")
    with pytest.raises(ProviderError) as exc:
        await provider.complete(
            [{"role": "user", "content": LOCAL_FAILURE_MARK}],
            None,
            None,
        )
    assert exc.value.is_retryable is True


def test_demo_compose_file_needs_no_host_keys() -> None:
    text = (ROOT / "compose.demo.yml").read_text(encoding="utf-8")
    assert "${" not in text
    compose = yaml.safe_load(text)
    env = compose["services"]["api"]["environment"]
    assert env["PROVIDER_MODE"] == "demo"
    assert env["GATEWAY_API_KEY"] == DEMO_GATEWAY_API_KEY
    assert "GEMINI_API_KEY" not in env
    api = compose["services"]["api"]
    redis = compose["services"]["redis"]
    assert api["ports"] == ["127.0.0.1:8000:8000"]
    assert api["restart"] == "unless-stopped"
    assert api["depends_on"]["redis"]["condition"] == "service_healthy"
    assert "/health/live" in str(api["healthcheck"]["test"])
    command = redis["command"]
    assert "demo-redis" in command
    assert redis["ports"] == ["127.0.0.1:6379:6379"]
    assert str(redis["image"]).startswith("redis:7-alpine@sha256:")
    assert redis["restart"] == "unless-stopped"


def test_demo_script_lists_the_curl_sequence() -> None:
    script = ROOT / "scripts" / "demo.sh"
    text = script.read_text(encoding="utf-8")
    assert LOCAL_FAILURE_MARK in text
    assert DEMO_GATEWAY_API_KEY in text
    assert "compose.demo.yml" in text
    assert text.startswith("#!/bin/sh\n")
