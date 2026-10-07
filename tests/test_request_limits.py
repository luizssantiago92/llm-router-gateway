"""Chat field bounds and the post-auth body size cap."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.cache.service import CacheService
from app.main import create_app
from app.providers.fake import FakeProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.schemas.chat import ChatCompletionRequest
from app.settings import MAX_BODY_BYTES, MAX_MESSAGE_CHARS, MAX_MESSAGES, Settings

API_KEY = "gateway-test"
HEADERS = {"X-API-Key": API_KEY}


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


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "redis_url": "redis://localhost:6379/0",
        "ollama_base_url": "http://ollama",
        "gemini_api_key": "gemini-test",
        "gateway_api_key": API_KEY,
        "cache_ttl_seconds": 60,
        "complexity_word_threshold": 150,
        "upstream_timeout_seconds": 30,
        "chat_daily_limit": 5,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _app(**overrides: object) -> tuple[FastAPI, FakeProvider]:
    settings = _settings(**overrides)
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
    return app, local


def _messages(content: str, count: int = 1, role: str = "user") -> list[dict[str, str]]:
    return [{"role": role, "content": content} for _ in range(count)]


@pytest.mark.parametrize(
    ("payload", "accepted"),
    [
        ({"messages": []}, False),
        ({"messages": _messages("hi", role="hacker")}, False),
        ({"messages": _messages("hi", role="system")}, True),
        ({"messages": _messages("hi", role="user")}, True),
        ({"messages": _messages("hi", role="assistant")}, True),
        ({"messages": _messages("")}, False),
        ({"messages": _messages("a")}, True),
        ({"messages": _messages("a" * MAX_MESSAGE_CHARS)}, True),
        ({"messages": _messages("a" * (MAX_MESSAGE_CHARS + 1))}, False),
        ({"messages": _messages("a", MAX_MESSAGES)}, True),
        ({"messages": _messages("a", MAX_MESSAGES + 1)}, False),
        ({"messages": _messages("a" * MAX_MESSAGE_CHARS, 2)}, True),
        ({"messages": [*_messages("a" * MAX_MESSAGE_CHARS, 2), *_messages("a")]}, False),
        ({"messages": _messages("hi"), "temperature": 0}, True),
        ({"messages": _messages("hi"), "temperature": 2}, True),
        ({"messages": _messages("hi"), "temperature": -5}, False),
        ({"messages": _messages("hi"), "temperature": 2.1}, False),
        ({"messages": _messages("hi"), "max_tokens": 1}, True),
        ({"messages": _messages("hi"), "max_tokens": 4096}, True),
        ({"messages": _messages("hi"), "max_tokens": -1}, False),
        ({"messages": _messages("hi"), "max_tokens": 0}, False),
        ({"messages": _messages("hi"), "max_tokens": 4097}, False),
    ],
)
def test_field_bounds(payload: dict[str, object], accepted: bool) -> None:
    if accepted:
        ChatCompletionRequest.model_validate(payload)
        return
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(payload)


def test_omitted_temperature_and_max_tokens_stay_unset() -> None:
    body = ChatCompletionRequest.model_validate({"messages": _messages("hi")})
    assert body.temperature is None
    assert body.max_tokens is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "status"),
    [
        ({"messages": []}, 422),
        ({"messages": _messages("hi", role="hacker")}, 422),
        ({"messages": _messages("a" * (MAX_MESSAGE_CHARS + 1))}, 422),
        ({"messages": _messages("a", MAX_MESSAGES + 1)}, 422),
        ({"messages": [*_messages("a" * MAX_MESSAGE_CHARS, 2), *_messages("b")]}, 422),
        ({"messages": _messages("hi"), "temperature": -5}, 422),
        ({"messages": _messages("hi"), "max_tokens": -1}, 422),
        ({"messages": _messages("a" * MAX_MESSAGE_CHARS)}, 200),
        ({"messages": _messages("a", MAX_MESSAGES)}, 200),
        ({"messages": _messages("a" * MAX_MESSAGE_CHARS, 2)}, 200),
        ({"messages": _messages("hi"), "temperature": 0}, 200),
        ({"messages": _messages("hi"), "temperature": 2}, 200),
        ({"messages": _messages("hi"), "max_tokens": 1}, 200),
        ({"messages": _messages("hi"), "max_tokens": 4096}, 200),
    ],
)
async def test_http_bounds(payload: dict[str, object], status: int) -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=payload)
    assert response.status_code == status
    if status == 422:
        assert local.calls == 0


@pytest.mark.asyncio
async def test_omitted_temperature_is_sent_as_the_provider_default() -> None:
    app, local = _app()
    transport = ASGITransport(app=app)
    messages = _messages("hi")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": messages},
        )
        second = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": messages, "temperature": 1.0},
        )
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert local.calls == 1


@pytest.mark.asyncio
async def test_tighter_message_setting_rejects_before_the_builtin_ceiling() -> None:
    app, local = _app(max_message_chars=3)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        accepted = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": _messages("abc")},
        )
        rejected = await client.post(
            "/v1/chat/completions",
            headers=HEADERS,
            json={"messages": _messages("abcd")},
        )
    assert accepted.status_code == 200
    assert rejected.status_code == 422
    assert local.calls == 1


@pytest.mark.asyncio
async def test_content_length_over_the_cap_is_413_and_the_cap_itself_is_allowed() -> None:
    app, local = _app()
    body = json.dumps({"messages": _messages("hi")}).encode()
    allowed = await _asgi(
        app,
        headers=_key_headers(content_length=MAX_BODY_BYTES),
        body=body,
    )
    rejected = await _asgi(
        app,
        headers=_key_headers(content_length=MAX_BODY_BYTES + 1),
        body=body,
    )
    assert allowed[0] == 200
    assert rejected[0] == 413
    error = rejected[1]["error"]
    assert isinstance(error, dict)
    assert error["type"] == "payload_too_large"
    assert local.calls == 1


@pytest.mark.asyncio
async def test_chunked_body_over_the_cap_is_413_and_the_cap_itself_is_not() -> None:
    app, _local = _app()
    at_cap = await _asgi(app, headers=_key_headers(), body=b"x" * MAX_BODY_BYTES)
    over = await _asgi(app, headers=_key_headers(), body=b"x" * (MAX_BODY_BYTES + 1))
    assert at_cap[0] == 422
    assert over[0] == 413


@pytest.mark.asyncio
async def test_missing_credential_on_an_oversized_body_is_401_before_the_body_is_read() -> None:
    app, local = _app()
    status, payload = await _asgi(
        app,
        headers=[(b"content-length", str(MAX_BODY_BYTES + 1).encode())],
        body=b"x" * (MAX_BODY_BYTES + 1),
        read_body=False,
    )
    assert status == 401
    error = payload["error"]
    assert isinstance(error, dict)
    assert error["type"] == "unauthorized"
    assert local.calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "payload", "status"),
    [
        ({"max_messages": 1}, {"messages": _messages("a", 1)}, 200),
        ({"max_messages": 1}, {"messages": _messages("a", 2)}, 422),
        ({"max_total_message_chars": 3}, {"messages": _messages("abc")}, 200),
        ({"max_total_message_chars": 3}, {"messages": _messages("abcd")}, 422),
        ({"max_temperature": 1}, {"messages": _messages("hi"), "temperature": 1}, 200),
        ({"max_temperature": 1}, {"messages": _messages("hi"), "temperature": 1.5}, 422),
        ({"max_max_tokens": 4}, {"messages": _messages("hi"), "max_tokens": 4}, 200),
        ({"max_max_tokens": 4}, {"messages": _messages("hi"), "max_tokens": 5}, 422),
    ],
)
async def test_tighter_settings_apply_below_the_builtin_ceiling(
    overrides: dict[str, object],
    payload: dict[str, object],
    status: int,
) -> None:
    app, local = _app(**overrides)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/chat/completions", headers=HEADERS, json=payload)
    assert response.status_code == status
    if status == 422:
        assert local.calls == 0


@pytest.mark.asyncio
async def test_tighter_body_setting_rejects_a_small_json_body() -> None:
    body = json.dumps({"messages": _messages("hi")}, separators=(",", ":")).encode()
    headers = {**HEADERS, "content-type": "application/json"}
    allowed_app, allowed_local = _app(max_body_bytes=len(body))
    rejected_app, rejected_local = _app(max_body_bytes=len(body) - 1)
    async with AsyncClient(
        transport=ASGITransport(app=allowed_app),
        base_url="http://test",
    ) as client:
        allowed = await client.post("/v1/chat/completions", headers=headers, content=body)
    async with AsyncClient(
        transport=ASGITransport(app=rejected_app),
        base_url="http://test",
    ) as client:
        rejected = await client.post("/v1/chat/completions", headers=headers, content=body)
    assert allowed.status_code == 200
    assert rejected.status_code == 413
    assert allowed_local.calls == 1
    assert rejected_local.calls == 0


@pytest.mark.asyncio
async def test_unusable_content_length_is_measured_from_the_body() -> None:
    app, local = _app()
    body = json.dumps({"messages": _messages("hi")}).encode()
    status, _payload = await _asgi(
        app,
        headers=[*_key_headers(), (b"content-length", b"nope")],
        body=body,
    )
    assert status == 200
    assert local.calls == 1


def _key_headers(*, content_length: int | None = None) -> list[tuple[bytes, bytes]]:
    headers = [
        (b"x-api-key", API_KEY.encode()),
        (b"content-type", b"application/json"),
    ]
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode()))
    return headers


async def _asgi(
    app: FastAPI,
    *,
    headers: list[tuple[bytes, bytes]],
    body: bytes,
    read_body: bool = True,
) -> tuple[int, dict[str, object]]:
    sent = False

    async def receive() -> dict[str, object]:
        nonlocal sent
        if not read_body:
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
    return status, parsed
