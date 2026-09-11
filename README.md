# LLM Router Gateway

**One OpenAI-shaped facade for local and cloud chat models — zero-cost demo.**

Internal apps call a single completions endpoint. The gateway caches exact matches, sends simple work to a local model when available, sends complex work to the cloud (Gemini), and fails over once when an upstream is down.

| Status | Detail |
| --- | --- |
| **Shipped** | Compose demo verified (`api` + `redis`); smoke `/health` + chat via Gemini |
| **Posture** | Academic / demonstrative reference — not a production chatbot |
| **Cloud** | Google Gemini free tier (`GEMINI_API_KEY`) |
| **Cost guard** | Shared `X-API-Key` + daily Redis quota (default 5; cache hits free) |
| **Domain** | [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022) |

**Reuse intent:** patterns here (cache, complexity routing, fallback, quota, Gemini adapter) may be lifted into [Gold Queen](https://github.com/luizssantiago92/gold-queen-api) where useful, and later into a **real company chatbot**. This repo stays the **demo / lab** surface.

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

---

## How it works

1. **Look up the cache** — Same messages, temperature, and max tokens? Serve Redis and stop.
2. **Classify the prompt** — Short and plain prefers local; long text or code/reasoning keywords go to Gemini.
3. **Call one provider** — Local (Ollama, if running) or cloud (Gemini).
4. **Fail over once** — If the primary returns 5xx or times out, try the other tier; both fail → 502.
5. **Store and observe** — Successful misses are cached; every response carries cache, latency, and provider signals.

Clients never choose a provider. Streaming is not supported (`stream: true` → 422).

**Without Ollama:** leave `OLLAMA_BASE_URL` at the Compose default. Health stays `degraded` (local down, cloud up); simple prompts fail locally once and **fall back to Gemini**. That is the supported light-PC demo path.

---

## Quick start

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL 2 on Windows) and a [Gemini API key](https://aistudio.google.com/apikey). Ollama is optional.

```bash
cp .env.example .env
# Required: GEMINI_API_KEY, GATEWAY_API_KEY (you invent the gateway secret).
# Optional: GEMINI_MODEL (default gemini-3.5-flash), CHAT_DAILY_LIMIT (default 5).

docker compose up --build
```

```bash
curl -s http://localhost:8000/health
# Expect: status "ok" if Ollama is up, or "degraded" if only Gemini is up.
```

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $GATEWAY_API_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

API surface: `POST /v1/chat/completions` · `GET /health` (`ok` / `degraded` / Redis-down `503`).

Full env table: [`docs/development.md`](docs/development.md).

---

## Still open (agents: read this)

This repo is a **demonstrative** gateway. Do **not** treat the list below as in-scope until the owner starts a new `feature-init`. Prefer extracting useful pieces into Gold Queen or a future production chatbot rather than growing this demo into a full product here.

| Item | Status | Notes |
| --- | --- | --- |
| Streaming (`stream: true`) | **deferred** | Rejected with 422 today (D-009) |
| Production edge auth | **deferred** | Only shared `GATEWAY_API_KEY` / `X-API-Key` |
| Multi-tenancy / per-tenant quotas | **deferred** | Single demo key + daily Redis bucket |
| Semantic / embedding cache | **deferred** | Exact-match SHA-256 only |
| Rate limits beyond daily quota | **deferred** | — |
| RAG / tools / function calling | **deferred** | — |
| Paid OpenAI (or other paid cloud) happy path | **deferred** | Separate product / company chatbot later |
| vLLM / Anthropic adapters (happy path) | **deferred** | Protocol-ready ideas only |
| Kubernetes / Helm / Terraform | **deferred** | Compose is the ship unit |
| Hosted deploy (Render, etc.) | **not started** | Optional for demos; Gold Queen already has deploy patterns |
| First-class Ollama in Compose | **not started** | Ollama stays external; optional on stronger machines |
| UI / chat frontend | **not started** | API-only demo |

**Owner roadmap (outside this repo):** (1) reuse interesting bits in Gold Queen → (2) later build a real company chatbot on paid/controlled infra → (3) keep **this** repository as the academic / zero-cost demonstrative reference.

Session pointer: [`.specs/STATE.md`](.specs/STATE.md). Milestones: [`.specs/project/ROADMAP.md`](.specs/project/ROADMAP.md).

---

## Documentation

| Doc | For |
| --- | --- |
| [Architecture](docs/architecture.md) | Request path, cache, routing, fallback |
| [API](docs/api.md) | Contract, headers, status codes, quota |
| [Development](docs/development.md) | Stack, env vars, tests, Compose, Spec Guardrails |

**Go deeper:** [docs index](docs/README.md) · product kickoff [`prd.md`](prd.md) · domain [`spec.md`](.specs/domains/llm-router-gateway/spec.md)

---

## License

See repository settings. Do not commit secrets, API keys, or `.env` files.
