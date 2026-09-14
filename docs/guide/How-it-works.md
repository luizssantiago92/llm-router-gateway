# How it works

Think of LLM Router Gateway as a **single door** in front of local and cloud chat models.

Without it, every service picks a provider SDK, retries on its own, and pays for the same prompt twice. With it, the gateway **authenticates the demo caller, serves exact cache hits, classifies misses, calls one adapter, hops once if needed, and tells you who served the answer**.

## The simple idea

1. **Same contract** (OpenAI-shaped JSON)
2. **Same prompt?** (Redis exact match — no quota)
3. **Simple or complex?** (word count or keywords)
4. **One hop if the primary is sick** (5xx or timeout only)
5. **Show your work** (`cached`, `latency_ms`, `provider`)

If both hops fail, the gateway **stops** with HTTP 502 and refunds the quota unit. It does not retry forever.

## The journey (in plain words)

### 0. Auth — chat only

`POST /v1/chat/completions` requires `X-API-Key` matching `GATEWAY_API_KEY`. Missing or wrong → **401**. `GET /health` has **no** key (REQ-020).

### 1. Cache — “Have we answered this exact thing?”

The key is SHA-256 of a canonical JSON of `messages` + `temperature` + `max_tokens`. The model id is **not** in the key. Hits return the stored body with `cached: true` and the stored `provider` (`local` or `cloud` — never `"cache"`). Quota is not consumed. Errors are never stored.

### 2. Quota — “Misses cost a demo token”

On miss, the gateway consumes one unit of the caller’s daily Redis bucket (`CHAT_DAILY_LIMIT`, default 5, UTC midnight). Exhausted → **429**. Dual-fail (or any remaining `ProviderError` after routing) **refunds** that unit.

### 3. Classify — “Local or cloud first?”

Concatenated message contents are **complex** if word count **> 150** (configurable) **or** they contain `code`, `algorithm`, `implement`, `debug`, `function`, `class`, `step by step`, or `reason`. Otherwise **simple** (Ollama first).

### 4. Call — “One adapter, then maybe the other”

Simple → Ollama then Gemini. Complex → Gemini then Ollama. Connection failures and HTTP 5xx / timeouts are retryable. Gemini/Ollama **4xx** is **not** hopped; the route still returns **502**.

Without Ollama, simple prompts fail locally once (retryable) and **fall back to Gemini**. Health stays `degraded`. That is the supported light-PC path (REQ-022).

### 5. Observe — “Who answered?”

JSON and headers: `X-Cache`, `X-Latency-Ms`, `X-Provider`. Streaming is not supported (`stream: true` → 422).

```text
POST /v1/chat/completions
        X-API-Key
              |
              v
     +--------+--------+
     |  SHA-256 cache  |
     +--------+--------+
          |         |
     (hit)|         |(miss)
          v         v
     return Redis   consume daily quota
                    |
                    v
              classify prompt
               /          \
         simple            complex
            v                  v
        Ollama              Gemini
            \                  /
             \   5xx/timeout  /
              \   one hop    /
               +------+------+
                      |
                      v
              store success in Redis
```

## What you get day to day

- Repeats in milliseconds instead of another Gemini round-trip
- Simple prompts stay local when Ollama is up
- One upstream outage is not an automatic hard fail
- Demo spend capped by a shared key + daily quota

## What it does *not* do

It does not stream, embed, run RAG, or pick Anthropic/OpenAI on the happy path. It **does** keep a stable facade so apps do not care which adapter won.

See [Limitations](Limitations.md).

## Next

- New here? → [Overview](Overview.md)
- [Quick start](Quick-start.md)
- Components → [Architecture](Architecture.md)
- Status codes → [API](API.md)
- Back → [Home](Home.md)
