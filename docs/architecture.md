# Architecture

LLM Router Gateway is an async FastAPI reverse proxy in front of local and cloud chat models. Clients never pick a provider. The gateway caches exact matches, classifies the prompt, routes, and fails over once.

This page is the system description. The HTTP contract is [API](api.md). Running and testing it is [Operations](operations.md). Archived kickoff material stays in [history](history/).

Status: demo on Compose (Gemini, optional Ollama, Redis quota). Academic / lab reference, not a production chatbot.

## Request path

```text
POST /v1/chat/completions
        X-API-Key
              |
              v
     +--------+--------+
     |  SHA-256 cache  |
     +--------+--------+
          |         |
     (hit)|         |(miss)
          v         v
     return Redis   consume daily quota
                    |
                    v
              classify prompt
               /          \
         simple            complex
            v                  v
        Ollama              Gemini
            \                  /
             \   5xx/timeout  /
              \   one hop    /
               +------+------+
                      |
                      v
              store success in Redis
```

1. Chat requires `X-API-Key` or `Authorization: Bearer`. Health does not. A missing or invalid credential is HTTP 401 and the body is not read.
2. The cache key is SHA-256 of canonical `messages`, `temperature`, and `max_tokens`. Omitted temperature is stored as `1.0`. `top_p`, `stop`, and a caller-selected Gemini model id are added only when the request sets them.
3. A hit returns the stored completion. Quota is not consumed. The stored `provider` stays `local` or `cloud`.
4. A miss consumes one daily quota unit, then classifies. More than 150 words, or a keyword (`code`, `algorithm`, `implement`, `debug`, `function`, `class`, `step by step`, `reason`), is complex and starts on Gemini. Anything else is simple and starts on Ollama.
5. A retryable primary failure (timeout, HTTP 5xx, or an unexpected exception) hops once to the other tier. A non-retryable 4xx does not hop. Both failures return HTTP 502. Error responses are not cached.
6. Cache Redis errors fail open (a read error is a miss; a write error still returns the completion). Quota Redis errors fail closed with HTTP 503 and do not call a provider.

`PROVIDER_MODE=demo` replaces both adapters with in-process echoes. Live mode, the default, still calls Ollama and Gemini.

## Components

| Component | Path | Responsibility |
| --- | --- | --- |
| FastAPI app | `app/main.py`, `app/runtime.py`, `app/deps.py`, `app/api/` | OpenAI-shaped facade. A lifespan owns the Redis client and the upstream HTTP clients. |
| Settings | `app/settings.py` | Env-only config. No `load_dotenv`. |
| Cache | `app/cache/service.py` | SHA-256 key and Redis TTL (default 3600s). |
| Evaluator | `app/routing/evaluator.py` | Word count or keyword match. |
| Router | `app/routing/router.py` | Primary provider, then one opposite-tier hop. |
| Local adapter | `app/providers/ollama.py` | Optional Ollama (`llama3`). `name="local"`. |
| Cloud adapter | `app/providers/gemini.py` | Gemini. The key goes in the `x-goog-api-key` header. `name="cloud"`. |
| Demo adapters | `app/providers/demo.py` | Echo providers used only when `PROVIDER_MODE=demo`. |
| Quota | `app/quota/daily.py` | Daily Redis bucket. The id is a scrypt digest of the caller credential. |
| Health | `app/api/health.py` | `GET /health`, `GET /health/live`, `GET /health/ready`. |
| Access log and metrics | `app/observability.py`, `app/metrics.py` | `X-Request-Id`, one JSON access line, `GET /metrics`. |

## Observability

Every completion returns JSON `cached`, `latency_ms`, and `provider`, plus headers `X-Cache`, `X-Latency-Ms`, and `X-Provider`. Every HTTP response returns `X-Request-Id`. One JSON access line records the request id, method, route template, status, and latency. It leaves out the submitted message text and credential headers. `GET /metrics` exposes unauthenticated Prometheus counters. The scrape itself is counted after the body is written.

## Ship unit

Docker Compose runs `api` and `redis`. Kubernetes, Helm, and Terraform are out of scope.

- The API is published on `127.0.0.1:8000` only. Redis is published on `127.0.0.1:6379` only.
- Redis requires `REDIS_PASSWORD`, is pinned by digest, and must answer `PING` before the API starts.
- Both services restart unless stopped.
- The API image runs as non-root user `app` from a digest-pinned `python:3.12-slim` base and probes `GET /health/live`.
- Ollama is not in Compose. It is an optional host process. When it is down, health is `degraded` and simple prompts fall back to Gemini.
- `host.docker.internal` maps to `host-gateway` so Linux Docker Engine can reach that host process.

## Limitations

These limits stay in force: Gemini free-tier rate limits still apply, a shared `X-API-Key` is not multi-tenant auth, and a green pytest run is not proof of production quality.

| Item | Status |
| --- | --- |
| Streaming (`stream: true`) | Deferred. Rejected with HTTP 422. |
| Production edge auth and multi-tenant quotas | Deferred. One shared key and one daily Redis bucket. |
| Semantic or embedding cache | Deferred. Exact-match SHA-256 only. |
| RAG, tools, and function calling | Deferred. |
| Paid OpenAI or other paid cloud happy path | Deferred. |
| Kubernetes, Helm, and Terraform | Deferred. Compose is the ship unit. |
| Hosted deploy | Not started. |
| Ollama inside Compose | Not started. Ollama stays external. |
| Chat UI | Not started. API only. |

Patterns may be lifted into [Gold Queen](https://github.com/luizssantiago92/gold-queen-api). This repository stays the demo.

Archived requirements: [domain spec](history/domain-spec.md) (REQ-001–REQ-022), [feature design](history/design.md), [kickoff](history/PRD.pt-BR.md).
