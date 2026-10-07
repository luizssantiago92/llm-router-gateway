from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TokenUsage:
    """Counts reported by a provider. Missing counts stay null."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


def count_or_none(value: object) -> int | None:
    """Accept a non-negative integer count and reject anything else."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def reported_usage(
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
) -> TokenUsage | None:
    """Build usage from provider-reported counts.

    ``total_tokens`` is the provider total when present. When the provider
    reports both sides and no total, the total is their sum. The gateway
    does not estimate a count the provider omitted.
    """
    if prompt_tokens is None and completion_tokens is None and total_tokens is None:
        return None
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    return TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


@dataclass(frozen=True)
class Completion:
    content: str
    model: str
    provider: str
    usage: TokenUsage | None = None


class ProviderError(Exception):
    """Upstream failure that the router can classify as 5xx or timeout."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        timed_out: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.timed_out = timed_out

    @property
    def is_retryable(self) -> bool:
        if self.timed_out:
            return True
        return self.status_code is not None and self.status_code >= 500


class Provider(Protocol):
    name: str

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
    ) -> Completion: ...

    async def health(self) -> bool: ...
