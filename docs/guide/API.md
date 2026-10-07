# API (demo + domain REQ-001–REQ-022)

OpenAI-shaped facade. Streaming is rejected with HTTP 422 (`stream: true`). Demo callers authenticate chat with `X-API-Key` or `Authorization: Bearer`. Cloud upstream is Gemini (free-tier oriented).

Product: [README](../../README.md) · [Overview](Overview.md). Domain: [domain spec](../history/domain-spec.md).

Process factory: `app.main:build_default_app` (Uvicorn `--factory`). The factory does not open sockets. A lifespan opens the async Redis client and one HTTP client per upstream on startup, and closes them on shutdown, before the process accepts traffic and after in-flight requests finish. Routes are registered on `create_app(...)` for tests that inject fakes. Injected objects are not replaced or closed by that lifespan. Request handlers receive settings, Redis, and the provider clients through FastAPI dependencies.

## `POST /v1/chat/completions`

**Auth:** `X-API-Key` or `Authorization: Bearer <GATEWAY_API_KEY>` must match `GATEWAY_API_KEY`. Otherwise HTTP **401** (`unauthorized`), including when the body is missing, invalid JSON, fails validation, or is larger than the size cap. The credential is compared as UTF-8 bytes, and a missing credential does not read the body. Health does not use either header. OpenAPI lists both schemes under `securitySchemes`.

**Size:** after a valid credential, `Content-Length` or a chunked body above the cap is HTTP **413** (`payload_too_large`) and is not parsed. The default cap is 256 KiB (`MAX_BODY_BYTES`). A missing credential on that same body is still **401**.

**Fields:** `role` is `system`, `user`, or `assistant`. Each `content` is 1–32,000 characters (`MAX_MESSAGE_CHARS`). `messages` has 1–50 items (`MAX_MESSAGES`). Combined `content` is at most 64,000 characters (`MAX_TOTAL_MESSAGE_CHARS`). `temperature`, when present, is 0–2. When it is omitted, the cache key and the local adapter use `1.0`, and the Gemini generation config leaves `temperature` out. An explicit `0` is still sent. `top_p`, when present, is 0–1, is copied to Gemini `topP`, and is part of the cache key. When `top_p` is omitted, the cache key stays the same. `stop` is a string or a list of 1–5 strings, each 1–256 characters; it is forwarded as Gemini `stopSequences` and included in the cache key. `model` selects the cloud model for that call only when it is a Gemini id (`gemini` plus letters, digits, `.`, `_`, and `-`, at most 128 characters) and that id is then part of the cache key. Any other model name keeps the configured cloud model and stays out of the cache key. `max_tokens`, when present, is 1–4096. Settings can lower the message, temperature, and `max_tokens` ceilings and cannot raise them. Out-of-range values are HTTP **422**.

**Quota:** each cache **miss** consumes one unit of the caller's daily limit (`CHAT_DAILY_LIMIT`, default 5). Cache **hits** do not consume. Exhausted → HTTP **429** (`rate_limit_reached`). If Redis cannot update the counter, the route returns HTTP **503** (`quota_unavailable`) and does not call a provider. Upstream dual-fail refunds the consumed unit; a refund that itself cannot reach Redis still returns **502**. The Redis bucket resets at **UTC midnight**.

**Cache failures:** a Redis error on read is a cache miss. A Redis error on write does not fail the completion. Invalid cached JSON is a miss.

OpenAI Chat Completions-compatible body: `messages`, `temperature`, `max_tokens`, plus optional `top_p`, `stop`, and `model` as described above. Other extra fields are ignored.

Each success includes a unique `id` (`chatcmpl-` plus a random hex), `created` (unix seconds), `model` (the provider model, or null when a cached value has none), `choices[0].finish_reason`, and `usage`. Gemini `STOP` (or a missing reason) is `stop`, `MAX_TOKENS` is `length`, and `SAFETY`, `RECITATION`, `BLOCKLIST`, `PROHIBITED_CONTENT`, or `SPII` is `content_filter`. A cached finish reason outside that set is replayed as `stop`. `usage.prompt_tokens`, `usage.completion_tokens`, and `usage.total_tokens` are copied from the provider. Gemini uses `usageMetadata` (`promptTokenCount`, `candidatesTokenCount`, `totalTokenCount`). Ollama uses `prompt_eval_count` and `eval_count`; when both are present and no total was sent, `total_tokens` is their sum. A count the provider did not send is **null**. The gateway does not estimate tokens. `latency_ms` is a whole number of milliseconds.

