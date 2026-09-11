# Design: 001-llm-router-gateway

## Context

Greenfield FastAPI service. No application package exists yet. The spec requires an OpenAI-shaped HTTP facade, Redis exact-match cache, complexity routing, one-hop fallback, Compose (app + Redis), and pytest-asyncio coverage (REQ-001–REQ-018). The `python-platform` preset requires Ship Surface and AI Surface because Compose and LLM adapters will appear in tasks.

## Decision

Implement a single async FastAPI process with three internal ports: a Pydantic request/response boundary, a Redis cache keyed by SHA-256 of canonical `messages`+`temperature`+`max_tokens`, and a router that classifies the prompt then calls a **Provider** protocol. Default adapters: Ollama (local) and OpenAI (cloud). Fallback is one call to the other adapter on HTTP 5xx or timeout. Tests fake Redis and both adapters; Compose is the local ship unit.

## Alternatives considered

| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| A. Sync Flask + redis blocking | Smaller tutorial surface | Violates RNF-01 / REQ-015 | Rejected |
| B. Library-only SDK, no HTTP | Simpler process | PRD requires HTTP facade and health | Rejected |
| C. FastAPI async gateway + Provider protocol + Redis (chosen) | Matches PRD, testable fakes, Compose | Two upstreams to operate | Selected |
| D. Embed a local GGUF in-process | No Ollama daemon | Heavy image, not the named local runtime | Rejected for v1 |

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Keyword classifier misfires (simple treated as complex) | Extra cloud cost | Configurable keyword list and word threshold; unit tests for both branches |
| Ollama or OpenAI slow beyond 30s | Fallback hop adds latency | Single retry only (REQ-012); timeout from env |
| Cache key canonicalization drift | False misses or mixed completions | One serializer module; tests pin the hex digest for a fixture payload |
| Secrets leaked in logs or git | Credential exposure | Env-only config; tests assert `.env` is gitignored; no key values in fixtures |
| <10 ms cache-hit SLO flaky in CI | False Verify failures | Unit tests assert no provider call on hit; SLO documented as NFR, not a hard CI bound |

## Approach

Layer the app as `api` (routes) → `cache` → `router` → `providers`. Routes never import httpx OpenAI/Ollama clients directly. The router owns classify → primary → fallback. Cache wraps the router so hits skip classification.

## Components

| Component | Responsibility | New or reuse | Serves |
| --- | --- | --- | --- |
| FastAPI routes | `/v1/chat/completions`, `/health`, header injection | new `app/api/` | REQ-001, REQ-002, REQ-003, REQ-004, REQ-014 |
| Pydantic v2 schemas | Request/response models | new `app/schemas/` | REQ-001, REQ-002, REQ-014 |
| Cache service | Canonical JSON, SHA-256, Redis GET/SET with TTL | new `app/cache/` | REQ-005, REQ-006, REQ-007, REQ-008 |
| Evaluator | Word count + keyword match | new `app/routing/evaluator.py` | REQ-009 |
| Router | Primary + one fallback hop | new `app/routing/router.py` | REQ-010, REQ-011, REQ-012, REQ-013 |
| Provider protocol | `complete(messages, …) -> Completion` | new `app/providers/base.py` | REQ-010, REQ-011 |
| Ollama adapter | HTTP to `OLLAMA_BASE_URL` | new `app/providers/ollama.py` | REQ-010 |
| OpenAI adapter | HTTP to OpenAI Chat Completions | new `app/providers/openai.py` | REQ-011 |
| Settings | Env-backed config, no secrets in git | new `app/settings.py` | REQ-016, REQ-012 TTL/timeout |
| Compose | `api` + `redis` services | new `docker-compose.yml` | REQ-017 |
| Tests | pytest-asyncio fakes | new `tests/` | REQ-018 |

## Data Flow

| Step | From | To | Payload / notes |
| ---: | --- | --- | --- |
| 1 | Client | FastAPI | `POST /v1/chat/completions` JSON |
| 2 | FastAPI | Pydantic | Validate; 422 on failure or `stream=true` |
| 3 | API | Cache | SHA-256 key of canonical triple |
| 4a | Cache | Client | Hit: stored JSON + `cached=true` + headers; stop |
| 4b | Cache | Evaluator | Miss: classify simple vs complex |
| 5 | Router | Primary provider | Local if simple, cloud if complex |
| 6 | Router | Secondary provider | Only on 5xx or timeout; one hop |
| 7 | Router | Cache | SET successful completion with TTL |
| 8 | API | Client | JSON + `X-Cache`, `X-Latency-Ms`, `X-Provider` |

## Decisions

### AD-003: In-process Provider protocol
- **Chosen**: Protocol/ABC with Ollama and OpenAI adapters
- **Rejected**: Direct OpenAI SDK calls from the route because fallback and tests need a seam

### AD-004: Fake adapters in unit tests
- **Chosen**: In-memory fakes plus fakeredis or a Redis fake
- **Rejected**: Live network tests in the default suite (slow, paid, flaky)

## Out of Scope for This Design

- Streaming workers, Kubernetes manifests, Anthropic adapter implementation beyond the protocol stub

## Ship Surface

| Field | Value |
| --- | --- |
| API / contract | `POST /v1/chat/completions`, `GET /health` (OpenAPI from FastAPI) |
| Migrations | N/A (no SQL datastore) |
| Env / secrets | `REDIS_URL`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, `CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, `UPSTREAM_TIMEOUT_SECONDS` — values from env, never git |
| Deploy unit | Docker Compose services `api` and `redis` |
| CI | `pytest` (asyncio) must pass before merge; optional `docker compose config` in `quality.checks` |
| Rollback | Redeploy previous Compose image tag / git SHA; flush Redis only if a bad cache schema shipped |
| Observability | JSON `cached`, `latency_ms`, `provider`; headers `X-Cache`, `X-Latency-Ms`, `X-Provider`; structured logs without secrets |

## AI Surface

| Field | Value |
| --- | --- |
| Capability | Chat completion routing (no RAG, no tools) |
| Model / provider | Local default Llama 3 8B class via Ollama; cloud default OpenAI chat model from env `OPENAI_MODEL` |
| Tools / MCP scope | Deny all tools/MCP in v1 |
| Eval harness | `pytest tests/eval/test_routing_eval.py` plus unit routing tests; golden prompts for simple vs complex; `pytest -m "not live"` default |
| PII / data policy | Do not log full prompts in production logs; no prompt corpora committed with PII; secrets never sent in test fixtures |
| Fallback / degrade | On 5xx or timeout, one hop to the opposite-tier provider; if both fail, HTTP 502 and no cache write |
| Cost guard | Prefer local on simple prompts; cache exact repeats; no third retry; execution-policy budgets apply during agent Execute |
