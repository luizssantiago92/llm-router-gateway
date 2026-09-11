# Spec: 001-llm-router-gateway

## Goal

Internal applications send OpenAI-compatible chat completions to one FastAPI gateway that serves Redis exact-match hits, routes misses by prompt complexity to a local or cloud model, fails over once on 5xx or timeout, and returns cache, latency, and provider origin on every response.

## Complexity: Complex

## Requirements

### REQ-001: Chat completions facade
- **Acceptance Criteria**: WHEN a client sends `POST /v1/chat/completions` with a body that includes `messages`, `temperature`, and `max_tokens` THEN the system SHALL accept the request using an OpenAI Chat Completions-compatible schema and SHALL return a completion JSON object on success

### REQ-002: Strict request validation
- **Acceptance Criteria**: WHEN the request body fails Pydantic v2 validation THEN the system SHALL respond with HTTP 422 and SHALL NOT call Redis SET, local providers, or cloud providers

### REQ-003: Streaming rejected
- **Acceptance Criteria**: WHEN the request sets `stream` to true THEN the system SHALL reject the request with HTTP 422 and SHALL NOT call an upstream provider

### REQ-004: Health endpoint
- **Acceptance Criteria**: WHEN Redis is reachable and every configured upstream health check succeeds THEN `GET /health` SHALL return HTTP 200 with JSON field `status` equal to `ok`
- WHEN Redis is reachable and at least one configured upstream health check fails THEN `GET /health` SHALL return HTTP 200 with JSON field `status` equal to `degraded`
- WHEN Redis is unreachable THEN `GET /health` SHALL return HTTP 503

### REQ-005: Exact-match cache key
- **Acceptance Criteria**: WHEN the gateway looks up or stores a completion THEN the system SHALL use SHA-256 over a canonical serialization of `messages`, `temperature`, and `max_tokens` as the Redis key and SHALL NOT include the routed model name in that key

### REQ-006: Cache hit
- **Acceptance Criteria**: WHEN Redis contains a value for the request cache key THEN the system SHALL return that stored completion with JSON `cached` equal to true, SHALL include numeric `latency_ms`, and SHALL NOT call a local or cloud LLM provider

### REQ-007: Cache miss write
- **Acceptance Criteria**: WHEN Redis has no value for the request cache key and an upstream provider returns a successful completion THEN the system SHALL write that completion to Redis with TTL from `CACHE_TTL_SECONDS` (default 3600) before returning JSON `cached` equal to false

### REQ-008: Errors are not cached
- **Acceptance Criteria**: IF the upstream outcome is HTTP 4xx, HTTP 5xx, or a timeout THEN the system SHALL NOT write a Redis value for that request key

### REQ-009: Complexity classification
- **Acceptance Criteria**: WHEN a cache miss occurs THEN the system SHALL classify the prompt as complex IF the approximate word count of concatenated message contents is greater than `COMPLEXITY_WORD_THRESHOLD` (default 150) OR the contents match at least one configured keyword (`code`, `algorithm`, `implement`, `debug`, `function`, `class`, `step by step`, `reason`); otherwise the system SHALL classify it as simple

### REQ-010: Simple route uses local primary
- **Acceptance Criteria**: WHEN the prompt is classified simple THEN the system SHALL send the completion request to the local provider adapter first (default Ollama, Llama 3 8B class)

### REQ-011: Complex route uses cloud primary
- **Acceptance Criteria**: WHEN the prompt is classified complex THEN the system SHALL send the completion request to the cloud provider adapter first (default OpenAI)

### REQ-012: One-hop fallback
- **Acceptance Criteria**: WHEN the primary provider returns HTTP 5xx or exceeds `UPSTREAM_TIMEOUT_SECONDS` (default 30) THEN the system SHALL retry the same request once against the opposite-tier provider (simple: local then cloud; complex: cloud then local) and SHALL NOT retry a third time

### REQ-013: Dual-provider failure
- **Acceptance Criteria**: IF both the primary and the secondary provider return HTTP 5xx or timeout THEN the system SHALL respond with HTTP 502 and SHALL NOT write the error body to Redis

### REQ-014: Observability on completions
- **Acceptance Criteria**: WHEN the gateway returns a successful `POST /v1/chat/completions` body THEN the JSON SHALL include `cached` (boolean), `latency_ms` (number), and `provider` (string), and the response SHALL include headers `X-Cache`, `X-Latency-Ms`, and `X-Provider` whose values match those fields

