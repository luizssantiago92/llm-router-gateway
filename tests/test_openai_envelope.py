"""OpenAI-shaped chat responses and one error envelope."""

from __future__ import annotations

import json
import time

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import __version__
from app.api.completions import rounded_latency_ms
from app.cache.service import CacheService
from app.main import create_app
from app.providers.base import TokenUsage
from app.providers.fake import FakeProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import MAX_BODY_BYTES, Settings

API_KEY = "gateway-test"
HEADERS = {"X-API-Key": API_KEY}
SUBMITTED = "client-text-should-not-echo"


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


def _app(local: FakeProvider | None = None) -> tuple[FastAPI, FakeProvider]:
    provider = local or FakeProvider("local", content="hello", model="fake-model")
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
    redis = _Redis()
    app = create_app(
        settings=settings,
        cache=CacheService(redis, settings.cache_ttl_seconds),
        router=Router(provider, FakeProvider("cloud"), word_threshold=150),
        redis=redis,
        local=provider,
        cloud=FakeProvider("cloud"),
        quota=DailyQuota(redis, settings.chat_daily_limit),
    )
    return app, provider


def _payload() -> dict[str, object]:
    return {"messages": [{"role": "user", "content": "hi"}]}


def test_rounded_latency_is_whole_milliseconds() -> None:
    assert rounded_latency_ms(0.5) == 500
    assert isinstance(rounded_latency_ms(0.001), int)


@pytest.mark.asyncio
async def test_responses_have_unique_ids_created_model_and_null_usage() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
        second = await client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert first.status_code == 200
    assert second.status_code == 200
    body = first.json()
    again = second.json()
    assert body["id"].startswith("chatcmpl-")
    assert again["id"].startswith("chatcmpl-")
    assert body["id"] != again["id"]
    assert isinstance(body["created"], int)
    assert abs(body["created"] - int(time.time())) < 5
    assert body["model"] == "fake-model"
    assert again["model"] == "fake-model"
    assert body["usage"] == {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
    }
    assert isinstance(body["latency_ms"], int)
    assert not isinstance(body["latency_ms"], bool)
    assert first.headers["x-latency-ms"] == str(body["latency_ms"])
    assert again["cached"] is True
    assert local.calls == 1


@pytest.mark.asyncio
async def test_reported_usage_is_returned_and_replayed_from_cache() -> None:
    app, local = _app(
        FakeProvider(
            "local",
            content="hello",
            model="fake-model",
            usage=TokenUsage(prompt_tokens=2, completion_tokens=5, total_tokens=7),
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
        second = await client.post("/v1/chat/completions", headers=HEADERS, json=_payload())
    assert first.json()["usage"] == {
        "prompt_tokens": 2,
        "completion_tokens": 5,
        "total_tokens": 7,
    }
    assert second.json()["usage"] == first.json()["usage"]
    assert second.json()["id"] != first.json()["id"]
    assert local.calls == 1


@pytest.mark.asyncio
async def test_validation_error_omits_the_submitted_text() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": [{"role": "hacker", "content": SUBMITTED}]},
        )
        invalid = await client.post(
            "/v1/chat/completions",
            headers={**HEADERS, "content-type": "application/json"},
            content=b'{"messages": "' + SUBMITTED.encode() + b'"}',
        )
    assert response.status_code == 422
    assert invalid.status_code == 422
    error = response.json()["error"]
    assert error["type"] == "invalid_request_error"
    assert error["code"] == "validation_error"
    assert error["param"] == "messages.0.role"
    assert SUBMITTED not in response.text
    assert SUBMITTED not in invalid.text
    assert "input" not in error
    assert local.calls == 0


@pytest.mark.asyncio
async def test_unknown_path_uses_the_error_envelope() -> None:
    app, _local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/missing")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["message"] == "Not Found"
    assert error["type"] == "not_found"
    assert error["param"] is None
    assert "detail" not in response.json()


@pytest.mark.asyncio
async def test_root_redirects_to_docs() -> None:
    app, _local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_schema_lists_the_response_model_error_responses_and_version() -> None:
    schema = create_app().openapi()
    info = schema["info"]
    assert info["version"] == __version__
    assert info["title"] == "LLM Router Gateway"
    assert "null" in info["description"]
    post = schema["paths"]["/v1/chat/completions"]["post"]
    for status in ("200", "401", "413", "422", "429", "502"):
        assert status in post["responses"]
    ok = _deref(schema, post["responses"]["200"])
    assert {"id", "created", "model", "usage"} <= set(ok["properties"])
    usage = _deref(schema, ok["properties"]["usage"])
    assert {"prompt_tokens", "completion_tokens", "total_tokens"} <= set(usage["properties"])
    error = _deref(schema, post["responses"]["422"])
    assert "error" in error["properties"]
    assert "/" not in schema["paths"]


@pytest.mark.asyncio
async def test_missing_credential_still_skips_the_body_and_oversize_stays_413() -> None:
    app, local = _app()
    status, payload, read = await _asgi(
        app,
        headers=[(b"content-length", str(MAX_BODY_BYTES + 1).encode())],
        body=b"x" * 8,
        allow_read=False,
    )
    assert status == 401
    assert payload["error"]["type"] == "unauthorized"
    assert read is False
    allowed = await _asgi(
        app,
        headers=[
            (b"x-api-key", API_KEY.encode()),
            (b"content-type", b"application/json"),
            (b"content-length", str(MAX_BODY_BYTES + 1).encode()),
        ],
        body=json.dumps(_payload()).encode(),
        allow_read=True,
    )
    assert allowed[0] == 413
    assert allowed[1]["error"]["type"] == "payload_too_large"
    assert local.calls == 0


def _deref(schema: dict[str, object], node: object) -> dict[str, object]:
    current = node
    assert isinstance(current, dict)
    if "content" in current:
        media = current["content"]
        assert isinstance(media, dict)
        json_body = media["application/json"]
        assert isinstance(json_body, dict)
        current = json_body["schema"]
        assert isinstance(current, dict)
    if "$ref" in current:
        ref = current["$ref"]
        assert isinstance(ref, str)
        components = schema["components"]
        assert isinstance(components, dict)
        models = components["schemas"]
        assert isinstance(models, dict)
        resolved = models[ref.rsplit("/", 1)[-1]]
        assert isinstance(resolved, dict)
        return resolved
    return current


async def _asgi(
    app: FastAPI,
    *,
    headers: list[tuple[bytes, bytes]],
    body: bytes,
    allow_read: bool,
) -> tuple[int, dict[str, object], bool]:
    read = False
    sent = False

    async def receive() -> dict[str, object]:
        nonlocal read, sent
        read = True
        if not allow_read:
            raise AssertionError("body was read")
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
        raw = message["body"]
        assert isinstance(raw, bytes)
        chunks.append(raw)
    parsed = json.loads(b"".join(chunks))
    assert isinstance(status, int)
    assert isinstance(parsed, dict)
    return status, parsed, read
