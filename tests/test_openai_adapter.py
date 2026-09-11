import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.openai import OpenAIProvider


def _transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_openai_adapter_maps_chat_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer sk-test"
        return httpx.Response(
            200,
            json={
                "model": "gpt-4o-mini",
                "choices": [{"message": {"role": "assistant", "content": "pong"}}],
            },
        )

    async with httpx.AsyncClient(
        transport=_transport(handler), base_url="https://api.openai.com/v1"
    ) as client:
        provider = OpenAIProvider("sk-test", client=client)
        result = await provider.complete(
            [{"role": "user", "content": "ping"}],
            temperature=0.0,
            max_tokens=8,
        )
    assert result.content == "pong"
    assert result.provider == "cloud"


@pytest.mark.asyncio
async def test_openai_adapter_maps_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow")

    async with httpx.AsyncClient(
        transport=_transport(handler), base_url="https://api.openai.com/v1"
    ) as client:
        provider = OpenAIProvider("sk-test", client=client)
        with pytest.raises(ProviderError) as exc:
            await provider.complete([{"role": "user", "content": "x"}], 0.0, 1)
    assert exc.value.timed_out is True
