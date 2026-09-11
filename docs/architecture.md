# Architecture

LLM Router Gateway is an async FastAPI reverse proxy in front of local and cloud chat models. Clients never pick a provider; the gateway caches, classifies, routes, and fails over.

Status: **spec and design drafted**, not implemented. Binding requirements: [`spec.md`](../.specs/features/001-llm-router-gateway/spec.md). How: [`design.md`](../.specs/features/001-llm-router-gateway/design.md). Product kickoff: [`prd.md`](../prd.md).

## Request path

```text
               +-----------------------+
               |  Cliente / Aplicação  |
               +-----------+-----------+
                           |
            POST /v1/chat/completions
                           |
                           v
               +-----------------------+
               |  FastAPI Router (Async)|
               +-----------+-----------+
                           |
             1. Checar Cache SHA-256
                           |
          +----------------+----------------+
          | (Cache Hit)                     | (Cache Miss)
          v                                 v
+------------------+             +-----------------------+
|  Retorna Redis   |             | Evaluator Service     |
|  (Latência <10ms)|             | (Analisa Complexidade)|
+------------------+             +-----------+-----------+
                                             |
                      +----------------------+----------------------+
                      | (Baixa Complexidade)                        | (Alta Complexidade)
                      v                                             v
           +--------------------+                        +--------------------+
           | Provedor Local     |                        | Provedor Cloud     |
           | (Ollama / vLLM)    |                        | (OpenAI / Anthropic|
           +---------+----------+                        +---------+----------+
                     |                                             |
                     +----------------------+----------------------+
                                            |
                                  2. Grava Resposta no Redis
                                            |
                                            v
                                  Retorna Resposta Final
```

On cache miss, a **5xx or timeout** on the primary provider triggers **one** hop to the opposite tier (local ↔ cloud) before the request fails. Error responses are not cached.

## Components (planned)

| Component | Responsibility |
| --- | --- |
| FastAPI app | OpenAI-shaped HTTP facade, Pydantic v2 validation |
| Cache layer | SHA-256 key over canonical `messages` + `temperature` + `max_tokens`; Redis TTL (default 3600s) |
| Evaluator | Approximate size **or** keyword match → simple vs complex |
| Local adapter | Default Ollama (Llama 3 8B class); vLLM-ready |
| Cloud adapter | Default OpenAI; Anthropic-ready behind the same facade |
| Health | Process + Redis + each configured upstream |

## Observability

Every completion returns:

- JSON: `cached`, `latency_ms`, provider/model origin
- Headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`

## Ship unit

Docker Compose runs the FastAPI service and Redis in isolation. Kubernetes, Helm, and Terraform are out of scope for v1. Secrets (cloud API keys, local runtime URLs) come from environment variables only.

## Surfaces for later Design

The `python-platform` preset will require, when those paths appear in tasks:

- **Ship Surface** — health/OpenAPI, env/secrets, Compose deploy unit, CI, rollback
- **AI Surface** — chat-routing capability, providers, eval harness, PII policy, fallback/degrade, cost guard
