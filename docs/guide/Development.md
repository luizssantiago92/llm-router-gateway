# Development

Application source lives in `app/`. Tests live in `tests/`. Work stays spec-first under [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) with the `python-platform` preset.

Human docs live in this `docs/guide/` tree. The root [README](../../README.md) is the product entry point.

## Repository map

| Path | Purpose |
| --- | --- |
| `prd.md` | Product requirements (owner kickoff; historical cloud examples) |
| `app/` | FastAPI gateway (settings, schemas, cache, routing, providers, routes) |
| `tests/` | pytest-asyncio suite; `tests/eval/` golden routing harness |
| `docker-compose.yml` / `Dockerfile` | Ship unit: `api` + `redis` |
| `.env.example` | Required env keys with empty values |
| `docs/guide/` | Human documentation (this tree) |
| `.specs/` | Specs, briefs, gates, session state, archived domain truth |
| `.cursor/skills/` | Agent hub and phase procedures |
| `AGENTS.md` | Agent-agnostic execution contract |
| `CONTRIBUTING.md` | How to change this repo, including README-on-PR |

## Stack

| Layer | Choice |
| --- | --- |
| API | Python 3.10+, FastAPI, asyncio, Pydantic v2 |
| HTTP client | httpx (async) |
| Cache | Redis via redis-py async |
| Local LLM | Ollama (optional; unreachable → one-hop fallback to Gemini) |
| Cloud LLM | Google Gemini (demo / free-tier default) |
| Ship unit | Docker Compose (`api` + `redis`) |
| Tests | pytest-asyncio (routing, cache hit/miss, fallback, quota) |

## Environment

Copy [`.env.example`](../../.env.example) to `.env` (never commit `.env`):

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_URL` | yes in-process; leave blank in `.env` for Compose | Compose hardcodes `redis://redis:6379/0` |
| `OLLAMA_BASE_URL` | yes in-process; Compose fills a default | `http://host.docker.internal:11434` (OK if Ollama is not installed) |
| `GEMINI_API_KEY` | yes | — |
| `GEMINI_MODEL` | no | `gemini-3.5-flash` (override in AI Studio if needed) |
| `GATEWAY_API_KEY` | yes | — (value callers send as `X-API-Key`) |
| `CHAT_DAILY_LIMIT` | no | `5` |
| `CACHE_TTL_SECONDS` | no | `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | `30` |

Never commit `.env`. Secrets are env-only (no `load_dotenv` in the app).

## Tests

```bash
pip install -e ".[dev]"
pytest
```

`pyproject.toml` `addopts` already applies `-m "not live"`. Live upstream tests stay opt-in via their marker; do not expect `pytest` (no extra `-m`) to call Gemini or Ollama.

## Compose

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or another Compose-capable Docker). If `docker` is not on PATH, install/start Docker Desktop and reopen the terminal.

```bash
docker compose up --build
```

- `api` on port **8000** (OpenAPI UI: `/docs`)
- `redis` on port **6379**
- `REDIS_URL` inside the `api` container is always `redis://redis:6379/0` (not taken from `.env`)
- Optional tunables (`CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, `UPSTREAM_TIMEOUT_SECONDS`, `CHAT_DAILY_LIMIT`, `GEMINI_MODEL`, `OLLAMA_BASE_URL`) are interpolated from `.env` with the defaults above
- Ollama is **not** in Compose. If the host cannot run Ollama, leave the default URL: health reports `degraded` and the router falls back to Gemini after one local failure.
- Compose sets `extra_hosts: host.docker.internal:host-gateway` so Linux Docker Engine can reach an optional **host** Ollama the same way Docker Desktop does. That mapping is unused when Ollama is not installed.

Chat callers must send the **same** `GATEWAY_API_KEY` value as `.env`. The shell variable `$GATEWAY_API_KEY` is not set by Compose; substituting an empty header returns HTTP 401. Health probes do not send a key (REQ-020).

Operator walkthrough: [Quick start](Quick-start.md).

## Spec Guardrails

```bash
npx @luizsantiago/spec-guardrails doctor
```

Preset: `python-platform` (see [`.specs/config.yaml`](../../.specs/config.yaml)). Day to day, work in agent chat; the agent calls the CLI when a phase needs it.

Typical Complex order:

```
/elicit → /specify → /discuss? → /plan → /tasks → /loop → /verify → /archive
```

v1 (`001-llm-router-gateway`) is archived. Independent `/verify` PASS: [validation.md](../../.specs/features/001-llm-router-gateway/validation.md). Domain truth: [`.specs/domains/llm-router-gateway/spec.md`](../../.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022). Do not re-ask **D-001–D-012**. Session pointer: [`.specs/STATE.md`](../../.specs/STATE.md).

Hub: [`.cursor/skills/agent-architecture.md`](../../.cursor/skills/agent-architecture.md). Conventional Commits; optional gate: `python .specs/guardrails/scripts/check_commit.py --message "…"`.

## Documentation on every PR

**C-008** and **C-009:** every pull request that changes product behavior, API, setup, architecture, or public status **must update documentation in that same PR** — not a follow-up.

1. **Update [`README.md`](../../README.md)** — status, Quick start, pillars, contract, and Limitations / Still open stay true.
2. **Update matching pages under `docs/guide/`** — Overview, Quick-start, How-it-works, Architecture, API, Development, concepts, FAQ, Glossary, Limitations as needed. Add a page only when an existing one cannot hold the change; link it from [guide README](README.md).
3. **Keep spec memory in sync** — [`.specs/project/PROJECT.md`](../../.specs/project/PROJECT.md) and [`ROADMAP.md`](../../.specs/project/ROADMAP.md) reflect current vision and milestones.
4. **Write artifacts in English** — README, `docs/`, `.specs/`, commits, and PR bodies (see engineering baseline).

Skip README only when the diff is purely internal (for example a typo in a gate script) and no operator-facing sentence became stale. When in doubt, update the README.

Cursor rules: `.cursor/rules/pr-documentation.mdc` · `.cursor/rules/engineering-baseline.mdc`. Also [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Out of scope / deferred

See [Limitations](Limitations.md) and the root [README → Still open](../../README.md#still-open-agents-read-this). Streaming, production multi-tenant auth, semantic cache, RAG/tools, paid OpenAI happy path, K8s, and hosted deploy are **not** in this demo unless the owner starts a new feature.