### REQ-015: Async I/O stack
- **Acceptance Criteria**: WHEN the gateway handles `POST /v1/chat/completions` or `GET /health` THEN the system SHALL perform HTTP and Redis I/O with FastAPI, asyncio, httpx, and redis-py async (no blocking Redis or HTTP clients on those paths)

### REQ-016: Secrets from the environment
- **Acceptance Criteria**: WHEN the process starts THEN the system SHALL read `REDIS_URL`, local base URL, and cloud API credentials from environment variables and SHALL NOT read those values from files committed in git

### REQ-017: Compose ship unit
- **Acceptance Criteria**: WHEN an operator runs the project `docker-compose.yml` THEN the system SHALL start the FastAPI service and a Redis instance as isolated Compose services

### REQ-018: Automated coverage
- **Acceptance Criteria**: WHEN the test suite runs with pytest-asyncio THEN it SHALL include passing tests for cache hit, cache miss, simple routing, complex routing, fallback after 5xx, fallback after timeout, and health `ok` / `degraded` / Redis-down

## Non-Functional Requirements

- WHEN a cache hit is served THEN the system SHALL exclude upstream LLM time from `latency_ms` and SHALL target gateway processing under 10 milliseconds on a local Redis (PRD latency goal)
- The system SHALL validate all public request and response models with Pydantic v2 (RNF-02, C-003)
- The system SHALL NOT log secret values or raw API keys (C-006)
- Business target: routing simple and repeated prompts away from the cloud SHALL reduce paid-token volume relative to an all-cloud baseline (PRD ≥30 percent); the Verify eval harness records token destination counts, not a production billing integration

## Test Plan

| Scenario | REQ | Assertion |
| --- | --- | --- |
| Valid completion, empty cache, simple prompt | REQ-001, REQ-007, REQ-010 | Local adapter called once; Redis SET; `cached` false |
| Repeat identical `messages`+`temperature`+`max_tokens` | REQ-005, REQ-006 | No provider call; `cached` true; headers match JSON |
| Invalid body | REQ-002 | HTTP 422; no Redis SET; no provider call |
| `stream: true` | REQ-003 | HTTP 422 |
| Word count above threshold or keyword match | REQ-009, REQ-011 | Cloud adapter is primary |
| Primary 5xx | REQ-012 | Opposite-tier adapter called once; success cached |
| Primary timeout (30s bound, fake clock or short test timeout) | REQ-012 | Opposite-tier adapter called once |
| Primary and secondary fail | REQ-013 | HTTP 502; no Redis SET of the error |
| Health all up | REQ-004 | HTTP 200 `status=ok` |
| Health upstream down, Redis up | REQ-004 | HTTP 200 `status=degraded` |
| Health Redis down | REQ-004 | HTTP 503 |
| Observability | REQ-014 | JSON + `X-Cache` / `X-Latency-Ms` / `X-Provider` |

Test files (planned): `tests/test_chat_completions.py`, `tests/test_cache.py`, `tests/test_routing.py`, `tests/test_fallback.py`, `tests/test_health.py`. Providers and Redis SHALL be faked in unit tests; live provider calls are out of the default suite.

## Assumptions

- Caller authentication is absent in v1 (brief D-002; internal network)
- Default local adapter is Ollama; default cloud adapter is OpenAI; vLLM and Anthropic are adapter interfaces only until a later spec adds them to the happy path (D-006)
- Canonical cache serialization is UTF-8 JSON with sorted keys for the three hashed fields (D-003)
- `latency_ms` measures gateway wall time for the request, not the provider's reported usage
- Health checks for Ollama and OpenAI are HTTP reachability probes, not model-quality probes
- Keyword matching is case-insensitive substring match against concatenated message contents

## Out of Scope

- Streaming completions (`text/event-stream`)
- Edge API keys, SSO, OAuth, multi-tenancy
- Semantic or embedding cache
- Prompt playground, admin UI, billing dashboards
- Per-tenant quotas and rate limiting
- RAG, tool-use, MCP agents, fine-tuning, embeddings APIs
- Kubernetes, Helm, Terraform
- Native Anthropic Messages request schema as the public contract
- Production APM or live LLM tracing platforms
