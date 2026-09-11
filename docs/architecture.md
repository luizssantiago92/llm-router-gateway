# Architecture

LLM Router Gateway is an async FastAPI reverse proxy in front of local and cloud chat models. Clients never pick a provider; the gateway caches, classifies, routes, and fails over.

Status: **implemented** (T1–T13). Independent `/verify` returned FAIL (weak assertions; see [`validation.md`](../.specs/features/001-llm-router-gateway/validation.md)). Binding requirements: [`spec.md`](../.specs/features/001-llm-router-gateway/spec.md). How: [`design.md`](../.specs/features/001-llm-router-gateway/design.md). Product kickoff: [`prd.md`](../prd.md).

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
| (latency <10 ms) |             | (complexity)          |
+------------------+             +-----------+-----------+
                                             |
                      +----------------------+----------------------+
                      | (simple)                                    | (complex)
                      v                                             v
           +--------------------+                        +--------------------+
           | Local provider     |                        | Cloud provider     |
           | (Ollama; vLLM-ready)|                       | (OpenAI; Anthropic-ready)
           +---------+----------+                        +---------+----------+
                     |                                             |
                     +----------------------+----------------------+
                                            |
                                  2. Write response to Redis
                                            |
                                            v
                                  Return final response
```

On cache miss, a **5xx or timeout** on the primary provider triggers **one** hop to the opposite tier (local ↔ cloud) before the request fails. Error responses are not cached.

## Components

| Component | Path | Responsibility |
| --- | --- | --- |
| FastAPI app | `app/main.py`, `app/api/` | OpenAI-shaped HTTP facade; Pydantic v2 validation |
| Settings | `app/settings.py` | Env-only config; no `load_dotenv` |
| Cache layer | `app/cache/service.py` | SHA-256 key over canonical `messages` + `temperature` + `max_tokens`; Redis TTL (default 3600s) |
| Evaluator | `app/routing/evaluator.py` | Word-count **or** keyword match → simple vs complex |
| Router | `app/routing/router.py` | Primary provider then one opposite-tier hop |
| Local adapter | `app/providers/ollama.py` | Default Ollama (Llama 3 8B class); `name="local"` |
| Cloud adapter | `app/providers/openai.py` | Default OpenAI; `name="cloud"` |
| Health | `app/api/health.py` | Process + Redis + each configured upstream |

vLLM and Anthropic happy-path adapters stay protocol-only in v1 (deferred).

## Observability

Every completion returns:

- JSON: `cached`, `latency_ms`, `provider`
- Headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`

## Ship unit

Docker Compose runs the FastAPI service (`api`) and Redis (`redis`) in isolation. Kubernetes, Helm, and Terraform are out of scope for v1. Secrets (cloud API keys, local runtime URLs) come from environment variables only. Ollama is an external runtime referenced by `OLLAMA_BASE_URL`.

## Surfaces

Declared in [`design.md`](../.specs/features/001-llm-router-gateway/design.md) and implemented in this Execute:

- **Ship Surface** — health/OpenAPI, env/secrets, Compose deploy unit, CI (`pytest`), rollback
- **AI Surface** — chat-routing capability, providers, eval harness (`tests/eval/`), PII policy, fallback/degrade, cost guard
