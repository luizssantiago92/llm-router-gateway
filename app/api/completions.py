from __future__ import annotations

import secrets
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.providers.base import ProviderError
from app.quota.daily import QuotaExceededError
from app.schemas.chat import ChatCompletionRequest

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request) -> JSONResponse:
    settings = request.app.state.settings
    api_key = request.headers.get("x-api-key", "")
    expected = getattr(settings, "gateway_api_key", "") if settings is not None else ""
    if not expected or not api_key or not secrets.compare_digest(api_key, expected):
        return JSONResponse(
            {"error": {"message": "missing or invalid X-API-Key", "type": "unauthorized"}},
            status_code=401,
        )

    started = time.perf_counter()
    cache = request.app.state.cache
    gateway = request.app.state.router
    quota = request.app.state.quota
    messages = [message.model_dump() for message in body.messages]
    cached_value = await cache.get(messages, body.temperature, body.max_tokens)
    if cached_value is not None:
        latency_ms = (time.perf_counter() - started) * 1000
        return _completion_response(
            content=str(cached_value.get("content", "")),
            provider=str(cached_value.get("provider", "cache")),
            cached=True,
            latency_ms=latency_ms,
        )

    if quota is not None:
        try:
            await quota.consume(api_key)
        except QuotaExceededError as exc:
            return JSONResponse(
                {"error": {"message": str(exc), "type": "rate_limit_reached"}},
                status_code=429,
            )

    try:
        completion = await gateway.complete(messages, body.temperature, body.max_tokens)
    except ProviderError as exc:
        if quota is not None:
            await quota.refund(api_key)
        return JSONResponse(
            {"error": {"message": str(exc), "type": "upstream_error"}},
            status_code=502,
        )
    await cache.store(
        messages,
        body.temperature,
        body.max_tokens,
        {"content": completion.content, "provider": completion.provider, "model": completion.model},
    )
    latency_ms = (time.perf_counter() - started) * 1000
    return _completion_response(
        content=completion.content,
        provider=completion.provider,
        cached=False,
        latency_ms=latency_ms,
    )


def _completion_response(
    *,
    content: str,
    provider: str,
    cached: bool,
    latency_ms: float,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "id": "chatcmpl-gateway",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "cached": cached,
        "latency_ms": latency_ms,
        "provider": provider,
    }
    headers = {
        "X-Cache": "true" if cached else "false",
        "X-Latency-Ms": str(latency_ms),
        "X-Provider": provider,
    }
    return JSONResponse(payload, headers=headers)
