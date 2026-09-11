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
| Local LLM | Ollama (vLLM adapter-ready) |
| Cloud LLM | OpenAI (Anthropic adapter-ready) |
| Ship unit | Docker Compose (`api` + `redis`) |
| Tests | pytest-asyncio (routing, cache hit/miss, fallback) |

## Environment

Copy [`.env.example`](../.env.example) to `.env` (never commit `.env`):

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_URL` | yes | — (Compose sets `redis://redis:6379/0`) |
| `OLLAMA_BASE_URL` | yes | — (Compose default `http://ollama:11434`; override to your host Ollama) |
| `OPENAI_API_KEY` | yes | — |
| `OPENAI_MODEL` | no | `gpt-4o-mini` |
| `CACHE_TTL_SECONDS` | no | `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | `30` |

Secrets and upstream URLs come from the environment only (no `load_dotenv` in the app).

## Tests

```bash
pip install -e ".[dev]"
pytest -m "not live"
```

Default CI/local gate skips live upstream markers. Full suite without the exclude: `pytest`.

## Compose

```bash
docker compose up --build
```

- `api` on port **8000**
- `redis` on port **6379**
- Ollama is **not** in Compose — it must be reachable at `OLLAMA_BASE_URL` (on Windows/Docker Desktop, `host.docker.internal:11434` is a common host override)

## Spec Guardrails

```bash
npx @luizsantiago/spec-guardrails doctor
```

Preset: `python-platform` (see [`.specs/config.yaml`](../.specs/config.yaml)). Day to day, work in agent chat; the agent calls the CLI when a phase needs it.

Typical Complex order:

```
/elicit → /specify → /discuss? → /plan → /tasks → /loop → /verify → /archive
```

v1 (`001-llm-router-gateway`) is archived. Independent `/verify` PASS: [validation.md](../.specs/features/001-llm-router-gateway/validation.md). Domain truth: [`.specs/domains/llm-router-gateway/spec.md`](../.specs/domains/llm-router-gateway/spec.md). Do not re-ask **D-001–D-012**. Next product change starts with `feature-init` against the domain. Session pointer: [`.specs/STATE.md`](../.specs/STATE.md).

Hub: [`.cursor/skills/agent-architecture.md`](../.cursor/skills/agent-architecture.md). Conventional Commits; optional gate: `python .specs/guardrails/scripts/check_commit.py --message "…"`.

## Documentation on every PR

Every pull request that changes the product, process, or operator-facing setup **must**:

1. **Update [`README.md`](../README.md)** — product status, quick start, and doc links stay true.
2. **Update or add pages under `docs/`** — architecture, API, and development match what the PR actually ships. Add a page only when an existing one cannot hold the change.
3. **Keep spec memory in sync** — [`.specs/project/PROJECT.md`](../.specs/project/PROJECT.md) and [`ROADMAP.md`](../.specs/project/ROADMAP.md) reflect current vision and milestones.
4. **Write artifacts in English** — README, `docs/`, `.specs/`, commits, and PR bodies (see engineering baseline).

Skip README edits only when the diff is purely internal (for example a typo in a gate script) and no status or link is stale. When in doubt, update the README.

This policy is also an always-on Cursor rule: `.cursor/rules/pr-documentation.mdc` (C-008).

## Out of scope for v1

Streaming, edge auth, semantic cache, admin UI, rate limits, multi-tenancy, RAG/tool-use, Kubernetes. Full list: brief § Constraints.
