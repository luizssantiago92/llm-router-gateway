import json

import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.gemini import GeminiProvider


def _transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_gemini_adapter_maps_generate_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/models/gemini-3.5-flash:generateContent")
        assert request.headers["x-goog-api-key"] == "gemini-test"
        assert "key" not in request.url.params
        return httpx.Response(
            200,
            json={
                "modelVersion": "gemini-3.5-flash",
                "candidates": [{"content": {"parts": [{"text": "pong"}]}}],
            },
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        result = await provider.complete(
            [{"role": "user", "content": "ping"}],
            temperature=0.0,
            max_tokens=8,
        )
    assert result.content == "pong"
    assert result.provider == "cloud"
    assert result.usage is None


@pytest.mark.asyncio
async def test_gemini_adapter_copies_reported_usage_and_does_not_fill_gaps() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "modelVersion": "gemini-3.5-flash",
                "candidates": [{"content": {"parts": [{"text": "pong"}]}}],
                "usageMetadata": {"promptTokenCount": 3, "totalTokenCount": 9},
            },
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        result = await provider.complete([{"role": "user", "content": "ping"}], 0.0, 8)
    assert result.usage is not None
    assert result.usage.prompt_tokens == 3
    assert result.usage.completion_tokens is None
    assert result.usage.total_tokens == 9


@pytest.mark.asyncio
async def test_gemini_adapter_maps_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow")

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        with pytest.raises(ProviderError) as exc:
            await provider.complete([{"role": "user", "content": "x"}], 0.0, 1)
    assert exc.value.timed_out is True


def _body(request: httpx.Request) -> dict[str, object]:
    loaded = json.loads(request.content)
    assert isinstance(loaded, dict)
    return loaded


@pytest.mark.asyncio
async def test_omitted_temperature_is_absent_from_generation_config() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["config"] = _body(request).get("generationConfig")
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "pong"}]}}]},
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        await provider.complete(
            [{"role": "user", "content": "ping"}],
            temperature=None,
            max_tokens=8,
        )
    assert seen["config"] == {"maxOutputTokens": 8}


@pytest.mark.asyncio
async def test_explicit_zero_temperature_is_sent() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["config"] = _body(request).get("generationConfig")
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "pong"}]}}]},
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        await provider.complete([{"role": "user", "content": "ping"}], 0.0, None)
    assert isinstance(seen["config"], dict)
    assert seen["config"]["temperature"] == 0.0


@pytest.mark.asyncio
async def test_top_p_is_copied_to_gemini_top_p() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["config"] = _body(request).get("generationConfig")
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "pong"}]}}]},
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        await provider.complete(
            [{"role": "user", "content": "ping"}],
            0.2,
            8,
            top_p=0.2,
        )
    assert isinstance(seen["config"], dict)
    assert seen["config"]["topP"] == 0.2


@pytest.mark.asyncio
async def test_gemini_model_name_is_used_in_the_request_url() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "pong"}]}}]},
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        await provider.complete(
            [{"role": "user", "content": "ping"}],
            0.0,
            8,
            model="gemini-2.5-pro",
        )
    assert seen["path"].endswith("/models/gemini-2.5-pro:generateContent")


@pytest.mark.asyncio
async def test_non_gemini_model_name_keeps_the_configured_model() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "pong"}]}}]},
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        await provider.complete(
            [{"role": "user", "content": "ping"}],
            0.0,
            8,
            model="gpt-4o",
        )
    assert seen["path"].endswith("/models/gemini-3.5-flash:generateContent")


@pytest.mark.asyncio
async def test_max_tokens_finish_reason_maps_to_length() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {"parts": [{"text": "pong"}]},
                        "finishReason": "MAX_TOKENS",
                    }
                ]
            },
        )

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        result = await provider.complete([{"role": "user", "content": "ping"}], 0.0, 8)
    assert result.finish_reason == "length"


@pytest.mark.asyncio
async def test_blocked_prompt_without_text_is_not_retryable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    async with httpx.AsyncClient(
        transport=_transport(handler),
        base_url="https://generativelanguage.googleapis.com/v1beta",
    ) as client:
        provider = GeminiProvider("gemini-test", client=client)
        with pytest.raises(ProviderError) as exc:
            await provider.complete([{"role": "user", "content": "ping"}], 0.0, 8)
    assert exc.value.status_code == 400
    assert exc.value.is_retryable is False
