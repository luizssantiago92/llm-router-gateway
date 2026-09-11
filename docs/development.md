# Development

Application source lives in `app/`. Tests live in `tests/`. Work stays spec-first under Spec Guardrails (`python-platform`).

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

## Toolchain

- Python 3.10+, FastAPI, asyncio, httpx, redis-py async, Pydantic v2
- pytest-asyncio for routing, cache hit/miss, fallback, and quota (`pytest -m "not live"` by default)
- Docker Compose for the app and Redis
- Conventional Commits; `python3 .specs/guardrails/scripts/check_commit.py --message "…"`

## Environment

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_URL` | yes | Compose: `redis://redis:6379/0` |
| `OLLAMA_BASE_URL` | yes | Compose default `http://host.docker.internal:11434` |
| `GEMINI_API_KEY` | yes | — |
| `GEMINI_MODEL` | no | `gemini-2.0-flash` |
| `GATEWAY_API_KEY` | yes | — (value callers send as `X-API-Key`) |
| `CHAT_DAILY_LIMIT` | no | `5` |
| `CACHE_TTL_SECONDS` | no | `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | `30` |

Never commit `.env`. Secrets are env-only (no `load_dotenv` in the app).

```bash
pip install -e ".[dev]"
pytest
npx @luizsantiago/spec-guardrails doctor
```

## Agent phases

Typical order for this product (Complex):

```
/elicit (done) → /specify (done) → /discuss (done) → /plan (done) → /tasks (done) → /loop (done) → /verify (PASS) → /archive (done)
```

Historical feature: [`.specs/features/001-llm-router-gateway/spec.md`](../.specs/features/001-llm-router-gateway/spec.md). Tasks: [`.specs/features/001-llm-router-gateway/tasks.md`](../.specs/features/001-llm-router-gateway/tasks.md). Domain truth: [`.specs/domains/llm-router-gateway/spec.md`](../.specs/domains/llm-router-gateway/spec.md). Do not re-ask **D-001–D-012**. Session pointer: [`.specs/STATE.md`](../.specs/STATE.md).

v1 is archived. Independent `/verify` PASS: [validation.md](../.specs/features/001-llm-router-gateway/validation.md). Next work is `feature-init` against the domain spec.

## Documentation on every PR

Every pull request that changes the product, process, or operator-facing setup **must**:

1. **Update [`README.md`](../README.md)** — status, stack, API summary, and links stay true.
2. **Update or add pages under `docs/`** — architecture, API, and development match what the PR actually ships. Add a page only when an existing one cannot hold the change.
3. **Keep spec memory in sync** — [`.specs/project/PROJECT.md`](../.specs/project/PROJECT.md) and [`ROADMAP.md`](../.specs/project/ROADMAP.md) reflect current vision and milestones.
4. **Write artifacts in English** — README, `docs/`, `.specs/`, commits, and PR bodies (see engineering baseline).

Skip README edits only when the diff is purely internal (for example a typo in a gate script) and no status or link is stale. When in doubt, update the README.

This policy is also an always-on Cursor rule: `.cursor/rules/pr-documentation.mdc`.

## Out of scope (still)

Streaming, semantic cache, multi-tenancy, RAG/tool-use, Kubernetes, paid OpenAI happy path. Minimal `X-API-Key` + daily quota are in for the zero-cost demo.
