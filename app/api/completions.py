from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.deps import CacheDep, QuotaDep, RouterDep, SettingsDep
from app.providers.base import ProviderError, TokenUsage
from app.quota.daily import QuotaExceededError
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorEnvelope,
    configured_limit_reason,
    error_payload,
)
from app.security import AuthFirstRoute, GatewayKeyDep

# Providers still receive a concrete temperature. Omitting the field keeps
# today's sampling input (1.0) without changing the Gemini adapter.
_OMITTED_TEMPERATURE = 1.0

router = APIRouter(route_class=AuthFirstRoute)


def _null_usage() -> dict[str, int | None]:
    return {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
    }


def rounded_latency_ms(elapsed_seconds: float) -> int:
    """Round a duration to a whole millisecond."""
    return round(elapsed_seconds * 1000)


def _usage_dict(usage: TokenUsage | None) -> dict[str, int | None]:
    if usage is None:
        return _null_usage()
    return usage.as_dict()


def _cached_usage(value: object) -> dict[str, int | None]:
    if not isinstance(value, dict):
        return _null_usage()
    return {
        "prompt_tokens": _cached_count(value.get("prompt_tokens")),
        "completion_tokens": _cached_count(value.get("completion_tokens")),
        "total_tokens": _cached_count(value.get("total_tokens")),
    }


def _cached_count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _cached_model(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


@router.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    responses={
        401: {"model": ErrorEnvelope},
        413: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
        502: {"model": ErrorEnvelope},
    },
)
async def chat_completions(
    body: ChatCompletionRequest,
    api_key: GatewayKeyDep,
    cache: CacheDep,
    gateway: RouterDep,
    quota: QuotaDep,
    settings: SettingsDep,
) -> JSONResponse:
    reason = configured_limit_reason(body, settings)
    if reason is not None:
        raise RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("body",),
                    "msg": reason,
                    "input": None,
                }
            ]
        )
    temperature = _OMITTED_TEMPERATURE if body.temperature is None else body.temperature
    started = time.perf_counter()
    messages = [message.model_dump() for message in body.messages]
    cached_value = await cache.get(messages, temperature, body.max_tokens)
    if cached_value is not None:
        return _completion_response(
            content=str(cached_value.get("content", "")),
            provider=str(cached_value.get("provider", "cache")),
            model=_cached_model(cached_value.get("model")),
            usage=_cached_usage(cached_value.get("usage")),
            cached=True,
            latency_ms=rounded_latency_ms(time.perf_counter() - started),
        )

    if quota is not None:
        try:
            await quota.consume(api_key)
        except QuotaExceededError as exc:
            return JSONResponse(
                error_payload(str(exc), "rate_limit_reached", code="rate_limit_reached"),
                status_code=429,
            )

    try:
        completion = await gateway.complete(messages, temperature, body.max_tokens)
    except ProviderError as exc:
        if quota is not None:
            await quota.refund(api_key)
        return JSONResponse(
            error_payload(str(exc), "upstream_error", code="upstream_error"),
            status_code=502,
        )
    usage = _usage_dict(completion.usage)
    await cache.store(
        messages,
        temperature,
        body.max_tokens,
        {
            "content": completion.content,
            "provider": completion.provider,
            "model": completion.model,
            "usage": usage,
        },
    )
    return _completion_response(
        content=completion.content,
        provider=completion.provider,
        model=completion.model,
        usage=usage,
        cached=False,
        latency_ms=rounded_latency_ms(time.perf_counter() - started),
    )


def _completion_response(
    *,
    content: str,
    provider: str,
    model: str | None,
    usage: dict[str, int | None],
    cached: bool,
    latency_ms: int,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "id": f"chatcmpl-{uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": usage,
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
