# API

OpenAI-shaped facade. Process factory: `app.main:build_default_app` (Uvicorn `--factory`). The factory does not open sockets. A lifespan opens the async Redis client and one HTTP client per upstream on startup and closes them on shutdown. Tests call `create_app(...)` and inject fakes. Those injected objects are not replaced or closed by the lifespan.

Product entry: [README](../README.md). System description: [Architecture](architecture.md).

## `POST /v1/chat/completions`

**Auth.** `X-API-Key` or `Authorization: Bearer` must match `GATEWAY_API_KEY`. Otherwise HTTP 401 (`unauthorized` / `invalid_api_key`, message `missing or invalid X-API-Key`). That includes a missing body, invalid JSON, a validation failure, or an oversized body: the credential is checked before the body is read. The comparison uses UTF-8 bytes. Health does not use either header.

**Size.** After a valid credential, `Content-Length` or a chunked body above the cap is HTTP 413 (`payload_too_large`) and is not parsed. The default cap is 256 KiB (`MAX_BODY_BYTES`, 262144). Settings can only tighten that cap.

**Fields.**

| Field | Rule |
| --- | --- |
| `role` | `system`, `user`, or `assistant` |
| `content` | 1–32,000 characters |
| `messages` | 1–50 items; combined content at most 64,000 characters |
| `temperature` | Omitted, or 0–2. Omitted uses `1.0` in the cache key and the local adapter, and is left out of the Gemini generation config. Explicit `0` is sent. |
| `top_p` | Omitted, or 0–1. When set, Gemini receives `topP` and the cache key includes it. |
| `stop` | A string or a list of 1–5 strings, each 1–256 characters. Forwarded as Gemini `stopSequences` and Ollama `options.stop`. Included in the cache key only when non-empty. |
| `model` | Optional, 1–128 characters. A Gemini id (`gemini` plus letters, digits, `.`, `_`, `-`) selects the cloud model for that call and is part of the cache key. Any other name is ignored. Ollama keeps its configured model. Health probes use the configured cloud model. |
| `max_tokens` | Omitted, or 1–4096 |
| `stream` | `true` is HTTP 422 |

Settings can lower the message, temperature, and `max_tokens` ceilings and cannot raise them. Out-of-range values are HTTP 422. Extra fields are ignored.

**Quota.** Each cache miss consumes one unit of the caller's daily limit (`CHAT_DAILY_LIMIT`, default 5). Cache hits do not. Exhausted is HTTP 429 (`rate_limit_reached`). If Redis cannot update the counter, the route returns HTTP 503 (`service_unavailable` / `quota_unavailable`, message `quota store unavailable`) and does not call a provider. A dual failure refunds the unit. A refund that itself cannot reach Redis still returns 502. The bucket id is a scrypt digest of the API key. It resets at UTC midnight.

**Cache failures.** A Redis error on read is a miss. A Redis error on write does not fail the completion. Invalid cached JSON is a miss.

**Success body.** Unique `id` (`chatcmpl-` plus random hex), `created` (unix seconds), `model`, `choices[0].finish_reason`, and `usage`. Cache hits mint a new id and `created`. `usage` is copied from the provider and is null when the provider sent no count. The gateway does not estimate tokens. Gemini copies `promptTokenCount`, `candidatesTokenCount`, and `totalTokenCount` when they are non-negative integers, and does not add thoughts tokens. Ollama uses `prompt_eval_count` and `eval_count`; `total_tokens` is their sum only when both are present and no total was sent. `latency_ms` is the elapsed time rounded to a whole millisecond and matches `X-Latency-Ms`.

Gemini finish reasons: `STOP` or missing becomes `stop`, `MAX_TOKENS` becomes `length`, and `SAFETY`, `RECITATION`, `BLOCKLIST`, `PROHIBITED_CONTENT`, or `SPII` become `content_filter`. `promptFeedback.blockReason` forces `content_filter` when text exists. A blocked prompt with no text is a non-retryable provider failure (HTTP 502 at the route, no hop). A cached finish reason outside `{stop, length, content_filter}` is replayed as `stop`.

Gateway fields on the same object: `cached` (boolean), `latency_ms` (integer), `provider` (`local` or `cloud`).

**Errors.** One envelope, and the submitted text is not repeated:

```json
{"error": {"message": "...", "type": "...", "param": null, "code": "..."}}
```

| Condition | HTTP | `type` / `code` |
| --- | --- | --- |
| Missing or invalid credential, even if the body is invalid or oversized | 401 | `unauthorized` / `invalid_api_key` |
| Authenticated body over the size cap | 413 | `payload_too_large` |
| Invalid body, including `stream: true` | 422 | `invalid_request_error` / `validation_error`. Message `request validation failed`. `param` is the field path with `body` stripped. |
| Daily quota exhausted | 429 | `rate_limit_reached` |
| Quota store cannot be updated | 503 | `service_unavailable` / `quota_unavailable` |
| Both providers fail, a non-retryable primary 4xx, or a blocked Gemini prompt with no text | 502 | `upstream_error` |
| Unknown path | 404 | `not_found` / `not_found`. Message `Not Found`. |

`GET /` redirects to `/docs` with HTTP 307 and is omitted from the schema. The schema title is `LLM Router Gateway` and `info.version` is `app.__version__` (`0.1.0`).

## `GET /metrics`

Unauthenticated Prometheus text (`text/plain; version=0.0.4; charset=utf-8`). Counters: `gateway_http_requests_total{method,path,status}`, `gateway_http_request_latency_ms_sum`, `gateway_http_request_latency_ms_count`. The path label is the route template or `unmatched`.

## `GET /health`

| Redis | Upstreams | HTTP | `status` |
| --- | --- | --- | --- |
| Up | All reachable | 200 | `ok` |
| Up | At least one down | 200 | `degraded` |
| Down | — | 503 | `down` |

`GET /health/live` returns HTTP 200 `{"status":"live"}` and does not probe Redis or providers. `GET /health/ready` returns HTTP 200 `ready` only when Redis is up and at least one provider is up. Otherwise it returns HTTP 503 `not_ready`. None of the three probes require a credential.

## Headers

| Header | Meaning |
| --- | --- |
| `X-Cache` | `hit` or `miss` on a completion |
| `X-Latency-Ms` | Same whole-millisecond value as `latency_ms` |
| `X-Provider` | `local` or `cloud` |
| `X-Request-Id` | Caller value when it is 1–128 characters of letters, digits, `.`, `_`, or `-` and starts with a letter or digit. Otherwise a generated id. Present on every response, including 401 and 404. |
