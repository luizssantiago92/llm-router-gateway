"""Environment-backed process settings. Values never come from git."""

from __future__ import annotations

import os
from dataclasses import dataclass

# Built-in ceilings. Settings may lower these; they cannot raise them.
MAX_MESSAGE_CHARS = 32_000
MAX_MESSAGES = 50
MAX_TOTAL_MESSAGE_CHARS = 64_000
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
MIN_MAX_TOKENS = 1
MAX_MAX_TOKENS = 4096
MAX_BODY_BYTES = 256 * 1024

# Documented local key for PROVIDER_MODE=demo. Live mode never uses it.
DEMO_GATEWAY_API_KEY = "demo"
_DEMO_OLLAMA_BASE_URL = "http://127.0.0.1:11434"

SETTINGS_KEYS = (
    "REDIS_URL",
    "OLLAMA_BASE_URL",
    "GEMINI_API_KEY",
    "GATEWAY_API_KEY",
    "CACHE_TTL_SECONDS",
    "COMPLEXITY_WORD_THRESHOLD",
    "UPSTREAM_TIMEOUT_SECONDS",
    "CHAT_DAILY_LIMIT",
)

_DEFAULTS = {
    "CACHE_TTL_SECONDS": "3600",
    "COMPLEXITY_WORD_THRESHOLD": "150",
    "UPSTREAM_TIMEOUT_SECONDS": "30",
    "CHAT_DAILY_LIMIT": "5",
    "GEMINI_MODEL": "gemini-3.5-flash",
    "MAX_MESSAGE_CHARS": str(MAX_MESSAGE_CHARS),
    "MAX_MESSAGES": str(MAX_MESSAGES),
    "MAX_TOTAL_MESSAGE_CHARS": str(MAX_TOTAL_MESSAGE_CHARS),
    "MIN_TEMPERATURE": str(MIN_TEMPERATURE),
    "MAX_TEMPERATURE": str(MAX_TEMPERATURE),
    "MIN_MAX_TOKENS": str(MIN_MAX_TOKENS),
    "MAX_MAX_TOKENS": str(MAX_MAX_TOKENS),
    "MAX_BODY_BYTES": str(MAX_BODY_BYTES),
}


@dataclass(frozen=True)
class Settings:
    redis_url: str
    ollama_base_url: str
    gemini_api_key: str
    gateway_api_key: str
    cache_ttl_seconds: int
    complexity_word_threshold: int
    upstream_timeout_seconds: int
    chat_daily_limit: int = 5
    gemini_model: str = "gemini-3.5-flash"
    max_message_chars: int = MAX_MESSAGE_CHARS
    max_messages: int = MAX_MESSAGES
    max_total_message_chars: int = MAX_TOTAL_MESSAGE_CHARS
    min_temperature: float = MIN_TEMPERATURE
    max_temperature: float = MAX_TEMPERATURE
    min_max_tokens: int = MIN_MAX_TOKENS
    max_max_tokens: int = MAX_MAX_TOKENS
    max_body_bytes: int = MAX_BODY_BYTES
    provider_mode: str = "live"

    def __post_init__(self) -> None:
        if self.provider_mode not in {"live", "demo"}:
            raise RuntimeError("PROVIDER_MODE must be live or demo")
        _within("max_message_chars", self.max_message_chars, 1, MAX_MESSAGE_CHARS)
        _within("max_messages", self.max_messages, 1, MAX_MESSAGES)
        _within(
            "max_total_message_chars",
            self.max_total_message_chars,
            1,
            MAX_TOTAL_MESSAGE_CHARS,
        )
        if not (MIN_TEMPERATURE <= self.min_temperature <= self.max_temperature <= MAX_TEMPERATURE):
            raise RuntimeError("temperature limits must stay inside 0..2")
        if not (MIN_MAX_TOKENS <= self.min_max_tokens <= self.max_max_tokens <= MAX_MAX_TOKENS):
            raise RuntimeError("max_tokens limits must stay inside 1..4096")
        _within("max_body_bytes", self.max_body_bytes, 1, MAX_BODY_BYTES)

    @classmethod
    def from_env(cls) -> Settings:
        redis_url = _require("REDIS_URL")
        mode = os.environ.get("PROVIDER_MODE", "live").strip().lower()
        if mode not in {"live", "demo"}:
            raise RuntimeError("PROVIDER_MODE must be live or demo")
        if mode == "demo":
            gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
            gateway_api_key = os.environ.get("GATEWAY_API_KEY", "").strip() or DEMO_GATEWAY_API_KEY
            ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "").strip() or _DEMO_OLLAMA_BASE_URL
        else:
            gemini_api_key = _require("GEMINI_API_KEY")
            gateway_api_key = _require("GATEWAY_API_KEY")
            ollama_base_url = _require("OLLAMA_BASE_URL")
        return cls(
            redis_url=redis_url,
            ollama_base_url=ollama_base_url,
            gemini_api_key=gemini_api_key,
            gateway_api_key=gateway_api_key,
            provider_mode=mode,
            cache_ttl_seconds=int(
                os.environ.get("CACHE_TTL_SECONDS", _DEFAULTS["CACHE_TTL_SECONDS"])
            ),
            complexity_word_threshold=int(
                os.environ.get("COMPLEXITY_WORD_THRESHOLD", _DEFAULTS["COMPLEXITY_WORD_THRESHOLD"])
            ),
            upstream_timeout_seconds=int(
                os.environ.get("UPSTREAM_TIMEOUT_SECONDS", _DEFAULTS["UPSTREAM_TIMEOUT_SECONDS"])
            ),
            chat_daily_limit=int(os.environ.get("CHAT_DAILY_LIMIT", _DEFAULTS["CHAT_DAILY_LIMIT"])),
            gemini_model=os.environ.get("GEMINI_MODEL", _DEFAULTS["GEMINI_MODEL"]),
            max_message_chars=int(
                os.environ.get("MAX_MESSAGE_CHARS", _DEFAULTS["MAX_MESSAGE_CHARS"])
            ),
            max_messages=int(os.environ.get("MAX_MESSAGES", _DEFAULTS["MAX_MESSAGES"])),
            max_total_message_chars=int(
                os.environ.get("MAX_TOTAL_MESSAGE_CHARS", _DEFAULTS["MAX_TOTAL_MESSAGE_CHARS"])
            ),
            min_temperature=float(os.environ.get("MIN_TEMPERATURE", _DEFAULTS["MIN_TEMPERATURE"])),
            max_temperature=float(os.environ.get("MAX_TEMPERATURE", _DEFAULTS["MAX_TEMPERATURE"])),
            min_max_tokens=int(os.environ.get("MIN_MAX_TOKENS", _DEFAULTS["MIN_MAX_TOKENS"])),
            max_max_tokens=int(os.environ.get("MAX_MAX_TOKENS", _DEFAULTS["MAX_MAX_TOKENS"])),
            max_body_bytes=int(os.environ.get("MAX_BODY_BYTES", _DEFAULTS["MAX_BODY_BYTES"])),
        )


def _require(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable {key}")
    return value


def _within(name: str, value: int, floor: int, ceiling: int) -> None:
    if value < floor or value > ceiling:
        raise RuntimeError(f"{name} must stay inside {floor}..{ceiling}")
