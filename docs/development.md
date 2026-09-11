# Development

Application source lives in `app/`. Tests live in `tests/`. Work stays spec-first under [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) with the `python-platform` preset.

## Repository map

| Path | Purpose |
| --- | --- |
| `prd.md` | Product requirements (owner kickoff) |
| `app/` | FastAPI gateway (settings, schemas, cache, routing, providers, routes) |
| `tests/` | pytest-asyncio suite; `tests/eval/` golden routing harness |
| `docker-compose.yml` / `Dockerfile` | Ship unit: `api` + `redis` |
| `.env.example` | Required env keys with empty values |
| `docs/` | Human documentation (this tree) |
| `.specs/` | Specs, briefs, gates, session state, archived domain truth |
| `.cursor/skills/` | Agent hub and phase procedures |
| `AGENTS.md` | Agent-agnostic execution contract |

## Stack

| Layer | Choice |
| --- | --- |
| API | Python 3.10+, FastAPI, asyncio, Pydantic v2 |
| HTTP client | httpx (async) |
| Cache | Redis via redis-py async |
| Local LLM | Ollama (optional; falha → fallback Gemini) |
| Cloud LLM | Google Gemini (demo / free-tier default) |
| Ship unit | Docker Compose (`api` + `redis`) |
| Tests | pytest-asyncio (routing, cache hit/miss, fallback, quota) |

## Environment

Copy [`.env.example`](../.env.example) to `.env` (never commit `.env`):

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_URL` | yes | Compose: `redis://redis:6379/0` |
| `OLLAMA_BASE_URL` | yes | Compose default `http://host.docker.internal:11434` (placeholder OK if Ollama is not installed) |
| `GEMINI_API_KEY` | yes | — |
| `GEMINI_MODEL` | no | `gemini-3.5-flash` (or `gemini-3.6-flash` if listed in AI Studio) |
| `GATEWAY_API_KEY` | yes | — (value callers send as `X-API-Key`) |
| `CHAT_DAILY_LIMIT` | no | `5` |
| `CACHE_TTL_SECONDS` | no | `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | `30` |

Never commit `.env`. Secrets are env-only (no `load_dotenv` in the app).

## Tests

```bash
pip install -e ".[dev]"
pytest -m "not live"
```

Default CI/local gate skips live upstream markers. Full suite without the exclude: `pytest`.

## Compose

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or another Compose-capable Docker). If `docker` is not on PATH, install/start Docker Desktop and reopen the terminal.

```bash
docker compose up --build
```

- `api` on port **8000**
- `redis` on port **6379**
- Ollama is **not** in Compose. If the host cannot run Ollama, leave the default URL: health reports `degraded` and the router falls back to Gemini after one local failure.

## Spec Guardrails

```bash
npx @luizsantiago/spec-guardrails doctor
```

Preset: `python-platform` (see [`.specs/config.yaml`](../.specs/config.yaml)). Day to day, work in agent chat; the agent calls the CLI when a phase needs it.

Typical Complex order:

```
/elicit → /specify → /discuss? → /plan → /tasks → /loop → /verify → /archive
```

v1 (`001-llm-router-gateway`) is archived. Independent `/verify` PASS: [validation.md](../.specs/features/001-llm-router-gateway/validation.md). Domain truth: [`.specs/domains/llm-router-gateway/spec.md`](../.specs/domains/llm-router-gateway/spec.md) (REQ-001–REQ-022). Do not re-ask **D-001–D-012**. Session pointer: [`.specs/STATE.md`](../.specs/STATE.md).

Hub: [`.cursor/skills/agent-architecture.md`](../.cursor/skills/agent-architecture.md). Conventional Commits; optional gate: `python .specs/guardrails/scripts/check_commit.py --message "…"`.

## Documentation on every PR

Every pull request that changes the product, process, or operator-facing setup **must**:

1. **Update [`README.md`](../README.md)** — product status, quick start, and doc links stay true.
2. **Update or add pages under `docs/`** — architecture, API, and development match what the PR actually ships. Add a page only when an existing one cannot hold the change.
3. **Keep spec memory in sync** — [`.specs/project/PROJECT.md`](../.specs/project/PROJECT.md) and [`ROADMAP.md`](../.specs/project/ROADMAP.md) reflect current vision and milestones.
4. **Write artifacts in English** — README, `docs/`, `.specs/`, commits, and PR bodies (see engineering baseline).

Skip README edits only when the diff is purely internal (for example a typo in a gate script) and no status or link is stale. When in doubt, update the README.

This policy is also an always-on Cursor rule: `.cursor/rules/pr-documentation.mdc` (C-008).

## Out of scope (still)

Streaming, semantic cache, multi-tenancy, RAG/tool-use, Kubernetes, paid OpenAI happy path. Minimal `X-API-Key` + daily quota are in for the zero-cost demo.
