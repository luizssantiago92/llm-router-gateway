# API (demo + domain REQ-001–REQ-022)

OpenAI-shaped facade. Streaming is rejected with HTTP 422 (`stream: true`). Demo callers authenticate chat with `X-API-Key` or `Authorization: Bearer`. Cloud upstream is Gemini (free-tier oriented).

Product: [README](../../README.md) · [Overview](Overview.md). Domain: [domain spec](../history/domain-spec.md).

Process factory: `app.main:build_default_app` (Uvicorn `--factory`). The factory does not open sockets. A lifespan opens the async Redis client and one HTTP client per upstream on startup, and closes them on shutdown, before the process accepts traffic and after in-flight requests finish. Routes are registered on `create_app(...)` for tests that inject fakes. Injected objects are not replaced or closed by that lifespan. Request handlers receive settings, Redis, and the provider clients through FastAPI dependencies.

## `POST /v1/chat/completions`

**Auth:** `X-API-Key` or `Authorization: Bearer <GATEWAY_API_KEY>` must match `GATEWAY_API_KEY`. Otherwise HTTP **401** (`unauthorized`), including when the body is missing, invalid JSON, fails validation, or is larger than the size cap. The credential is compared as UTF-8 bytes, and a missing credential does not read the body. Health does not use either header. OpenAPI lists both schemes under `securitySchemes`.

**Size:** after a valid credential, `Content-Length` or a chunked body above the cap is HTTP **413** (`payload_too_large`) and is not parsed. The default cap is 256 KiB (`MAX_BODY_BYTES`). A missing credential on that same body is still **401**.

**Fields:** `role` is `system`, `user`, or `assistant`. Each `content` is 1–32,000 characters (`MAX_MESSAGE_CHARS`). `messages` has 1–50 items (`MAX_MESSAGES`). Combined `content` is at most 64,000 characters (`MAX_TOTAL_MESSAGE_CHARS`). `temperature`, when present, is 0–2; when omitted, providers still receive `1.0`. `max_tokens`, when present, is 1–4096. Settings can lower these ceilings and cannot raise them. Out-of-range values are HTTP **422**.

**Quota:** each cache **miss** consumes one unit of the caller's daily limit (`CHAT_DAILY_LIMIT`, default 5). Cache **hits** do not consume. Exhausted → HTTP **429** (`rate_limit_reached`). Upstream dual-fail refunds the consumed unit. The Redis bucket resets at **UTC midnight**.

OpenAI Chat Completions-compatible body: `messages`, `temperature`, `max_tokens`. Additional OpenAI fields are accepted and ignored.

Gateway-specific response fields (in addition to a standard completion payload):

| Field | Type | Meaning |
| --- | --- | --- |
| `cached` | boolean | Redis exact-match hit |
| `latency_ms` | number | Gateway hop latency |
| `provider` | string | Adapter that produced the completion (`local` or `cloud`). Cache hits reuse the stored origin; they do not set `provider` to `cache`. |

Mirrored headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`.

### Behavior

| Condition | Result |
| --- | --- |
| Cache hit | Stored completion, `cached: true`, target latency <10 ms |
| Cache miss, success | Upstream completion, write Redis, `cached: false` |
| Primary 5xx or timeout | One retry on the secondary provider; success is cached |
| Both providers fail | HTTP 502; **not** cached; quota refunded. Remaining `ProviderError` (including adapter-mapped Gemini 4xx) also surfaces as 502 |
| Missing/invalid `X-API-Key` or Bearer token, even if the body is invalid or oversized | HTTP 401 |
| Authenticated body over the size cap | HTTP 413 |
| Daily quota exhausted | HTTP 429 |
| Invalid body, including out-of-range fields | HTTP 422 (Pydantic) |
| `stream: true` | HTTP 422 |

Cache key: SHA-256 of a canonical serialization of `messages` + `temperature` + `max_tokens`. The routed model name is not part of the key.

## `GET /health`

| Redis | Upstreams | HTTP | Payload `status` |
| --- | --- | --- | --- |
| Up | All reachable | 200 | `ok` |
| Up | At least one down | 200 | `degraded` |
| Down | — | 503 | `down` |

The process can still serve cache hits when a single upstream is down, as long as Redis is healthy. Without Ollama, expect `degraded` while Gemini remains up. `GET /health` does **not** require `X-API-Key`.

Interactive OpenAPI: `GET /docs` (FastAPI default).

**Go deeper:** [Quick start](Quick-start.md) · [How it works](How-it-works.md)
