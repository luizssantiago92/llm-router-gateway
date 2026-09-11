# Domain: llm-router-gateway

> Seeded by archive-feature from `001-llm-router-gateway`.

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
