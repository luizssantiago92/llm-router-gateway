# LLM Router Gateway

**One OpenAI-shaped facade for local and cloud chat models — zero-cost demo.**

Internal apps call a single completions endpoint. The gateway caches exact matches, sends simple work to a local model when available, sends complex work to Gemini, and fails over once when an upstream is down.

Agents are fast — and optimistic. This repo is the **demo / lab** surface: a stable contract in git, not a scatter of provider SDKs in every service. You keep control of keys, quota, and what is in scope.

| Without the gateway | With LLM Router Gateway |
| --- | --- |
| Every call is a paid cloud hop | Exact-match cache returns repeats in milliseconds |
| Apps pick models and fail over themselves | Simple → local; complex → cloud; one automatic hop |
| Outage = hard fail | Primary 5xx/timeout retries the other tier once |
| Opaque origin | `X-Cache` / `X-Latency-Ms` / `X-Provider` on every response |
| Unbounded demo spend | Shared `X-API-Key` + daily quota (cache hits free) |

Domain: [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) **REQ-001–REQ-022**

**Docs:** [Overview](docs/guide/Overview.md) · [Quick start](docs/guide/Quick-start.md) · [Full guide index](docs/guide/README.md)

---

## What it is

LLM Router Gateway is not a production chatbot, not a multi-tenant LLM platform, and not hosted SaaS. It is a **repo-native FastAPI reverse proxy** for internal chat completions: cache, complexity routing, one-hop fallback, and a Gemini free-tier demo with daily quota.

It intercepts OpenAI-shaped `POST /v1/chat/completions` so applications get:

- **Requirements as code** — domain spec REQ-001–REQ-022, not chat folklore
- **Exact-match cache** — Redis SHA-256 over `messages` + `temperature` + `max_tokens`
- **Complexity routing** — short/plain → optional Ollama; long text or code/reasoning keywords → Gemini
- **One-hop fallback** — primary 5xx or timeout retries the other tier once
- **Demo cost guard** — `GATEWAY_API_KEY` via `X-API-Key`; Redis daily quota (default 5; cache hits free)
- **Observability** — JSON `cached`, `latency_ms`, `provider` plus matching `X-*` headers

You do not need to already know the adapters. Clients never choose a provider.

| Status | Detail |
| --- | --- |
| **Shipped** | Compose demo (`api` + `redis`); `/health` + chat via Gemini |
| **Posture** | Academic / demonstrative — not a production chatbot |
| **Cloud** | Google Gemini free tier (`GEMINI_API_KEY`, default `gemini-3.5-flash`) |
| **Local** | Optional Ollama (`llama3` class); unreachable → health `degraded`, fallback to Gemini |
| **Contract** | `POST /v1/chat/completions` · `GET /health` (no key) · OpenAPI at `/docs` |

