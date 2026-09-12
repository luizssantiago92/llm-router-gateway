# FAQ

Common operator and contributor questions. Product page: [README](../../README.md).

## Why is `/health` `degraded`?

Ollama is optional. If it is not running, local health fails and Gemini can still be up → HTTP 200 `degraded`. That is expected (REQ-022). Simple prompts still complete via one-hop fallback to Gemini.

## Why do I get HTTP 401 on chat?

`X-API-Key` must equal `GATEWAY_API_KEY` in `.env`. Compose injects that value into the `api` container. Your shell `$GATEWAY_API_KEY` is **not** set by Compose — a curl with an empty header 401s. Health does not need the key.

## Why do I get HTTP 429 after a few chats?

Cache **misses** consume the daily bucket (`CHAT_DAILY_LIMIT`, default 5, UTC midnight). Repeating the same `messages` / `temperature` / `max_tokens` is a hit and is free. Dual-fail refunds the unit.

## Why HTTP 502 when Gemini returns 4xx?

The adapter maps Gemini 4xx to `ProviderError` with that status. That is **not** retryable, so the router does not hop to Ollama. The route still returns 502 and refunds quota. Retryable hops are 5xx and timeouts only.

## Does `.env` `REDIS_URL` change Compose?

No. `api` always gets `redis://redis:6379/0`. Fill `REDIS_URL` only if you run the process **outside** Compose (`Settings.from_env` requires it).

## Do `CACHE_TTL_SECONDS` and friends in `.env` work?

Yes, on Compose — they are interpolated with defaults (`3600` / `150` / `30`). Empty values in `.env` fall through to those defaults (`:-` substitution).

## Is this a production chatbot?

No. Academic / demonstrative reference. Reuse patterns in Gold Queen or a future company chatbot. See [Limitations](Limitations.md).

## Must every PR update the README?

**Significant** product, API, setup, architecture, or status changes: **yes, in the same PR** (C-008 / C-009). Skip only purely internal diffs with no stale operator-facing text. When in doubt, update it. Details: [Development](Development.md#documentation-on-every-pr) · [CONTRIBUTING](../../CONTRIBUTING.md).

## Where is the OpenAI adapter?

Removed from the happy path (AD-004). The public contract stays OpenAI-**shaped**. Cloud default is Gemini. Paid OpenAI is deferred.

## Next

[Overview](Overview.md) · [Quick start](Quick-start.md) · [Glossary](Glossary.md) · [Home](Home.md)
