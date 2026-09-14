# Architecture

LLM Router Gateway is an async FastAPI reverse proxy in front of local and cloud chat models. Clients never pick a provider; the gateway caches, classifies, routes, and fails over.

Product overview: [README](../../README.md) · [Overview](Overview.md). Domain truth: [`.specs/domains/llm-router-gateway/spec.md`](../../.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022). Backlog: [Limitations](Limitations.md) · [Still open](../../README.md#still-open-agents-read-this).

Status: **demo shipped** on Compose (Gemini + optional Ollama + quota).

## Request path

```text
               +-----------------------+
               |  Client / application |
               +-----------+-----------+
                           |
            POST /v1/chat/completions
                           |
                           v
               +-----------------------+
               | FastAPI router (async)|
               +-----------+-----------+
                           |
             1. SHA-256 cache lookup
                           |
          +----------------+----------------+
          | (cache hit)                     | (cache miss)
          v                                 v
+------------------+             +-----------------------+
| Return Redis     |             | Evaluator service     |
| (target <10 ms)  |             | (complexity)          |
+------------------+             +-----------+-----------+
                                             |
                      +----------------------+----------------------+
                      | (simple)                                    | (complex)
                      v                                             v
           +--------------------+                        +--------------------+
           | Local provider     |                        | Cloud provider     |
           | (Ollama; optional) |                        | (Gemini; free-tier)|
           +---------+----------+                        +---------+----------+
                     |                                             |
                     +----------------------+----------------------+
                                            |
                                  2. Write response to Redis
                                            |
                                            v
                                  Return final response
```

On cache miss, a **5xx or timeout** on the primary provider triggers **one** hop to the opposite tier (local ↔ cloud) before the request fails. Error responses are not cached. Non-retryable 4xx from the primary is not hopped (HTTP 502 at the route).

## Components

| Component | Path | Responsibility |
| --- | --- | --- |
| FastAPI app | `app/main.py`, `app/api/` | OpenAI-shaped HTTP facade; Pydantic v2 validation |
| Settings | `app/settings.py` | Env-only config; no `load_dotenv` |
| Cache layer | `app/cache/service.py` | SHA-256 key over canonical `messages` + `temperature` + `max_tokens`; Redis TTL (default 3600s) |
| Evaluator | `app/routing/evaluator.py` | Word-count **or** keyword match → simple vs complex |
| Router | `app/routing/router.py` | Primary provider then one opposite-tier hop |
| Local adapter | `app/providers/ollama.py` | Optional Ollama (`llama3` class); `name="local"` |
| Cloud adapter | `app/providers/gemini.py` | Default Gemini (`GEMINI_API_KEY`); `name="cloud"` |
| Quota | `app/quota/daily.py` | Redis daily bucket per `X-API-Key` (cache hits free) |
| Health | `app/api/health.py` | Process + Redis + each configured upstream |

## Observability

Every completion returns JSON `cached`, `latency_ms`, `provider` and headers `X-Cache`, `X-Latency-Ms`, `X-Provider`. Cache hits reuse the stored origin (`local` or `cloud`).

## Ship unit

Docker Compose runs `api` and `redis` in isolation. Kubernetes, Helm, and Terraform are out of scope. Secrets come from environment variables only. Ollama is an optional external runtime (`OLLAMA_BASE_URL`). When it is unreachable, health is `degraded` and simple prompts fall back to Gemini. The `api` service maps `host.docker.internal` to the Docker host gateway so Linux Engine can reach host Ollama.

## Surfaces

Declared in archived [`design.md`](../../.specs/features/001-llm-router-gateway/design.md):

- **Ship Surface** — health/OpenAPI, env/secrets, Compose deploy unit, CI (`pytest`), rollback
- **AI Surface** — chat-routing capability, providers, eval harness (`tests/eval/`), PII policy, fallback/degrade, cost guard

**Go deeper:** [How it works](How-it-works.md) · [API](API.md) · [concepts](concepts.md)
