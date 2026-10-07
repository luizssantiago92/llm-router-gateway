from __future__ import annotations

from app.providers.base import Completion, Provider, ProviderError
from app.routing.evaluator import classify

# ProviderError is handled on its own so a non-retryable 4xx is not hopped.
# Every other Exception from a provider is one hop, then a 502.
_UNEXPECTED = (Exception,)


class Router:
    def __init__(
        self,
        local: Provider,
        cloud: Provider,
        word_threshold: int = 150,
    ) -> None:
        self._local = local
        self._cloud = cloud
        self._word_threshold = word_threshold

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
        kind = classify(messages, self._word_threshold)
        primary = self._local if kind == "simple" else self._cloud
        secondary = self._cloud if kind == "simple" else self._local
        try:
            return await primary.complete(
                messages,
                temperature,
                max_tokens,
                top_p=top_p,
                stop=stop,
                model=model,
            )
        except ProviderError as exc:
            if not exc.is_retryable:
                raise
        except _UNEXPECTED:
            pass
        try:
            return await secondary.complete(
                messages,
                temperature,
                max_tokens,
                top_p=top_p,
                stop=stop,
                model=model,
            )
        except _UNEXPECTED as second:
            raise ProviderError("both providers failed", status_code=502) from second