Gateway-specific response fields (in addition to that completion payload):

| Field | Type | Meaning |
| --- | --- | --- |
| `cached` | boolean | Redis exact-match hit |
| `latency_ms` | integer | Gateway hop latency, rounded to a millisecond |
| `provider` | string | Adapter that produced the completion (`local` or `cloud`). Cache hits reuse the stored origin; they do not set `provider` to `cache`. |

The chat route declares `response_model` and `responses` for 200, 401, 413, 422, 429, 502, and 503. The schema `info.version` is `app.__version__`. `GET /` redirects to `/docs`.

Errors use one envelope and do not repeat the submitted body:

```json
{"error": {"message": "...", "type": "...", "param": null, "code": "..."}}
```

Mirrored headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`. Every response also returns `X-Request-Id`. A caller may send that header when the value is 1–128 characters of letters, digits, `.`, `_`, or `-`. Any other value is replaced with a generated id. The process writes one JSON access log line per request with `request_id`, `method`, `path` (the route template, or `unmatched`), `status`, and `latency_ms`. Chat lines also include `provider` and `cached` when those response headers are present. The line leaves out the submitted message text and credential headers.

### Behavior

| Condition | Result |
| --- | --- |
| Cache hit | Stored completion, `cached: true`, target latency <10 ms |
| Cache miss, success | Upstream completion, write Redis, `cached: false` |
| Primary 5xx, timeout, or unexpected provider exception | One retry on the secondary provider; success is cached |
| Primary non-retryable 4xx | HTTP 502; the secondary provider is not called |
| Gemini blocks the prompt and returns no text | HTTP 502; the secondary provider is not called |
| Both providers fail | HTTP 502; **not** cached; quota refunded when Redis allows it |
| Redis cannot read the cache | Treated as a miss; the upstream completion is returned |
| Redis cannot write the cache | HTTP 200 with the completion |
| Redis cannot consume quota | HTTP 503 (`quota_unavailable`); providers are not called |
| Missing/invalid `X-API-Key` or Bearer token, even if the body is invalid or oversized | HTTP 401 |
| Authenticated body over the size cap | HTTP 413 |
| Daily quota exhausted | HTTP 429 |
| Quota store cannot be updated | HTTP 503 |
| Invalid body, including out-of-range fields | HTTP 422 (`invalid_request_error`; submitted text is not echoed) |
| `stream: true` | HTTP 422 |
| Unknown path | HTTP 404 (`not_found`) |

Cache key: SHA-256 of a canonical serialization of `messages` + `temperature` + `max_tokens`. Omitted `temperature` is stored as `1.0`. `top_p`, `stop`, and a caller-selected Gemini model id are added only when the request sets them. The routed provider name is not part of the key.

## `GET /metrics`

Unauthenticated Prometheus text. `gateway_http_requests_total` counts handled requests by method, route, and status. `gateway_http_request_latency_ms_sum` and `gateway_http_request_latency_ms_count` record latency in milliseconds. The page is counters only.

## `GET /health`

| Redis | Upstreams | HTTP | Payload `status` |
| --- | --- | --- | --- |
| Up | All reachable | 200 | `ok` |
| Up | At least one down | 200 | `degraded` |
| Down | — | 503 | `down` |

The process can still serve cache hits when a single upstream is down, as long as Redis is healthy. Without Ollama, expect `degraded` while Gemini remains up. `GET /health` does **not** require `X-API-Key`.

`GET /health/live` returns HTTP 200 `{"status": "live"}` and does not probe Redis or providers. `GET /health/ready` returns HTTP 200 `ready` when Redis is up and at least one provider is up. It returns HTTP 503 `not_ready` when Redis is down or both providers are down. Neither probe requires `X-API-Key`.

Interactive OpenAPI: `GET /docs` (FastAPI default).

**Go deeper:** [Quick start](Quick-start.md) · [How it works](How-it-works.md)
