from __future__ import annotations

import re
from typing import Any

import httpx

from app.providers.base import (
    Completion,
    ProviderError,
    TokenUsage,
    count_or_none,
    reported_usage,
)

# A caller-selected cloud model is a Gemini id: the "gemini" prefix plus a
# short unreserved token. Anything else keeps the configured model.
_CLOUD_MODEL = re.compile(r"gemini[A-Za-z0-9._-]{0,122}\Z")
_SAFETY_FINISH = frozenset({"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"})
_FINISH_REASON = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "content_filter",
    "RECITATION": "content_filter",
    "BLOCKLIST": "content_filter",
    "PROHIBITED_CONTENT": "content_filter",
    "SPII": "content_filter",
}


def caller_gemini_model(requested: str | None) -> str | None:
    """Return a caller Gemini model id, or None when the name is not one."""
    if requested is not None and _CLOUD_MODEL.fullmatch(requested):
        return requested
    return None


def _messages_to_gemini(
    messages: list[dict[str, str]],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Split OpenAI-shaped messages into systemInstruction + Gemini contents."""
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role", "user")
        text = message.get("content", "")
        if role == "system":
            system_parts.append(text)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": text}]})
    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, contents


class GeminiProvider:
    name = "cloud"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 30,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._client = client

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
        chosen = caller_gemini_model(model) or self._model
        system_instruction, contents = _messages_to_gemini(messages)
        if not contents:
            contents = [{"role": "user", "parts": [{"text": ""}]}]
        payload: dict[str, Any] = {"contents": contents}
        generation = _generation_config(temperature, max_tokens, top_p, stop)
        if generation:
            payload["generationConfig"] = generation
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        url = f"{self._base_url}/models/{chosen}:generateContent"
        data = await self._request("POST", url, json=payload)
        content = _extract_text(data)
        if _blocked_without_text(data, content):
            raise ProviderError("gemini blocked the prompt", status_code=400)
        reported = data.get("modelVersion", chosen)
        return Completion(
            content=content,
            model=reported if isinstance(reported, str) and reported else chosen,
            provider=self.name,
            usage=_usage_from_gemini(data),
            finish_reason=_finish_reason(data),
        )

    async def health(self) -> bool:
        try:
            await self._request("GET", f"{self._base_url}/models/{self._model}")
            return True
        except ProviderError:
            return False

    async def _request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"x-goog-api-key": self._api_key}
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        owns_client = self._client is None
        try:
            response = await client.request(method, url, json=json, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderError("gemini timeout", timed_out=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("gemini unreachable", status_code=503) from exc
        finally:
            if owns_client:
                await client.aclose()
        if response.status_code >= 500:
            raise ProviderError("gemini upstream error", status_code=response.status_code)
        if response.status_code >= 400:
            raise ProviderError("gemini client error", status_code=response.status_code)
        body: dict[str, Any] = response.json()
        return body


def _usage_from_gemini(data: dict[str, Any]) -> TokenUsage | None:
    meta = data.get("usageMetadata")
    if not isinstance(meta, dict):
        return None
    return reported_usage(
        count_or_none(meta.get("promptTokenCount")),
        count_or_none(meta.get("candidatesTokenCount")),
        count_or_none(meta.get("totalTokenCount")),
    )


def _generation_config(
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
    stop: list[str] | None,
) -> dict[str, Any]:
    generation: dict[str, Any] = {}
    if temperature is not None:
        generation["temperature"] = temperature
    if top_p is not None:
        generation["topP"] = top_p
    if max_tokens is not None:
        generation["maxOutputTokens"] = max_tokens
    if stop:
        generation["stopSequences"] = stop
    return generation


def _finish_token(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not isinstance(candidates, list) or not candidates:
        return ""
    first = candidates[0]
    if not isinstance(first, dict):
        return ""
    token = first.get("finishReason")
    if not isinstance(token, str):
        return ""
    return token


def _prompt_blocked(data: dict[str, Any]) -> bool:
    feedback = data.get("promptFeedback")
    if not isinstance(feedback, dict):
        return False
    reason = feedback.get("blockReason")
    return isinstance(reason, str) and bool(reason)


def _blocked_without_text(data: dict[str, Any], content: str) -> bool:
    if content:
        return False
    if _prompt_blocked(data):
        return True
    return _finish_token(data) in _SAFETY_FINISH


def _finish_reason(data: dict[str, Any]) -> str:
    if _prompt_blocked(data):
        return "content_filter"
    return _FINISH_REASON.get(_finish_token(data), "stop")


def _extract_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    content = (candidates[0] or {}).get("content") or {}
    parts = content.get("parts") or []
    texts = [str(part.get("text", "")) for part in parts if isinstance(part, dict)]
    return "".join(texts)
