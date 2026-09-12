# LLM Router Gateway

**One OpenAI-shaped facade for local and cloud chat models — zero-cost demo.**

Internal apps call a single completions endpoint. The gateway caches exact matches, sends simple work to a local model when available, sends complex work to the cloud (Gemini), and fails over once when an upstream is down.

| Status | Detail |
| --- | --- |
| **Shipped** | Compose demo (`api` + `redis`); smoke `/health` + chat via Gemini |
| **Posture** | Academic / demonstrative reference — not a production chatbot |
| **Cloud** | Google Gemini free tier (`GEMINI_API_KEY`, default `GEMINI_MODEL=gemini-3.5-flash`) |
| **Local** | Optional Ollama (`llama3` class); unreachable → health `degraded`, fallback to Gemini |
| **Cost guard** | Shared `X-API-Key` (`GATEWAY_API_KEY`) + Redis daily quota (default 5; cache hits free) |
| **Contract** | `POST /v1/chat/completions` · `GET /health` (no key) · OpenAPI at `/docs` |
| **Domain** | [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022) |

**Reuse intent:** patterns here (cache, complexity routing, fallback, quota, Gemini adapter) may be lifted into [Gold Queen](https://github.com/luizssantiago92/gold-queen-api) where useful, and later into a **real company chatbot**. This repo stays the **demo / lab** surface.

---

## The problem

Calling a cloud LLM directly from every service creates three recurring costs:

| Pain | What goes wrong |
| --- | --- |
| **Cost** | Short, repeated, or simple prompts burn paid tokens |
| **Latency** | Identical requests hit the network every time |
| **SPOF** | One upstream outage blocks the whole product |

You want a stable contract for applications — not a scatter of provider SDKs and ad-hoc retries.

---

## What you get

| Without the gateway | With LLM Router Gateway |
| --- | --- |
| Every call is a paid cloud hop | Exact-match cache returns repeats in milliseconds |
| Apps pick models and fail over themselves | Simple → local; complex → cloud; one automatic hop |
| Outage = hard fail | Primary 5xx/timeout retries the other tier once |
| Opaque origin | `X-Cache` / `X-Latency-Ms` / `X-Provider` on every response |
| Unbounded demo spend | Shared `X-API-Key` + daily quota (cache hits free) |

---

## How it works

1. **Authenticate (chat only)** — `POST /v1/chat/completions` requires `X-API-Key` matching `GATEWAY_API_KEY` (401 if missing/wrong). `GET /health` has no key.
2. **Look up the cache** — Same messages, temperature, and max tokens? Serve Redis and stop (quota not consumed).
3. **Classify the prompt** — Short and plain prefers local; long text (>150 words) or code/reasoning keywords go to Gemini.
4. **Call one provider** — Local (Ollama, if running) or cloud (Gemini). Cache misses consume one daily quota unit first (429 when exhausted).
5. **Fail over once** — If the primary returns 5xx or times out, try the other tier; both fail → 502 and the quota unit is refunded.
6. **Store and observe** — Successful misses are cached; every response carries cache, latency, and provider signals.

Clients never choose a provider. Streaming is not supported (`stream: true` → 422).

**Without Ollama:** leave `OLLAMA_BASE_URL` at the Compose default. Health stays `degraded` (local down, cloud up); simple prompts fail locally once and **fall back to Gemini**. That is the supported light-PC demo path (REQ-022).

---

## Quick start

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL 2 on Windows) or another Compose-capable Docker, and a [Gemini API key](https://aistudio.google.com/apikey). Ollama is optional.

```bash
cp .env.example .env
# Required in .env:
#   GEMINI_API_KEY     — from Google AI Studio
#   GATEWAY_API_KEY    — any secret you invent; callers send it as X-API-Key
# Optional:
#   GEMINI_MODEL       — default gemini-3.5-flash
#   CHAT_DAILY_LIMIT   — default 5
#   OLLAMA_BASE_URL    — default http://host.docker.internal:11434

docker compose up --build
```

Health does **not** need the gateway key:

```bash
curl -s http://localhost:8000/health
# Expect HTTP 200: "ok" if Ollama and Gemini are both up; "degraded" if only Gemini is up.
# Redis down → HTTP 503, status "down".
```

Chat **does**. Use the same `GATEWAY_API_KEY` value you wrote in `.env` (Compose injects it into the `api` container; an unset shell `$GATEWAY_API_KEY` will 401):

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_GATEWAY_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

Interactive contract: [http://localhost:8000/docs](http://localhost:8000/docs).

### Expected chat outcomes

| Result | Meaning |
| --- | --- |
| `200` + `provider: "cloud"` | Gemini served a cache miss (typical without Ollama) |
| `200` + `cached: true` | Repeat of the same messages/temperature/max_tokens (quota not consumed) |
| `401` | `X-API-Key` missing or not equal to `GATEWAY_API_KEY` |
| `429` | Daily cache-miss quota exhausted (default 5; resets at UTC midnight) |
| `422` | Invalid body or `stream: true` |
| `502` | Both hops failed, or the primary returned a non-retryable 4xx (no second hop). Quota unit refunded |

Full env table and pytest: [`docs/development.md`](docs/development.md). Contract detail: [`docs/api.md`](docs/api.md).

---

## Environment (Compose)

Compose loads `.env` for substitution. Fill the secrets; leave the rest blank to use defaults.

| Variable | Required in `.env` | What Compose does |
| --- | --- | --- |
| `GEMINI_API_KEY` | yes | Passed through |
| `GATEWAY_API_KEY` | yes | Passed through (callers send it as `X-API-Key`) |
| `GEMINI_MODEL` | no | Default `gemini-3.5-flash` |
| `CHAT_DAILY_LIMIT` | no | Default `5` |
| `OLLAMA_BASE_URL` | no | Default `http://host.docker.internal:11434` |
| `CACHE_TTL_SECONDS` | no | Default `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | Default `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | Default `30` |
| `REDIS_URL` | no (leave blank) | Hardcoded `redis://redis:6379/0` inside `api` — `.env` does not override it |

Never commit `.env`. The app reads the process environment only (no `load_dotenv`).

**Ollama on Linux Docker Engine:** Compose maps `host.docker.internal` → `host-gateway` so an optional host Ollama is reachable. Docker Desktop (Mac/Windows) already provides that hostname. If you skip Ollama entirely, you can leave the default URL; the demo still works via Gemini fallback.

---

## Tests

Default gate skips live upstreams (`pyproject.toml` `addopts` already applies `-m "not live"`):

```bash
pip install -e ".[dev]"
pytest
```

---

## Still open (agents: read this)

This repo is a **demonstrative** gateway. Do **not** treat the list below as in-scope until the owner starts a new `feature-init`. Prefer extracting useful pieces into Gold Queen or a future production chatbot rather than growing this demo into a full product here.

| Item | Status | Notes |
| --- | --- | --- |
| Streaming (`stream: true`) | **deferred** | Rejected with 422 today (D-009) |
| Production edge auth | **deferred** | Only shared `GATEWAY_API_KEY` / `X-API-Key` |
| Multi-tenancy / per-tenant quotas | **deferred** | Single demo key + daily Redis bucket (UTC midnight) |
| Semantic / embedding cache | **deferred** | Exact-match SHA-256 only |
| Rate limits beyond daily quota | **deferred** | — |
| RAG / tools / function calling | **deferred** | — |
| Paid OpenAI (or other paid cloud) happy path | **deferred** | Separate product / company chatbot later |
| vLLM / Anthropic adapters (happy path) | **deferred** | Protocol-ready ideas only |
| Kubernetes / Helm / Terraform | **deferred** | Compose is the ship unit |
| Hosted deploy (Render, etc.) | **not started** | Optional for demos; Gold Queen already has deploy patterns |
| First-class Ollama in Compose | **not started** | Ollama stays external; optional on stronger machines |
| UI / chat frontend | **not started** | API-only demo |

**Owner roadmap (outside this repo):** (1) reuse interesting bits in Gold Queen → (2) later build a real company chatbot on paid/controlled infra → (3) keep **this** repository as the academic / zero-cost demonstrative reference.

Session pointer: [`.specs/STATE.md`](.specs/STATE.md). Milestones: [`.specs/project/ROADMAP.md`](.specs/project/ROADMAP.md).

---

## Documentation

| Doc | For |
| --- | --- |
| [Architecture](docs/architecture.md) | Request path, cache, routing, fallback |
| [API](docs/api.md) | Contract, headers, status codes, quota |
| [Development](docs/development.md) | Stack, env vars, tests, Compose, Spec Guardrails |

**Go deeper:** [docs index](docs/README.md) · product kickoff [`prd.md`](prd.md) · domain [`spec.md`](.specs/domains/llm-router-gateway/spec.md)

---

## License

No `LICENSE` file is published on this repository. Do not assume reuse rights. Do not commit secrets, API keys, or `.env` files.
