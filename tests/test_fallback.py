import pytest

from app.providers.base import ProviderError
from app.providers.fake import FakeProvider
from app.routing.router import Router


@pytest.mark.asyncio
async def test_primary_5xx_retries_opposite_tier_once() -> None:
    local = FakeProvider("local", error=ProviderError("down", status_code=503))
    cloud = FakeProvider("cloud", content="fallback")
    router = Router(local, cloud, word_threshold=150)
    result = await router.complete([{"role": "user", "content": "hi"}], 0.0, 8)
    assert result.content == "fallback"
    assert local.calls == 1
    assert cloud.calls == 1


@pytest.mark.asyncio
async def test_primary_timeout_retries_opposite_tier_once() -> None:
    cloud = FakeProvider("cloud", error=ProviderError("slow", timed_out=True))
    local = FakeProvider("local", content="local-fallback")
    router = Router(local, cloud, word_threshold=150)
    result = await router.complete(
        [{"role": "user", "content": "please implement this algorithm"}],
        0.0,
        8,
    )
    assert result.content == "local-fallback"
    assert cloud.calls == 1
    assert local.calls == 1


@pytest.mark.asyncio
async def test_dual_failure_does_not_retry_a_third_time() -> None:
    local = FakeProvider("local", error=ProviderError("down", status_code=500))
    cloud = FakeProvider("cloud", error=ProviderError("down", status_code=500))
    router = Router(local, cloud, word_threshold=150)
    with pytest.raises(ProviderError) as exc:
        await router.complete([{"role": "user", "content": "hi"}], 0.0, 8)
    assert exc.value.status_code == 502
    assert local.calls == 1
    assert cloud.calls == 1
