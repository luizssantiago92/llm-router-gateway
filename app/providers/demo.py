"""In-process providers for PROVIDER_MODE=demo.

They echo the caller text, pause for a short fixed delay, and fail when the
prompt contains a documented token so one hop of fallback is visible.
"""

from __future__ import annotations

import asyncio

from app.providers.base import Completion, ProviderError, TokenUsage

LOCAL_FAILURE_MARK = "simulate-local-failure"
CLOUD_FAILURE_MARK = "simulate-cloud-failure"
DEMO_LATENCY_SECONDS = 0.05

_USAGE = TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2)


class DemoProvider:
    name: str

    def __init__(self, name: str, *, delay_seconds: float = 0.0) -> None:
        self.name = name
        self.delay_seconds = delay_seconds

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float | None,
        max_tokens: int | None,
        *,
        top_p: float | None = None,
        stop: list[str] | None = None,
        model: str | None = None,
    ) -> Completion:
        del temperature, max_tokens, top_p, stop, model
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        text = _echo_text(messages)
        if self.name == "local" and LOCAL_FAILURE_MARK in text:
            raise ProviderError("demo local provider failed", status_code=503)
        if self.name == "cloud" and CLOUD_FAILURE_MARK in text:
            raise ProviderError("demo cloud provider failed", status_code=503)
        return Completion(
            content=text,
            model=f"demo-{self.name}",
            provider=self.name,
            usage=_USAGE,
        )

    async def health(self) -> bool:
        return True


def _echo_text(messages: list[dict[str, str]]) -> str:
    user = [str(item.get("content", "")) for item in messages if item.get("role") == "user"]
    if user:
        return user[-1]
    if messages:
        return str(messages[-1].get("content", ""))
    return ""
