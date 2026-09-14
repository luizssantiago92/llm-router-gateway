# LLM Router Gateway

**One OpenAI-shaped facade for local and cloud chat models — zero-cost demo.**

Internal apps call a single completions endpoint. The gateway caches exact matches, sends simple work to a local model when available, sends complex work to Gemini, and fails over once when an upstream is down.

This repository is the **demo you run locally**: Compose (`api` + `redis`), a Gemini free-tier cloud hop, and an optional host Ollama. It is an academic / lab demo — not a production chatbot.

[The gateway](#the-gateway) ·
[Prepare](#1-prepare-your-environment) ·
[Run](#2-run-the-demo) ·
[Verify](#3-verify) ·
[Checklist](#checklist) ·
[Commands](#commands-at-hand) ·
[Explore](#explore-the-project) ·
[Still open](#still-open-agents-read-this)

**Docs:** [Overview](docs/guide/Overview.md) · [Quick start](docs/guide/Quick-start.md) · [Full guide](docs/guide/README.md)

---

## The gateway

You will find an OpenAI-shaped `POST /v1/chat/completions`, a `GET /health` probe, Redis exact-match cache, complexity routing, one-hop fallback, and a shared demo API key with a daily quota.

The stack is **Python 3.10+ / FastAPI**, **Redis**, **Google Gemini** (default `gemini-3.5-flash`), and **optional Ollama** (`llama3` class). To run the demo you **do** need Docker and a Gemini API key. You do **not** need a paid OpenAI account, Kubernetes, or a UI.

> **The contract:** applications never pick a provider. They send `messages`, `temperature`, and `max_tokens`. The gateway decides cache vs local vs cloud, hops once on 5xx/timeout, and returns `cached`, `latency_ms`, and `provider`.

| Status | Detail |
| --- | --- |
| **Shipped** | Compose demo; `/health` + chat via Gemini |
| **Posture** | Academic / demonstrative — not a production chatbot |
| **Cloud** | Gemini free tier (`GEMINI_API_KEY`) |
| **Local** | Optional Ollama; unreachable → health `degraded`, fallback to Gemini |
| **Cost guard** | `X-API-Key` (`GATEWAY_API_KEY`) + Redis daily quota (default 5; cache hits free) |
| **Domain** | [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022) |

**Reuse intent:** lift cache, routing, fallback, quota, and the Gemini adapter into [Gold Queen](https://github.com/luizssantiago92/gold-queen-api) where useful. A real company chatbot is a later product. This repo stays the demo.

### What you get

| Without the gateway | With LLM Router Gateway |
| --- | --- |
| Every call is a paid cloud hop | Exact-match cache returns repeats in milliseconds |
| Apps pick models and fail over themselves | Simple → local; complex → cloud; one automatic hop |
| Outage = hard fail | Primary 5xx/timeout retries the other tier once |
| Opaque origin | `X-Cache` / `X-Latency-Ms` / `X-Provider` on every response |
| Unbounded demo spend | Shared `X-API-Key` + daily quota (cache hits free) |

Different setups are welcome. Docker + a Gemini key is enough for the light-PC path (no Ollama). The numbered steps below get the process running; concepts live in the [guide](docs/guide/How-it-works.md).

---

## 1. Prepare your environment

Set this up **before** the first `docker compose up`.

| Tool | Requirement | What it is for |
| --- | --- | --- |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Compose-capable Docker | `docker compose` on PATH | Ship unit: `api` + `redis` |
| [Gemini API key](https://aistudio.google.com/apikey) | Non-empty `GEMINI_API_KEY` | Cloud completions (free-tier oriented) |
| Git | Installed | Clone and version the repo |
| Editor + terminal | Your usual tools | `.env`, curls, logs |
| [Ollama](https://ollama.com/) | **Optional** | Local primary for simple prompts (REQ-022) |
| Python 3.10+ | Optional (tests) | `pytest` without Compose |

**Ollama is optional.** If it is not installed, health stays `degraded` and simple prompts fall back to Gemini after one local failure. That is the supported demo path.

Open the notes for your system:

<details>
<summary>Windows — Docker Desktop + WSL 2</summary>

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) with the **WSL 2** backend. Reopen the terminal after install.
2. Confirm:

```bat
docker version
docker compose version
```

3. Keep the project **inside WSL** (or a Docker-integrated distro). Do not mix bind mounts between Windows paths and a Linux engine.
4. Get a Gemini key from [Google AI Studio](https://aistudio.google.com/apikey). You will paste it into `.env` in step 2.

</details>

<details>
<summary>macOS — Docker Desktop</summary>

1. Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/).
2. Confirm in Terminal:

```bash
docker version
docker compose version
```

3. `host.docker.internal` already points at the Mac. Optional host Ollama on port **11434** is reachable from the `api` container without extra Compose flags.

</details>

<details>
<summary>Linux — Docker Engine</summary>

1. Install a Compose-capable Docker Engine ([docs](https://docs.docker.com/engine/install/)).
2. Confirm:

```bash
docker version
docker compose version
```

3. This repo maps `host.docker.internal` → `host-gateway` on the `api` service so optional **host** Ollama works the same way as on Docker Desktop. If you skip Ollama, leave the default URL.

</details>

---

## 2. Run the demo

A **clone** brings the repo to your machine. You do not need a fork unless you intend to open a PR.

```bash
git clone https://github.com/luizssantiago92/llm-router-gateway.git
cd llm-router-gateway
cp .env.example .env
```

Fill **only** these two unless you need overrides:

| Variable | What to put |
| --- | --- |
| `GEMINI_API_KEY` | From Google AI Studio |
| `GATEWAY_API_KEY` | Any secret you invent — callers send it as `X-API-Key` |

Leave the rest blank for Compose defaults (`gemini-3.5-flash`, daily limit `5`, Ollama URL `http://host.docker.internal:11434`, TTL `3600`). Leave `REDIS_URL` blank — Compose hardcodes `redis://redis:6379/0` inside `api`.

```bash
docker compose up --build
```

Leave that terminal open. Then, in another terminal:

```bash
curl -s http://localhost:8000/health
```

Chat **requires** the same `GATEWAY_API_KEY` you wrote in `.env`. Compose injects it into the container; an unset shell `$GATEWAY_API_KEY` **401**s:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_GATEWAY_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

> **Open [http://localhost:8000/docs](http://localhost:8000/docs).** You should see the FastAPI OpenAPI UI. Health does not need a key; chat does.

### Check your first access

1. `GET /health` returns HTTP 200 with `"degraded"` (no Ollama) or `"ok"` (Ollama + Gemini up). Redis down would be HTTP **503**.
2. The `"Hello"` curl returns assistant content. Without Ollama, expect `provider: "cloud"` on a cache miss.
3. Repeat the **same** body: `cached: true` and the daily quota is **not** consumed.
4. A wrong or missing `X-API-Key` returns **401**.

| Result | Meaning |
| --- | --- |
| `200` + `provider: "cloud"` | Gemini served a cache miss (typical without Ollama) |
| `200` + `cached: true` | Exact-match repeat (quota not consumed) |
| `401` | Missing or wrong `X-API-Key` |
| `429` | Daily cache-miss quota exhausted (default 5; UTC midnight) |
| `422` | Invalid body or `stream: true` |
| `502` | Both hops failed, or primary returned non-retryable 4xx (no second hop). Quota refunded |

Never commit `.env`. The app does not call `load_dotenv`.

Stuck? [FAQ](docs/guide/FAQ.md) · [Quick start](docs/guide/Quick-start.md)

---

## 3. Verify

The default suite does **not** call live Gemini or Ollama (`pyproject.toml` already applies `-m "not live"`).

```bash
pip install -e ".[dev]"
pytest
```

Expected: **41 passed** (marker-filtered). Compose can keep running; tests use fakes, not the container.

---

## Checklist

- [ ] Docker Compose responds in the terminal.
- [ ] `.env` has non-empty `GEMINI_API_KEY` and `GATEWAY_API_KEY`.
- [ ] `docker compose up --build` stays up (`api` **8000**, `redis` **6379**).
- [ ] `GET /health` is `degraded` or `ok`.
- [ ] Chat curl with `YOUR_GATEWAY_KEY` returns content.
- [ ] Repeating the same body sets `cached: true`.
- [ ] `pytest` passes locally (optional if you only want the demo).

Blocked? Show the error and the step number. Common traps: empty `$GATEWAY_API_KEY` in the shell, blank Gemini key (container crash-loop), expecting `"ok"` health without Ollama.

---

## Commands at hand

Run from the repository root (where `docker-compose.yml` and `pyproject.toml` live).

| Command | What it does |
| --- | --- |
| `cp .env.example .env` | Create a local secrets file (never commit it). |
| `docker compose up --build` | Start `api` + `redis`. |
| `curl -s http://localhost:8000/health` | Probe Redis and providers (no API key). |
| `pytest` | Unit/integration suite; live upstreams skipped. |
| `npx @luizsantiago/spec-guardrails doctor` | Spec Guardrails Process / Brakes scores. |

### Need to reset quota or cache?

Daily quota lives in Redis and resets at **UTC midnight**. To wipe cache and quota during a demo, restart Redis (`docker compose restart redis`) — that also drops cached completions.

---

## Explore the project

| Path | What you find |
| --- | --- |
| [`app/`](app/) | FastAPI gateway: routes, cache, routing, providers, quota |
| [`app/api/completions.py`](app/api/completions.py) | `POST /v1/chat/completions` (auth, cache, quota, 502) |
| [`app/api/health.py`](app/api/health.py) | `GET /health` |
| [`app/providers/`](app/providers/) | Ollama (`local`) and Gemini (`cloud`) adapters |
| [`tests/`](tests/) | pytest-asyncio; [`tests/eval/`](tests/eval/) routing harness |
| [`docker-compose.yml`](docker-compose.yml) | Ship unit: `api` + `redis` |
| [`.env.example`](.env.example) | Env keys with empty values |
| [`docs/guide/`](docs/guide/README.md) | Overview, Quick start, Architecture, API, FAQ |
| [`AGENTS.md`](AGENTS.md) | Agent execution contract |
| [`.specs/domains/llm-router-gateway/spec.md`](.specs/domains/llm-router-gateway/spec.md) | Domain truth REQ-001–REQ-022 |
| [`prd.md`](prd.md) | Product kickoff (historical; live cloud default is Gemini) |

The target is **one local Compose instance**. JSON files and a shared demo key simplify the lab; production would need its own identity, multi-tenant quotas, and hosting decisions. See [Limitations](docs/guide/Limitations.md).

---

## How it works

1. **Authenticate (chat only)** — `X-API-Key` must match `GATEWAY_API_KEY` (401 if missing/wrong). Health has no key.
2. **Look up the cache** — Same messages, temperature, and max tokens? Serve Redis (quota not consumed).
3. **Classify** — Short and plain prefers local; long text (>150 words) or code/reasoning keywords go to Gemini.
4. **Call one provider** — Ollama if up, else Gemini. Cache misses consume one daily quota unit first (429 when exhausted).
5. **Fail over once** — Primary 5xx or timeout retries the other tier; primary 4xx is **not** hopped. Both fail → 502 and the quota unit is refunded.
6. **Store and observe** — Successful misses are cached; every response carries cache, latency, and provider signals.

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

Streaming is not supported (`stream: true` → 422). Clients never choose a provider.

**Go deeper:** [How it works](docs/guide/How-it-works.md) · [Architecture](docs/guide/Architecture.md) · [API](docs/guide/API.md)

---

## Spec Guardrails

This repo is governed with [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) (`python-platform`). Work in agent chat; the agent calls the CLI when a phase needs it.

```
/elicit → /specify → /discuss? → /plan → /tasks → /loop → /verify → /archive
```

v1 is archived. Do not re-ask **D-001–D-012**. Significant PRs update this README and `docs/guide/` **in the same PR** (C-008 / C-009) — [CONTRIBUTING](CONTRIBUTING.md).

---

## Still open (agents: read this)

Do **not** treat the list below as in-scope until the owner starts a new `feature-init`. Prefer extracting pieces into Gold Queen or a future production chatbot rather than growing this demo here.

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

Session: [`.specs/STATE.md`](.specs/STATE.md) · milestones: [`.specs/project/ROADMAP.md`](.specs/project/ROADMAP.md) · full table: [Limitations](docs/guide/Limitations.md)

---

## Documentation

### Start here

- [Overview](docs/guide/Overview.md) — what it is
- [Quick start](docs/guide/Quick-start.md) — first ten minutes
- [How it works](docs/guide/How-it-works.md) — request path
- [Home](docs/guide/Home.md) — short hub

### Understand the system

- [Architecture](docs/guide/Architecture.md) · [API](docs/guide/API.md) · [concepts](docs/guide/concepts.md)
- [FAQ](docs/guide/FAQ.md) · [Glossary](docs/guide/Glossary.md)
- [Development](docs/guide/Development.md) — stack, env, pytest, C-008 / C-009

### Advanced

- [Limitations](docs/guide/Limitations.md) · [CHANGELOG](docs/CHANGELOG.md) · [CONTRIBUTING](CONTRIBUTING.md)
- Domain [spec.md](.specs/domains/llm-router-gateway/spec.md) · [`prd.md`](prd.md)
- [PROJECT.md](.specs/project/PROJECT.md) · [ROADMAP.md](.specs/project/ROADMAP.md)

Full index: [docs/guide/README.md](docs/guide/README.md)

---

## License

No `LICENSE` file is published on this repository. Do not assume reuse rights. Do not commit secrets, API keys, or `.env` files.

[↑ Back to top](#llm-router-gateway)
