# API (v1, planned)

Internal facade. No caller authentication in v1. Streaming is out of scope. Implementation follows this contract after `/specify`.

## `POST /v1/chat/completions`

OpenAI Chat Completions-compatible body: `messages`, `temperature`, `max_tokens`. Additional OpenAI fields may be accepted and ignored if unused.

Gateway-specific response fields (in addition to a standard completion payload):

| Field | Type | Meaning |
| --- | --- | --- |
| `cached` | boolean | Redis exact-match hit |
| `latency_ms` | number | Gateway hop latency |
| provider/model origin | string | Which adapter served the completion |

Mirrored headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`.

### Behavior

| Condition | Result |
| --- | --- |
| Cache hit | Stored completion, `cached: true`, target latency <10 ms |
| Cache miss, success | Upstream completion, write Redis, `cached: false` |
| Primary 5xx or timeout | One retry on the secondary provider; success is cached |
| Both providers fail | HTTP 502 or 504; **not** cached |
| Invalid body | HTTP 422 (Pydantic) |
| `stream` present | Rejected or ignored (non-streaming JSON only) |

Cache key: SHA-256 of a canonical serialization of `messages` + `temperature` + `max_tokens`. The routed model name is not part of the key.

## `GET /health`

| Redis | Upstreams | HTTP | Payload |
| --- | --- | --- | --- |
| Up | All reachable | 200 | `ok` |
| Up | At least one down | 200 | `degraded` |
| Down | — | 503 | Redis unavailable |

The process can still serve cache hits when a single upstream is down, as long as Redis is healthy.
