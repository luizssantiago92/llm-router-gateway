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


class _Crash:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        **_extra: object,
    ) -> None:
        self.calls += 1
        raise RuntimeError("provider crashed")

    async def health(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_unexpected_primary_failure_hops_once() -> None:
    local = _Crash("local")
    cloud = FakeProvider("cloud", content="from-cloud")
    router = Router(local, cloud, word_threshold=150)
    result = await router.complete([{"role": "user", "content": "hi"}], 0.0, 8)
    assert result.content == "from-cloud"
    assert local.calls == 1
    assert cloud.calls == 1


@pytest.mark.asyncio
async def test_non_retryable_primary_does_not_call_secondary() -> None:
    local = FakeProvider("local", error=ProviderError("bad request", status_code=400))
    cloud = FakeProvider("cloud", content="should-not-run")
    router = Router(local, cloud, word_threshold=150)
    with pytest.raises(ProviderError) as exc:
        await router.complete([{"role": "user", "content": "hi"}], 0.0, 8)
    assert exc.value.status_code == 400
    assert local.calls == 1
    assert cloud.calls == 0


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
