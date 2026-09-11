import pytest

from app.providers.fake import FakeProvider
from app.routing.evaluator import classify
from app.routing.router import Router

GOLDEN_PROMPTS = [
    ("hello", "simple"),
    ("what time is it", "simple"),
    ("please implement this algorithm in a function", "complex"),
    ("DEBUG the class step by step", "complex"),
]


@pytest.mark.asyncio
async def test_golden_set_records_simple_versus_complex_destinations() -> None:
    local = FakeProvider("local", content="local")
    cloud = FakeProvider("cloud", content="cloud")
    router = Router(local, cloud, word_threshold=150)
    destinations = {"local": 0, "cloud": 0}
    for prompt, expected in GOLDEN_PROMPTS:
        kind = classify([{"role": "user", "content": prompt}])
        assert kind == expected
        result = await router.complete([{"role": "user", "content": prompt}], 0.0, 8)
        destinations[result.provider] += 1
    assert destinations["local"] == 2
    assert destinations["cloud"] == 2
    assert local.calls == 2
    assert cloud.calls == 2
