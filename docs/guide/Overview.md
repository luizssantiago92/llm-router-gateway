# Overview — LLM Router Gateway in plain language

This page explains **what the gateway is**, **how you use it**, and **how much ceremony you need** — without drowning in env names. For depth, follow the links at the end of each section.

---

## Definition

**LLM Router Gateway** is a **demonstrative FastAPI reverse proxy** for internal chat-completion traffic. Applications send an OpenAI-shaped `POST /v1/chat/completions`. The gateway caches exact matches, routes by prompt complexity, fails over once, and returns cache / latency / provider on every response.

It is **not** a production chatbot, **not** a multi-tenant LLM platform, and **not** hosted SaaS. It is an academic / lab reference. Patterns (cache, routing, fallback, quota, Gemini adapter) may be lifted into [Gold Queen](https://github.com/luizssantiago92/gold-queen-api); a real company chatbot is a separate product later.

It ships:

- **Compose** — `api` + `redis` (Ollama stays optional and external)
- **Gemini** — free-tier oriented cloud default (`GEMINI_API_KEY`, model `gemini-3.5-flash`)
- **Demo cost guard** — shared `X-API-Key` + Redis daily quota (default 5; cache hits free)

It answers one problem: every service talking to a cloud LLM directly burns tokens, repeats the same prompt, and dies when that one upstream is down.

---

## The core loop (what always applies)

```text
Authenticate   →  X-API-Key on chat (health has no key)
Cache lookup   →  SHA-256 of messages + temperature + max_tokens
Classify       →  simple → local (Ollama); complex → Gemini
Call once      →  consume quota on miss; hop once on 5xx/timeout
Observe        →  cached / latency_ms / provider
```

**Clients never pick a provider.** Streaming is rejected (`stream: true` → 422).

Full story: [How it works](How-it-works.md)

---

## Three ways to start (pick one)

| Path | You have | Flow |
| --- | --- | --- |
| **A — Compose demo** | Docker + Gemini API key | [Quick start](Quick-start.md) — `.env` → `docker compose up --build` |
| **B — Tests only** | Python 3.10+ and uv | `uv sync --frozen --all-extras` → `uv run pytest` (live upstreams skipped). `pip install -e ".[dev]"` still works |
| **C — Change the product** | Python 3.10+ and uv | [CONTRIBUTING](../../CONTRIBUTING.md) — small diffs, tests, docs in the same PR |

---

## How you interact

### HTTP — your main interface as an app

| Surface | When |
| --- | --- |
| `GET /health` | Is Redis up? Are local/cloud reachable? |
| `POST /v1/chat/completions` | Chat; send `X-API-Key` |
| `GET /docs` | OpenAPI UI while Compose is running |

Reference: [API](API.md)

### Changing this repo

Significant PRs update the [README](../../README.md) and matching `docs/guide/` pages in the **same** PR ([Development](Development.md#documentation-on-every-pr) · [CONTRIBUTING](../../CONTRIBUTING.md)).

---

## How much ceremony? (change size)

| Size | Example | Typical path |
| --- | --- | --- |
| **Quick** | README typo, one comment | Edit + commit — still fix stale README links if any |
| **Simple** | Env default, one adapter field | Update README/guide when operators see the change |
| **Medium+** | New route, new provider, quota rules | Tests for the new behavior + README + guide |

**Rule of thumb:** if an operator would copy a different curl, env name, or status code, the README changes in that PR.

---

## What’s in this repo

### 1. The gateway (`app/`)

FastAPI facade, Redis cache, evaluator, Ollama + Gemini adapters, daily quota. Tests in `tests/` (including `tests/eval/` routing harness).

### 2. The ship unit

`docker-compose.yml` + `Dockerfile`. Secrets from `.env` (never committed). Compose builds `REDIS_URL` from `REDIS_PASSWORD` and publishes Redis on `127.0.0.1` only. The image runs as non-root from a digest-pinned base. CI lints and tests on every pull request.

### 3. Archived requirements (`docs/history/`)

Domain requirements: [domain spec](../history/domain-spec.md) (REQ-001–REQ-022). Feature design: [design.md](../history/design.md). Kickoff: [PRD.pt-BR.md](../history/PRD.pt-BR.md).

### 4. Human docs (`docs/guide/`)

This tree. The root README stays the product front door.

---

## What this demo does not guarantee

- Gemini free-tier remaining free or unlimited
- Sub-10 ms cache hits on a loaded machine (that is a **target**, not a SLA)
- Production auth, streaming, RAG, or paid OpenAI
- That a green `pytest` run means the product is a company chatbot

See [Limitations](Limitations.md).

---

## Where to go next

| I want to… | Read |
| --- | --- |
| Run it in ten minutes | [Quick start](Quick-start.md) |
| Understand the hop | [How it works](How-it-works.md) |
| Integrate an app | [API](API.md) |
| Hack on the repo | [Development](Development.md) · [CONTRIBUTING](../../CONTRIBUTING.md) |
| Questions | [FAQ](FAQ.md) |
| Product README | [../../README.md](../../README.md) |

Back to [Home](Home.md)
