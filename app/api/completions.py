from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.deps import CacheDep, QuotaDep, RouterDep
from app.providers.base import ProviderError
from app.quota.daily import QuotaExceededError
from app.schemas.chat import ChatCompletionRequest
from app.security import AuthFirstRoute, GatewayKeyDep

router = APIRouter(route_class=AuthFirstRoute)


@router.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    api_key: GatewayKeyDep,
    cache: CacheDep,
    gateway: RouterDep,
    quota: QuotaDep,
) -> JSONResponse:
    started = time.perf_counter()
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
