# LLM Router Gateway

**One OpenAI-shaped facade for local and cloud chat models.**

Internal apps call a single completions endpoint. The gateway caches exact matches, sends simple work to a local model when available, sends complex work to the cloud (Gemini), and fails over once when an upstream is down — so repeats stay cheap and you avoid a single provider as a hard dependency.

v1 is shipped and archived. Domain truth: [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022). Demo posture: **Gemini free tier** + daily quota + shared `X-API-Key`.

---

## The problem

Calling a cloud LLM directly from every service creates three recurring costs:

| Pain | What goes wrong |
| --- | --- |
| **Cost** | Short, repeated, or simple prompts burn paid tokens |
| **Latency** | Identical requests hit the network every time |
| **SPOF** | One upstream outage blocks the whole product |

You want a stable contract for applications — not a scatter of provider SDKs and ad-hoc retries.

---

## What you get

| Without the gateway | With LLM Router Gateway |
| --- | --- |
| Every call is a paid cloud hop | Exact-match cache returns repeats in milliseconds |
| Apps pick models and fail over themselves | Simple → local; complex → cloud; one automatic hop |
| Outage = hard fail | Primary 5xx/timeout retries the other tier once |
| Opaque origin | `X-Cache` / `X-Latency-Ms` / `X-Provider` on every response |

Demo cost guard: callers send `X-API-Key`; cache misses consume a daily quota (default 5); cache hits do not.

Business targets from the PRD: cut paid-token volume by at least 30% via local routing, and remove a single cloud provider as a hard dependency.

---

## How it works

1. **Look up the cache** — Same messages, temperature, and max tokens? Serve Redis and stop.
2. **Classify the prompt** — Short and plain prefers local; long text or code/reasoning keywords go to Gemini.
3. **Call one provider** — Local (Ollama, if running) or cloud (Gemini).
4. **Fail over once** — If the primary returns 5xx or times out, try the other tier; both fail → 502.
5. **Store and observe** — Successful misses are cached; every response carries cache, latency, and provider signals.

Clients never choose a provider. Streaming is not supported (`stream: true` → 422).

**Without Ollama on this machine:** set `OLLAMA_BASE_URL` to a placeholder (Compose default is fine). Health stays `degraded`; simple prompts fail locally once and **fall back to Gemini**. That is enough for a zero-cost demo on a light PC.

---

## Quick start

Requires Docker Compose and a Gemini API key. Ollama is optional.

```bash
cp .env.example .env
# Set GEMINI_API_KEY and GATEWAY_API_KEY.
# OLLAMA_BASE_URL can stay at the Compose default if you are not running Ollama.

docker compose up --build
```

```bash
curl -s http://localhost:8000/health
```

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $GATEWAY_API_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

API surface: `POST /v1/chat/completions` · `GET /health` (`ok` / `degraded` / Redis-down `503`).

Env details: [`docs/development.md`](docs/development.md).

---

## Documentation

| Doc | For |
| --- | --- |
| [Architecture](docs/architecture.md) | Request path, cache, routing, fallback |
| [API](docs/api.md) | Contract, headers, status codes, quota |
| [Development](docs/development.md) | Stack, env vars, tests, Compose, Spec Guardrails |

**Go deeper:** [docs index](docs/README.md) · product kickoff [`prd.md`](prd.md)

---

## License

See repository settings. Do not commit secrets, API keys, or `.env` files.
