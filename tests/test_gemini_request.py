import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.cache.service import CacheService
from app.main import create_app
from app.providers.fake import FakeProvider
from app.providers.gemini import GeminiProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.schemas.chat import ChatCompletionRequest
from app.settings import Settings

API_KEY = "gateway-test"
HEADERS = {"X-API-Key": API_KEY}
MARKER = "marker-z9-block"


class MemoryRedis:
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


def _settings() -> Settings:
    return Settings(
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://ollama",
        gemini_api_key="gemini-test",
        gateway_api_key=API_KEY,
        cache_ttl_seconds=60,
        complexity_word_threshold=150,
        upstream_timeout_seconds=30,
        chat_daily_limit=5,
    )


def _app(local: FakeProvider, cloud: GeminiProvider):
    settings = _settings()
    redis = MemoryRedis()
    return create_app(
        settings=settings,
        cache=CacheService(redis, settings.cache_ttl_seconds),
        router=Router(local, cloud, word_threshold=150),
        redis=redis,
        local=local,
        cloud=cloud,
        quota=DailyQuota(redis, settings.chat_daily_limit),
    )


@pytest.mark.asyncio
async def test_blocked_gemini_prompt_returns_502_without_the_secondary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    local = FakeProvider("local", content="should-not-run")
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as upstream:
        cloud = GeminiProvider("gemini-test", client=upstream)
        app = _app(local, cloud)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/chat/completions",
                headers=HEADERS,
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": f"please implement this algorithm {MARKER}",
                        }
                    ]
                },
            )
    assert response.status_code == 502
    body = response.json()
    assert body["error"]["type"] == "upstream_error"
    assert body["error"]["code"] == "upstream_error"
    assert MARKER not in response.text
    assert local.calls == 0


@pytest.mark.asyncio
async def test_max_tokens_finish_reason_is_length_on_the_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "modelVersion": "gemini-3.5-flash",
                "candidates": [
                    {
                        "content": {"parts": [{"text": "done"}]},
                        "finishReason": "MAX_TOKENS",
                    }
                ],
            },
        )

    local = FakeProvider("local", content="should-not-run")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as upstream:
        cloud = GeminiProvider("gemini-test", client=upstream)
        app = _app(local, cloud)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/v1/chat/completions",
                headers=HEADERS,
                json={
                    "messages": [{"role": "user", "content": "please implement this algorithm"}],
                    "max_tokens": 8,
                },
            )
    assert response.status_code == 200
    body = response.json()
    assert body["choices"][0]["finish_reason"] == "length"
    assert body["choices"][0]["message"]["content"] == "done"
    assert local.calls == 0


def test_stop_string_and_bounds() -> None:
    body = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "hi"}],
            "stop": "END",
            "top_p": 1,
            "model": "gemini-2.5-pro",
        }
    )
    assert body.stop == ["END"]
    assert body.top_p == 1
    assert body.model == "gemini-2.5-pro"
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "top_p": 1.1}
        )
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "stop": ""}
        )
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "stop": ["a"] * 6}
        )
