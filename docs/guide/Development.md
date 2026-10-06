# Development

Application source lives in `app/`. Tests live in `tests/`.

Human docs live in this `docs/guide/` tree. The root [README](../../README.md) is the product entry point.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/history/PRD.pt-BR.md` | Product requirements (owner kickoff; historical cloud examples) |
| `app/` | FastAPI gateway (settings, schemas, cache, routing, providers, routes) |
| `tests/` | pytest-asyncio suite; `tests/eval/` golden routing harness |
| `docker-compose.yml` / `Dockerfile` | Ship unit: `api` + Redis (loopback port, password, non-root image) |
| `.github/workflows/ci.yml` | Ruff check, ruff format, mypy, pytest with an 85% branch-coverage gate, and pip-audit on Python 3.10, 3.12, and 3.13; actions pinned by commit SHA |
| `.github/workflows/retornatus.yml` | Retornatus verify and diff gates on pull requests (`luizssantiago92/retornatus@v1`) |
| `.github/workflows/codeql.yml` | CodeQL analysis for Python and GitHub Actions; weekly schedule |
| `.retornatus/` | Retornatus Changes, Contracts, and Evidence (agent governance; not Spec Guardrails) |
| `.github/dependabot.yml` | Weekly grouped minor/patch updates for `uv` (lockfile) and GitHub Actions |
| `uv.lock` | Locked runtime and dev dependencies (`[dependency-groups] dev`) |
| `.env.example` | Required env keys with empty values |
| `SECURITY.md` | Private vulnerability reports |
| `docs/guide/` | Human documentation (this tree) |
| `docs/history/` | Archived PRD, domain spec (REQ-001–REQ-022), and feature design |
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
| Tests | pytest-asyncio (routing, cache hit/miss, fallback, quota); CI on GitHub Actions (Python 3.10, 3.12, 3.13) |
| Packages | `uv.lock` with upper bounds; dev tools in the uv `dev` group (`uv sync`) |

## Environment

Copy [`.env.example`](../../.env.example) to `.env` (never commit `.env`):

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_PASSWORD` | yes for Compose | URL-safe secret; Compose refuses an empty value |
| `REDIS_URL` | yes in-process; leave blank in `.env` for Compose | Compose sets `redis://:<REDIS_PASSWORD>@redis:6379/0` |
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
uv sync --frozen
uv run ruff check app tests
uv run ruff format --check
uv run mypy app
uv export --frozen --no-emit-project | uv run pip-audit -r /dev/stdin --progress-spinner off --disable-pip
uv run pytest --cov --cov-report=term-missing --cov-fail-under=85
```

`uv sync` installs the `dev` group from `uv.lock` (pytest, ruff, mypy, pip-audit, pytest-cov). CI (`.github/workflows/ci.yml`) runs the same commands on Python 3.10, 3.12, and 3.13. `pip-audit --disable-pip` reads the hashed lock export directly, so it does not build a temporary virtualenv (that path fails on uv's CPython 3.10). `pyproject.toml` `addopts` already applies `-m "not live"`. Live upstream tests stay opt-in via their marker; do not expect `pytest` (no extra `-m`) to call Gemini or Ollama. Coverage is configured (`source = app`, branch coverage, missing lines). The suite is about 86% branch coverage today, so CI fails under 85%. A later test pass raises that floor to 90%.

## Compose

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or another Compose-capable Docker). If `docker` is not on PATH, install/start Docker Desktop and reopen the terminal.

```bash
docker compose up --build
```

- `api` on port **8000** (OpenAPI UI: `/docs`)
- `redis` on **127.0.0.1:6379** only, with `--requirepass` set from `REDIS_PASSWORD`
- `REDIS_URL` inside the `api` container is always `redis://:<REDIS_PASSWORD>@redis:6379/0` (not taken from `.env`)
- The image runs as non-root user `app`; the base image is pinned by digest
- Optional tunables (`CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, `UPSTREAM_TIMEOUT_SECONDS`, `CHAT_DAILY_LIMIT`, `GEMINI_MODEL`, `OLLAMA_BASE_URL`) are interpolated from `.env` with the defaults above
- Ollama is **not** in Compose. If the host cannot run Ollama, leave the default URL: health reports `degraded` and the router falls back to Gemini after one local failure.
- Compose sets `extra_hosts: host.docker.internal:host-gateway` so Linux Docker Engine can reach an optional **host** Ollama the same way Docker Desktop does. That mapping is unused when Ollama is not installed.

Chat callers must send the **same** `GATEWAY_API_KEY` value as `.env`. The shell variable `$GATEWAY_API_KEY` is not set by Compose; substituting an empty header returns HTTP 401. Health probes do not send a key (REQ-020).

Operator walkthrough: [Quick start](Quick-start.md).

Archived requirements: [domain spec](../history/domain-spec.md) (REQ-001–REQ-022) and [feature design](../history/design.md).

## Documentation on every PR

Every pull request that changes product behavior, API, setup, architecture, or public status **must update documentation in that same PR** — not a follow-up.

1. **Update [`README.md`](../../README.md)** — status, Quick start, contract, and limitations stay true.
2. **Update matching pages under `docs/guide/`** — Overview, Quick-start, How-it-works, Architecture, API, Development, concepts, FAQ, Glossary, Limitations as needed. Add a page only when an existing one cannot hold the change; link it from [guide README](README.md).
3. **Write artifacts in English** — README, `docs/`, commits, and PR bodies.

Skip README only when the diff is purely internal and no operator-facing sentence became stale. When in doubt, update the README.

Also [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Agent governance

Contributors and coding agents use Retornatus Changes, not Spec Guardrails. The CLI is installed with `uv tool install "retornatus==1.9.1"` (Python 3.11+). It is not a `pyproject.toml` dependency, because this repo's CI still runs on Python 3.10. State lives in [`.retornatus/`](../../.retornatus/config.toml). The pull-request check is [`.github/workflows/retornatus.yml`](../../.github/workflows/retornatus.yml). See [CONTRIBUTING](../../CONTRIBUTING.md#agent-governance).

## Out of scope / deferred

See [Limitations](Limitations.md). Streaming, production multi-tenant auth, semantic cache, RAG/tools, paid OpenAI happy path, Kubernetes, and hosted deploy are **not** in this demo.