**Reuse intent:** lift patterns into [Gold Queen](https://github.com/luizssantiago92/gold-queen-api) where useful; a **real company chatbot** is a later product. This repo stays the demo.

**Go deeper:** [Overview](docs/guide/Overview.md)

---

## Quick start

Two commands — run both in the project root after filling `.env`. Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL 2 on Windows) or another Compose-capable Docker, and a [Gemini API key](https://aistudio.google.com/apikey). Ollama is optional.

```bash
cp .env.example .env
# Required: GEMINI_API_KEY (AI Studio), GATEWAY_API_KEY (any secret you invent).

docker compose up --build
```

| Command | What it does |
| --- | --- |
| **`docker compose up --build`** | Starts `api` on **8000** and `redis` on **6379** |
| **`GET /health`** | No API key. `ok` if Ollama + Gemini are up; `degraded` if only Gemini is up; Redis down → **503** |
| **`POST /v1/chat/completions`** | Needs `X-API-Key` equal to `GATEWAY_API_KEY` from `.env` (an unset shell `$GATEWAY_API_KEY` **401**s) |

```bash
curl -s http://localhost:8000/health
```

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_GATEWAY_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

Interactive contract: [http://localhost:8000/docs](http://localhost:8000/docs).

| Result | Meaning |
| --- | --- |
| `200` + `provider: "cloud"` | Gemini served a cache miss (typical without Ollama) |
| `200` + `cached: true` | Repeat of the same body (quota not consumed) |
| `401` | Missing or wrong `X-API-Key` |
| `429` | Daily cache-miss quota exhausted (default 5; UTC midnight) |
| `422` | Invalid body or `stream: true` |
| `502` | Both hops failed, or primary 4xx (not retried). Quota refunded |

**Without Ollama:** leave the Compose default URL. Health stays `degraded`; simple prompts fail locally once and **fall back to Gemini** (REQ-022).

**Go deeper:** [Quick start](docs/guide/Quick-start.md) · [FAQ](docs/guide/FAQ.md)

---

## The problem

Calling a cloud LLM directly from every service creates three recurring costs:

| Pain | What goes wrong |
| --- | --- |
| **Cost** | Short, repeated, or simple prompts burn paid tokens |
| **Latency** | Identical requests hit the network every time |
| **SPOF** | One upstream outage blocks the whole product |

The gateway maps each failure mode to a mechanism:

| Failure mode | Mechanism |
| --- | --- |
| **Repeat spend** | Redis exact-match cache (TTL default 3600s) |
| **Simple work on an expensive model** | Complexity evaluator → local primary when Ollama is up |
| **One upstream down** | One opposite-tier hop on 5xx or timeout |
| **Demo quota blow-up** | Shared `X-API-Key` + daily Redis bucket (cache hits free) |

You want a stable contract for applications — not a scatter of provider SDKs and ad-hoc retries.

---

## Three pillars

Most demo pain is not “pick a better SDK.” It is **repeat cost**, **wrong model for the prompt**, or **one outage taking everything down**.

| Problem | Pillar | One-line win |
| --- | --- | --- |
| Same prompt paid again | **Exact-match cache** | Redis hit; quota not consumed |
| Tiny prompt on Gemini | **Complexity routing** | Simple → local; complex → cloud |
| Local or cloud is down | **One-hop fallback** | Retry the other tier once, then 502 |

### 1. Exact-match cache — stop paying for repeats

**Without it:** Identical `messages` / `temperature` / `max_tokens` hit Gemini every time and consume demo quota.

**With Redis:** The key is SHA-256 of a canonical serialization of those three fields (the routed model name is **not** in the key). Hits return the stored completion with `cached: true` and reuse the stored `provider` (`local` or `cloud` — never `"cache"`). Errors are not written.

**Go deeper:** [concepts](docs/guide/concepts.md#exact-match-cache)

### 2. Complexity routing — local for simple, Gemini for complex

**Without it:** Every miss goes to the cloud, or every caller hard-codes a model.

**With the evaluator:** Concatenated message contents are **complex** if the word count is **greater than** `COMPLEXITY_WORD_THRESHOLD` (default 150) **or** they contain a keyword (`code`, `algorithm`, `implement`, `debug`, `function`, `class`, `step by step`, `reason`). Otherwise they are **simple** (Ollama first). Clients never choose the adapter.

**Go deeper:** [concepts](docs/guide/concepts.md#complexity-routing)

### 3. One-hop fallback — one outage is not a hard fail

**Without it:** Ollama down means simple prompts die; Gemini 5xx means complex prompts die.

**With one hop:** A retryable primary failure (HTTP 5xx or timeout) tries the opposite tier once. A non-retryable 4xx from the primary is **not** hopped; the route still returns **502** and refunds the quota unit. Dual failure → 502, not cached.

**Go deeper:** [How it works](docs/guide/How-it-works.md) · [Architecture](docs/guide/Architecture.md)

---

## How it works

High-level request path — clients never pick a provider:

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
              X-Cache / X-Latency-Ms / X-Provider
```

Streaming is not supported (`stream: true` → 422).

**Go deeper:** [How it works](docs/guide/How-it-works.md)

---

## Contract

OpenAI-shaped facade. Extra request fields are accepted and ignored. Factory: `app.main:build_default_app`.

| Surface | Auth | Notes |
| --- | --- | --- |
| `POST /v1/chat/completions` | `X-API-Key` = `GATEWAY_API_KEY` | Quota on cache **miss** only |
| `GET /health` | none | `ok` / `degraded` / Redis-down `503` |
| `GET /docs` | none | FastAPI OpenAPI UI |

**Go deeper:** [API](docs/guide/API.md)

---

## What is shipped — and what is not

This demo implements the domain spec. It does **not** grow into the company chatbot without a new `feature-init`.

| Shipped | Not shipped |
| --- | --- |
| OpenAI-shaped JSON facade | Streaming (`stream: true` → 422, D-009) |
| Redis exact-match cache | Semantic / embedding cache |
| Ollama (optional) + Gemini | Paid OpenAI / Anthropic / vLLM happy path |
| One-hop fallback on 5xx/timeout | Kubernetes / Helm / Terraform |
| Shared `X-API-Key` + daily quota | Production multi-tenant auth |
| Compose `api` + `redis` | Hosted deploy, chat UI, Ollama-in-Compose |

> A green `pytest` run means the suite passed — it is not proof this demo is a production chatbot.

**Go deeper:** [Limitations](docs/guide/Limitations.md)

---

## Spec Guardrails

This repository is governed with [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) (`python-platform`). Day to day, work in agent chat; the agent calls the CLI when a phase needs it.

```bash
npx @luizsantiago/spec-guardrails doctor
```

Typical Complex order:

```
/elicit → /specify → /discuss? → /plan → /tasks → /loop → /verify → /archive
```

v1 (`001-llm-router-gateway`) is archived. Do not re-ask **D-001–D-012**.

**Significant PRs update this README and `docs/guide/` in the same PR** (C-008 / C-009) — see [CONTRIBUTING](CONTRIBUTING.md).

**Go deeper:** [Development](docs/guide/Development.md) · [Hub](.cursor/skills/agent-architecture.md)

---

## Limitations

Spec Guardrails and this README shape **how the demo is documented**. They do not make Gemini free-tier limits disappear, and they do not authorize production scope in this repo.

### Still open (agents: read this)

Do **not** treat the list below as in-scope until the owner starts a new `feature-init`. Prefer extracting useful pieces into Gold Queen or a future production chatbot rather than growing this demo here.

| Item | Status | Notes |
| --- | --- | --- |
| Streaming (`stream: true`) | **deferred** | Rejected with 422 today (D-009) |
| Production edge auth | **deferred** | Only shared `GATEWAY_API_KEY` / `X-API-Key` |
| Multi-tenancy / per-tenant quotas | **deferred** | Single demo key + daily Redis bucket (UTC midnight) |
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

Session pointer: [`.specs/STATE.md`](.specs/STATE.md). Milestones: [`.specs/project/ROADMAP.md`](.specs/project/ROADMAP.md). Full table: [Limitations](docs/guide/Limitations.md).

---

## Documentation

### Start here

- [Overview](docs/guide/Overview.md) — what it is, how to use it
- [Quick start](docs/guide/Quick-start.md) — first ten minutes
- [How it works](docs/guide/How-it-works.md) — request path in plain words
- [Home](docs/guide/Home.md) — short hub

### Understand the system

- [Architecture](docs/guide/Architecture.md) · [API](docs/guide/API.md) · [concepts](docs/guide/concepts.md)
- [FAQ](docs/guide/FAQ.md) · [Glossary](docs/guide/Glossary.md)
- [Development](docs/guide/Development.md) — stack, env, pytest, C-008 / C-009

### Advanced

- [Limitations](docs/guide/Limitations.md) · [CHANGELOG](docs/CHANGELOG.md) · [CONTRIBUTING](CONTRIBUTING.md)
- Domain [spec.md](.specs/domains/llm-router-gateway/spec.md) · [`prd.md`](prd.md) (historical; live cloud default is Gemini)
- [`.specs/project/PROJECT.md`](.specs/project/PROJECT.md) · [`ROADMAP.md`](.specs/project/ROADMAP.md) · [`STATE.md`](.specs/STATE.md)

Full index: [docs/guide/README.md](docs/guide/README.md)

---

## License

No `LICENSE` file is published on this repository. Do not assume reuse rights. Do not commit secrets, API keys, or `.env` files.
