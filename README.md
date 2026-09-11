# LLM Router Gateway

High-performance FastAPI reverse gateway that orchestrates, routes, and caches chat-completion traffic across local and cloud LLM providers.

Internal applications call a single OpenAI-compatible facade. The gateway applies exact-match Redis caching, complexity-based routing, and one-hop fallback so simple or repeated prompts stay cheap and fast, while complex work still reaches a stronger cloud model.

## Status

v1 is **archived**. Independent `/verify` PASS; domain truth is [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md). Feature history stays under [`.specs/features/001-llm-router-gateway/`](.specs/features/001-llm-router-gateway/spec.md).

| Item | Location |
| --- | --- |
| Product kickoff | [`prd.md`](prd.md) |
| Requirements brief | [`.specs/features/llm-router-gateway/brief.md`](.specs/features/llm-router-gateway/brief.md) |
| Domain truth (v1) | [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) |
| Feature spec (historical) | [`.specs/features/001-llm-router-gateway/spec.md`](.specs/features/001-llm-router-gateway/spec.md) |
| Design | [`.specs/features/001-llm-router-gateway/design.md`](.specs/features/001-llm-router-gateway/design.md) |
| Tasks | [`.specs/features/001-llm-router-gateway/tasks.md`](.specs/features/001-llm-router-gateway/tasks.md) |
| Validation | [`.specs/features/001-llm-router-gateway/validation.md`](.specs/features/001-llm-router-gateway/validation.md) |
| Feature dashboard | [`.specs/features/001-llm-router-gateway/overview.md`](.specs/features/001-llm-router-gateway/overview.md) |
| Project memory | [`.specs/project/PROJECT.md`](.specs/project/PROJECT.md) |
| Architecture | [`docs/architecture.md`](docs/architecture.md) |
| API contract (v1) | [`docs/api.md`](docs/api.md) |
| How we work | [`docs/development.md`](docs/development.md) |
| Docs index | [`docs/README.md`](docs/README.md) |

Next work starts with `feature-init` (delta specs against the domain). Do not re-ask **D-001–D-012**.

## What it does

- **Cache first** — SHA-256 exact match in Redis; cache hits target **<10 ms** with `cached: true` and `latency_ms`.
- **Route by complexity** — short/simple prompts go to a local model (Ollama / Llama 3 8B class by default); code, long, or structured-reasoning prompts go to the cloud (**Gemini** free-tier default).
- **Fail over once** — HTTP 5xx or timeout on the primary provider retries the other tier, then fails the request.
- **Demo cost guard** — callers send `X-API-Key`; cache misses consume a daily quota (default 5); cache hits do not.
- **Stay observable** — provider origin, cache status, and latency on both JSON fields and response headers.

Business goals from the PRD: cut paid-token volume by at least 30% via local routing, and remove a single cloud provider as a hard dependency.

## Stack

| Layer | Choice |
| --- | --- |
| API | Python 3.10+, FastAPI, asyncio, Pydantic v2 |
| HTTP client | httpx (async) |
| Cache | Redis via redis-py async |
| Local LLM | Ollama (vLLM adapter-ready) |
| Cloud LLM | Google Gemini (demo / free-tier default) |
| Ship unit | Docker Compose (app + Redis) |
| Tests | pytest-asyncio (routing, cache hit/miss, fallback, quota) |

Application source lives in `app/`. Default test command: `pytest` (`-m "not live"`). Local ship unit: `docker compose up --build`.

## API

```http
POST /v1/chat/completions
GET  /health
```

Request body follows OpenAI Chat Completions (`messages`, `temperature`, `max_tokens`). Callers must send header `X-API-Key` matching `GATEWAY_API_KEY`. `stream: true` is rejected with HTTP 422. Full contract: [`docs/api.md`](docs/api.md).

## Run locally

Copy [`.env.example`](.env.example) and set values in the environment (never commit `.env`):

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_URL` | yes | — (Compose sets Redis) |
| `OLLAMA_BASE_URL` | yes | Compose default `host.docker.internal:11434` |
| `GEMINI_API_KEY` | yes | — (Google AI Studio) |
| `GEMINI_MODEL` | no | `gemini-2.0-flash` |
| `GATEWAY_API_KEY` | yes | — (shared demo secret for `X-API-Key`) |
| `CHAT_DAILY_LIMIT` | no | `5` |
| `CACHE_TTL_SECONDS` | no | `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | `30` |

```bash
pip install -e ".[dev]"
pytest
docker compose up --build
```

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $GATEWAY_API_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

Compose starts `api` on port 8000 and `redis` on 6379. Ollama is expected at `OLLAMA_BASE_URL` (not bundled in Compose).

## Documentation policy

Every pull request updates this README when status, setup, API, or links change, and keeps [`docs/`](docs/README.md) aligned with what the PR actually ships. See [`docs/development.md`](docs/development.md#documentation-on-every-pr).

## Spec-driven workflow

This repo uses [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) (`python-platform` preset). Chat with the agent; do not memorize CLI.

```
/elicit → /specify → /discuss? → /plan → /tasks → /loop → /verify → /archive
```

- Hub: [`.cursor/skills/agent-architecture.md`](.cursor/skills/agent-architecture.md)
- Session state: [`.specs/STATE.md`](.specs/STATE.md)
- Install health: `npx @luizsantiago/spec-guardrails doctor`

## License

See repository settings. Do not commit secrets, API keys, or `.env` files.
