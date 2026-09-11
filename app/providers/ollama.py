from __future__ import annotations

import httpx

from app.providers.base import Completion, ProviderError


class OllamaProvider:
    name = "local"

    def __init__(
        self,
        base_url: str,
        model: str = "llama3",
        timeout_seconds: float = 30,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds
        self._client = client

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
    ) -> Completion:
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        data = await self._post(f"{self._base_url}/api/chat", json=payload)
        message = data.get("message") or {}
        content = str(message.get("content", ""))
        model = str(data.get("model", self._model))
        return Completion(content=content, model=model, provider=self.name)

    async def health(self) -> bool:
        try:
            await self._get(f"{self._base_url}/api/tags")
            return True
        except ProviderError:
            return False

    async def _post(self, url: str, json: dict) -> dict:
        return await self._request("POST", url, json=json)

    async def _get(self, url: str) -> dict:
        return await self._request("GET", url)

    async def _request(self, method: str, url: str, json: dict | None = None) -> dict:
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        owns_client = self._client is None
        try:
            response = await client.request(method, url, json=json)
        except httpx.TimeoutException as exc:
            raise ProviderError("ollama timeout", timed_out=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("ollama unreachable", status_code=503) from exc
        finally:
            if owns_client:
                await client.aclose()
        if response.status_code >= 500:
            raise ProviderError("ollama upstream error", status_code=response.status_code)
        if response.status_code >= 400:
            raise ProviderError("ollama client error", status_code=response.status_code)
        return response.json()
