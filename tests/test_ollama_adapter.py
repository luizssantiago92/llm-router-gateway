import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.ollama import OllamaProvider


def _transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_ollama_adapter_maps_chat_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        assert b"hello" in request.content
        return httpx.Response(
            200,
            json={"model": "llama3", "message": {"role": "assistant", "content": "hi"}},
        )

    async with httpx.AsyncClient(transport=_transport(handler), base_url="http://ollama") as client:
        provider = OllamaProvider("http://ollama", client=client)
        result = await provider.complete(
            [{"role": "user", "content": "hello"}],
            temperature=0.1,
            max_tokens=16,
        )
    assert result.content == "hi"
    assert result.provider == "local"
    assert result.model == "llama3"


@pytest.mark.asyncio
async def test_ollama_adapter_maps_5xx_to_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "down"})

    async with httpx.AsyncClient(transport=_transport(handler), base_url="http://ollama") as client:
        provider = OllamaProvider("http://ollama", client=client)
        with pytest.raises(ProviderError) as exc:
            await provider.complete([{"role": "user", "content": "x"}], 0.0, 1)
    assert exc.value.status_code == 503
    assert exc.value.is_retryable is True
