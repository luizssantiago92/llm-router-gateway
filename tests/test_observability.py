import json
import logging
import re

import pytest
from httpx import ASGITransport, AsyncClient

from app.cache.service import CacheService
from app.main import create_app
from app.observability import resolve_request_id
from app.providers.fake import FakeProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import Settings

API_KEY = "gateway-test"
HEADERS = {"X-API-Key": API_KEY}
PROMPT = "prompt-token-qq7"
_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


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


def _app():
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
    redis = MemoryRedis()
    local = FakeProvider("local", content="hello")
    cloud = FakeProvider("cloud", content="cloud")
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


def _counter(body: str, *, method: str, path: str, status: str) -> int:
    needle = f'gateway_http_requests_total{{method="{method}",path="{path}",status="{status}"}} '
    for line in body.splitlines():
        if line.startswith(needle):
            return int(line.removeprefix(needle))
    return 0


def _access_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    lines = []
    for record in caplog.records:
        if record.name != "app.access":
            continue
        loaded = json.loads(record.getMessage())
        assert isinstance(loaded, dict)
        lines.append(loaded)
    return lines


def test_resolve_request_id_keeps_a_token_and_replaces_other_values() -> None:
    assert resolve_request_id("trace.1_ok") == "trace.1_ok"
    assert resolve_request_id("a" * 128) == "a" * 128
    replaced = resolve_request_id("bad id")
    assert replaced != "bad id"
    assert _REQUEST_ID.fullmatch(replaced)
    assert resolve_request_id("a" * 129) != "a" * 129
    assert resolve_request_id(None) != ""


@pytest.mark.asyncio
async def test_chat_response_returns_a_request_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.access")
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": [{"role": "user", "content": PROMPT}]},
        )
    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    assert _REQUEST_ID.fullmatch(request_id)
    lines = _access_lines(caplog)
    assert len(lines) == 1
    assert lines[0]["request_id"] == request_id
    assert lines[0]["status"] == 200
    assert lines[0]["path"] == "/v1/chat/completions"
    assert lines[0]["provider"] == "local"
    assert lines[0]["cached"] is False
    text = "\n".join(record.getMessage() for record in caplog.records)
    assert PROMPT not in text
    assert API_KEY not in text


@pytest.mark.asyncio
async def test_caller_supplied_request_id_is_returned() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Request-Id": "trace.1_ok"},
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "trace.1_ok"


@pytest.mark.asyncio
async def test_invalid_request_id_is_replaced() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "X-Request-Id": "bad id"},
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "bad id"
    assert _REQUEST_ID.fullmatch(response.headers["x-request-id"])


@pytest.mark.asyncio
async def test_metrics_counter_is_higher_after_a_chat_request() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        before = await client.get("/metrics")
        chat = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        after = await client.get("/metrics")
    assert before.status_code == 200
    assert chat.status_code == 200
    assert after.status_code == 200
    before_count = _counter(
        before.text,
        method="POST",
        path="/v1/chat/completions",
        status="200",
    )
    after_count = _counter(
        after.text,
        method="POST",
        path="/v1/chat/completions",
        status="200",
    )
    assert after_count > before_count
    assert "gateway_http_request_latency_ms_count{" in after.text
    assert PROMPT not in after.text
    assert API_KEY not in after.text


@pytest.mark.asyncio
async def test_unknown_path_is_counted_as_unmatched() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing = await client.get("/missing")
        body = (await client.get("/metrics")).text
    assert missing.status_code == 404
    assert _REQUEST_ID.fullmatch(missing.headers["x-request-id"])
    assert _counter(body, method="GET", path="unmatched", status="404") == 1


def test_metrics_route_does_not_require_a_credential() -> None:
    schema = create_app().openapi()
    operation = schema["paths"]["/metrics"]["get"]
    assert "security" not in operation
