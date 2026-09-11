import pytest

from app.providers.base import Completion, ProviderError
from app.providers.fake import FakeProvider


@pytest.mark.asyncio
async def test_fake_adapter_returns_completion() -> None:
    provider = FakeProvider("local", content="hello")
    result = await provider.complete(
        [{"role": "user", "content": "hi"}],
        temperature=0.0,
        max_tokens=8,
    )
    assert isinstance(result, Completion)
    assert result.content == "hello"
    assert result.provider == "local"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_fake_adapter_can_raise_retryable_5xx() -> None:
    provider = FakeProvider("cloud", error=ProviderError("boom", status_code=503))
    with pytest.raises(ProviderError) as exc:
        await provider.complete([], 0.0, 1)
    assert exc.value.is_retryable is True
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_fake_adapter_can_raise_timeout() -> None:
    provider = FakeProvider("local", error=ProviderError("timeout", timed_out=True))
    with pytest.raises(ProviderError) as exc:
        await provider.complete([], 0.0, 1)
    assert exc.value.timed_out is True
    assert exc.value.is_retryable is True
