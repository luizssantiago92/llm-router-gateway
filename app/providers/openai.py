from __future__ import annotations

import httpx

from app.providers.base import Completion, ProviderError


class OpenAIProvider:
    name = "cloud"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
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
        temperature: float,
        max_tokens: int | None,
    ) -> Completion:
        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        data = await self._post(f"{self._base_url}/chat/completions", json=payload)
        choices = data.get("choices") or [{}]
        message = (choices[0] or {}).get("message") or {}
        content = str(message.get("content", ""))
        model = str(data.get("model", self._model))
        return Completion(content=content, model=model, provider=self.name)

    async def health(self) -> bool:
        try:
            await self._get(f"{self._base_url}/models")
            return True
        except ProviderError:
            return False

    async def _post(self, url: str, json: dict) -> dict:
        return await self._request("POST", url, json=json)

    async def _get(self, url: str) -> dict:
        return await self._request("GET", url)

    async def _request(self, method: str, url: str, json: dict | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        owns_client = self._client is None
        try:
            response = await client.request(method, url, json=json, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderError("openai timeout", timed_out=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("openai unreachable", status_code=503) from exc
        finally:
            if owns_client:
                await client.aclose()
        if response.status_code >= 500:
            raise ProviderError("openai upstream error", status_code=response.status_code)
        if response.status_code >= 400:
            raise ProviderError("openai client error", status_code=response.status_code)
        return response.json()
