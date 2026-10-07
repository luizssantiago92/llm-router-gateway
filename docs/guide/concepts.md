# Concepts

Short definitions of the moving parts. Narrative: [How it works](How-it-works.md).

## Exact-match cache

Redis stores successful completions keyed by SHA-256 of canonical JSON `{messages, temperature, max_tokens}`. The routed model name is **not** in the key. TTL defaults to `CACHE_TTL_SECONDS=3600`. Hits skip classification, upstreams, and quota. Failures (4xx, 5xx, timeout) are never written. The cache is **fail-open**: a Redis read error or invalid JSON is a miss, and a Redis write error still returns the completion.

## Complexity routing

On miss, concatenated message contents are **complex** when:

- approximate word count **> `COMPLEXITY_WORD_THRESHOLD`** (default 150), **or**
- the text contains at least one keyword: `code`, `algorithm`, `implement`, `debug`, `function`, `class`, `step by step`, `reason`

Otherwise **simple**. Simple → local primary (Ollama). Complex → cloud primary (Gemini). Clients never pass a provider id.

## One-hop fallback

`ProviderError.is_retryable` is true for timeouts and HTTP status ≥ 500. An unexpected exception from the primary is also hopped **once**. Non-retryable 4xx is not hopped; the route still returns HTTP **502**. Two failures return HTTP **502**. There is no third attempt.

## Daily quota

Redis key `quota:{sha256(api_key)[:16]}:{UTC date}`. Each cache **miss** `INCR`s; over `CHAT_DAILY_LIMIT` → 429. Hits do not increment. Dual-fail `DECR`s. Expiry is seconds until UTC midnight (minimum 60s). The quota store is **fail-closed**: if Redis cannot increment the counter, the route returns HTTP 503 and does not call a provider. A failed refund does not replace the HTTP 502.

## Health

`GET /health` probes Redis `PING` and each provider’s `health()`. Redis down → HTTP 503 `down`. Redis up and any provider down → 200 `degraded`. All up → 200 `ok`. `GET /health/live` is process liveness and does not probe dependencies. `GET /health/ready` is 200 only when Redis is up and at least one provider is up. No `X-API-Key`.

## Demo vs production

This repo is the **demo / lab**. Shared `GATEWAY_API_KEY` is not multi-tenant auth. Gemini free tier is not a paid SLA. See [Limitations](Limitations.md).

**Go deeper:** [Architecture](Architecture.md) · [API](API.md) · [Glossary](Glossary.md)
