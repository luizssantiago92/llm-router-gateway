# Quick start

Get from zero to a Gemini-backed chat response in about ten minutes.

## 1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL 2 on Windows) or another Compose-capable Docker
- A [Gemini API key](https://aistudio.google.com/apikey)
- Ollama is **optional** (REQ-022). Skip it on a light PC.

## 2. Configure secrets

```bash
cp .env.example .env
```

Fill **only** these two unless you need overrides:

| Variable | What to put |
| --- | --- |
| `GEMINI_API_KEY` | From Google AI Studio |
| `GATEWAY_API_KEY` | Any secret you invent — callers send it as `X-API-Key` |

Leave the rest blank to use Compose defaults (`gemini-3.5-flash`, daily limit `5`, Ollama URL `http://host.docker.internal:11434`, TTL `3600`, word threshold `150`, timeout `30`). Leave `REDIS_URL` blank — Compose sets `redis://redis:6379/0` inside `api` and **does not** read that key from `.env`.

Never commit `.env`. The app does not call `load_dotenv`.

## 3. Start Compose

```bash
docker compose up --build
```

| Service | Port |
| --- | --- |
| `api` | **8000** (OpenAPI: `/docs`) |
| `redis` | **6379** |

Linux Docker Engine: Compose maps `host.docker.internal` → `host-gateway` so optional **host** Ollama is reachable. Docker Desktop already provides that hostname.

## 4. Health (no API key)

```bash
curl -s http://localhost:8000/health
```

| Result | Meaning |
| --- | --- |
| HTTP 200 `"ok"` | Redis + Ollama + Gemini reachable |
| HTTP 200 `"degraded"` | Redis up; at least one provider down (typical without Ollama) |
| HTTP 503 `"down"` | Redis unreachable |

## 5. Chat (API key required)

Use the **same** `GATEWAY_API_KEY` value as `.env`. Compose injects it into the container; an unset shell `$GATEWAY_API_KEY` **401**s.

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_GATEWAY_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

`"Hello"` is **simple**. Without Ollama the local hop fails (retryable) and Gemini answers — expect `provider: "cloud"` on a miss.

| Result | Meaning |
| --- | --- |
| `200` + `provider: "cloud"` | Gemini served a cache miss (typical without Ollama) |
| `200` + `cached: true` | Repeat of the same messages/temperature/max_tokens (quota not consumed) |
| `401` | Missing or wrong `X-API-Key` |
| `429` | Daily cache-miss quota exhausted (default 5; UTC midnight) |
| `422` | Invalid body or `stream: true` |
| `502` | Both hops failed, or primary returned non-retryable 4xx (no second hop). Quota refunded |

Interactive contract: http://localhost:8000/docs

## What “good” looks like after ten minutes

- Compose is up (`api` + `redis`)
- `/health` is `degraded` or `ok`
- One chat curl returns assistant content
- Repeating the same body returns `cached: true` and does not consume quota

## Tests (no live Gemini)

```bash
pip install -e ".[dev]"
pytest
```

`pyproject.toml` `addopts` already applies `-m "not live"`.

## If something feels stuck

- **401 on chat?** The header must match `.env` `GATEWAY_API_KEY` exactly — not an empty `$GATEWAY_API_KEY`.
- **Container restart loop?** `GEMINI_API_KEY` and `GATEWAY_API_KEY` must be non-empty; `Settings.from_env` refuses blanks.
- **Want the request path?** → [How it works](How-it-works.md)
- **Want every status code?** → [API](API.md)

## Next

- **Full picture** → [Overview](Overview.md)
- **Architecture** → [Architecture.md](Architecture.md)
- **Common questions** → [FAQ](FAQ.md)
- Back → [Home](Home.md)
