# LLM Router Gateway

High-performance FastAPI reverse gateway that orchestrates, routes, and caches chat-completion traffic across local and cloud LLM providers.

Internal applications call a single OpenAI-compatible facade. The gateway applies exact-match Redis caching, complexity-based routing, and one-hop fallback so simple or repeated prompts stay cheap and fast, while complex work still reaches a stronger cloud model.

## Status

Specification in progress. Elicitation is complete; implementation has not started.

| Item | Location |
| --- | --- |
| Product kickoff | [`prd.md`](prd.md) |
| Approved requirements brief | [`.specs/features/llm-router-gateway/brief.md`](.specs/features/llm-router-gateway/brief.md) |
| Project memory | [`.specs/project/PROJECT.md`](.specs/project/PROJECT.md) |
| Architecture | [`docs/architecture.md`](docs/architecture.md) |
| API contract (v1) | [`docs/api.md`](docs/api.md) |
| How we work | [`docs/development.md`](docs/development.md) |
| Docs index | [`docs/README.md`](docs/README.md) |

Next phase: `/specify` → Discuss → Design → Tasks (Complex tier).

## What it does

- **Cache first** — SHA-256 exact match in Redis; cache hits target **<10 ms** with `cached: true` and `latency_ms`.
- **Route by complexity** — short/simple prompts go to a local model (Ollama / Llama 3 8B class by default); code, long, or structured-reasoning prompts go to the cloud (OpenAI by default).
- **Fail over once** — HTTP 5xx or timeout on the primary provider retries the other tier, then fails the request.
- **Stay observable** — provider origin, cache status, and latency on both JSON fields and response headers.

Business goals from the PRD: cut paid-token volume by at least 30% via local routing, and remove a single cloud provider as a hard dependency.

## Planned stack

| Layer | Choice |
| --- | --- |
| API | Python 3.10+, FastAPI, asyncio, Pydantic v2 |
| HTTP client | httpx (async) |
| Cache | Redis via redis-py async |
| Local LLM | Ollama (vLLM adapter-ready) |
| Cloud LLM | OpenAI (Anthropic adapter-ready) |
| Ship unit | Docker Compose (app + Redis) |
| Tests | pytest-asyncio (routing, cache hit/miss, fallback) |

Application source, Compose, and tests will land in later PRs after `spec.md` is approved.

## API (planned)

```http
POST /v1/chat/completions
GET  /health
```

Request body follows OpenAI Chat Completions (`messages`, `temperature`, `max_tokens`). There is no caller authentication in v1 (internal network). Streaming is out of scope. Full contract: [`docs/api.md`](docs/api.md).

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
