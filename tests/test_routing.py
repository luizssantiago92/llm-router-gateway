import pytest

from app.providers.base import ProviderError
from app.providers.fake import FakeProvider
from app.routing.router import Router


@pytest.mark.asyncio
async def test_simple_prompt_uses_local_primary() -> None:
    local = FakeProvider("local", content="from-local")
    cloud = FakeProvider("cloud", content="from-cloud")
    router = Router(local, cloud, word_threshold=150)
    result = await router.complete([{"role": "user", "content": "hi"}], 0.0, 8)
    assert result.content == "from-local"
    assert local.calls == 1
    assert cloud.calls == 0


@pytest.mark.asyncio
async def test_complex_prompt_uses_cloud_primary() -> None:
    local = FakeProvider("local", content="from-local")
    cloud = FakeProvider("cloud", content="from-cloud")
    router = Router(local, cloud, word_threshold=150)
    result = await router.complete(
        [{"role": "user", "content": "please implement this algorithm"}],
        0.0,
        8,
    )
    assert result.content == "from-cloud"
    assert cloud.calls == 1
    assert local.calls == 0
