# API (v1 + demo auth/quota)

OpenAI-shaped facade. Streaming is rejected with HTTP 422 (`stream: true`). Demo callers must send `X-API-Key`. Cloud upstream is Gemini (free-tier oriented). Historical REQs: [`spec.md`](../.specs/features/001-llm-router-gateway/spec.md).

Process factory: `app.main:build_default_app` (Uvicorn `--factory`). Routes are registered on `create_app(...)` for tests that inject fakes.

## `POST /v1/chat/completions`

**Auth:** header `X-API-Key` must match `GATEWAY_API_KEY` → otherwise HTTP **401** (`unauthorized`).

**Quota:** each cache **miss** consumes one unit of the caller's daily limit (`CHAT_DAILY_LIMIT`, default 5). Cache **hits** do not consume. Exhausted → HTTP **429** (`rate_limit_reached`). Upstream dual-fail refunds the consumed unit.

OpenAI Chat Completions-compatible body: `messages`, `temperature`, `max_tokens`. Additional OpenAI fields may be accepted and ignored if unused.

Gateway-specific response fields (in addition to a standard completion payload):

| Field | Type | Meaning |
| --- | --- | --- |
| `cached` | boolean | Redis exact-match hit |
| `latency_ms` | number | Gateway hop latency |
| `provider` | string | Adapter that served the completion (`local`, `cloud`, or `cache`) |

Mirrored headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`.

### Behavior

| Condition | Result |
| --- | --- |
| Cache hit | Stored completion, `cached: true`, target latency <10 ms |
| Cache miss, success | Upstream completion, write Redis, `cached: false` |
| Primary 5xx or timeout | One retry on the secondary provider; success is cached |
| Both providers fail | HTTP 502; **not** cached; quota refunded |
| Missing/invalid `X-API-Key` | HTTP 401 |
| Daily quota exhausted | HTTP 429 |
| Invalid body | HTTP 422 (Pydantic) |
| `stream: true` | HTTP 422 |

Cache key: SHA-256 of a canonical serialization of `messages` + `temperature` + `max_tokens`. The routed model name is not part of the key.

## `GET /health`

| Redis | Upstreams | HTTP | Payload `status` |
| --- | --- | --- | --- |
| Up | All reachable | 200 | `ok` |
| Up | At least one down | 200 | `degraded` |
| Down | — | 503 | `down` |

The process can still serve cache hits when a single upstream is down, as long as Redis is healthy.
