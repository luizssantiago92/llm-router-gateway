import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.gemini import GeminiProvider


def _transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_gemini_adapter_maps_generate_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/models/gemini-2.0-flash:generateContent")
        assert request.url.params.get("key") == "gemini-test"
        return httpx.Response(
            200,
            json={
                "modelVersion": "gemini-2.0-flash",
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
