# Operations

How to run, configure, and test the demo. The system description is [Architecture](architecture.md). The HTTP contract is [API](api.md).

## Zero-key local demo

No Gemini key is required:

```bash
docker compose -f compose.demo.yml up --build
```

The gateway key is `demo`. `scripts/demo.sh` checks health, sends `hello`, repeats it (cache hit), and sends `simulate-local-failure` so the local demo provider fails and the cloud demo provider answers. `simulate-cloud-failure` fails the cloud provider. `make demo` is the same Compose command. Leave `PROVIDER_MODE` unset to keep the live Ollama and Gemini adapters.

## Live Compose

Copy `.env.example` to `.env` and fill three values. Never commit `.env`.

| Variable | What to put |
| --- | --- |
| `GEMINI_API_KEY` | From Google AI Studio |
| `GATEWAY_API_KEY` | A secret you invent. Callers send it as `X-API-Key` or `Authorization: Bearer`. |
| `REDIS_PASSWORD` | A URL-safe secret. Compose refuses an empty value. |

```bash
docker compose up --build
```

`make dev` is the same command.

| Service | Publish |
| --- | --- |
| `api` | `127.0.0.1:8000` only. OpenAPI UI: `/docs` |
| `redis` | `127.0.0.1:6379` only. Image pinned by digest. `--requirepass` from `REDIS_PASSWORD`. |

Compose waits until Redis answers `PING`, then starts the API. Both services restart unless stopped. The image probes `GET /health/live`. `REDIS_URL` inside the `api` container is always `redis://:<REDIS_PASSWORD>@redis:6379/0`. The app does not call `load_dotenv`.

Ollama is optional and is not in Compose. Without it, `GET /health` is HTTP 200 `degraded` and simple prompts fall back to Gemini. Linux Docker Engine reaches a host Ollama through `host.docker.internal` → `host-gateway`.

## Environment

| Variable | Required | Default |
| --- | --- | --- |
| `REDIS_PASSWORD` | yes for Compose | URL-safe secret |
| `REDIS_URL` | yes in-process | Compose sets it. Leave it blank in `.env` when using Compose. |
| `OLLAMA_BASE_URL` | yes in live in-process mode | `http://host.docker.internal:11434` |
| `GEMINI_API_KEY` | yes in live mode | — |
| `GEMINI_MODEL` | no | `gemini-3.5-flash` |
| `GATEWAY_API_KEY` | yes in live mode | Demo mode uses `demo` when this is unset. |
| `PROVIDER_MODE` | no | `live`. `demo` uses the echo providers. |
| `CHAT_DAILY_LIMIT` | no | `5` |
| `CACHE_TTL_SECONDS` | no | `3600` |
| `COMPLEXITY_WORD_THRESHOLD` | no | `150` |
| `UPSTREAM_TIMEOUT_SECONDS` | no | `30` |
| `MAX_MESSAGE_CHARS` | no | `32000` (cannot exceed this ceiling) |
| `MAX_MESSAGES` | no | `50` |
| `MAX_TOTAL_MESSAGE_CHARS` | no | `64000` |
| `MIN_TEMPERATURE` / `MAX_TEMPERATURE` | no | `0` / `2` |
| `MIN_MAX_TOKENS` / `MAX_MAX_TOKENS` | no | `1` / `4096` |
| `MAX_BODY_BYTES` | no | `262144` |

`PROVIDER_MODE` is read by the process and is not listed in `.env.example`.

## Checks

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/health/live
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_GATEWAY_KEY" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"temperature":0.2,"max_tokens":64}'
```

| Result | Meaning |
| --- | --- |
| Health 200 `ok` | Redis and both providers are up |
| Health 200 `degraded` | Redis is up and at least one provider is down |
| Health 503 `down` | Redis is down |
| Chat 200 `provider: cloud` | Gemini served a miss (typical without Ollama) |
| Chat 200 `cached: true` | Repeat of the same messages, temperature, and max tokens |
| 401 | Missing or wrong credential. The shell variable is not set by Compose. |
| 413 | Valid credential and a body over 256 KiB |
| 429 | Daily miss quota exhausted |
| 422 | Invalid body or `stream: true` |
| 502 | Both hops failed, or the primary returned a non-retryable 4xx |
| 503 | Quota store could not be updated |

To wipe cache and quota during a demo, `docker compose restart redis`. The bucket also resets at UTC midnight.

## Tests and shortcuts

```bash
uv sync --frozen
uv run ruff check app tests
uv run ruff format --check
uv run mypy
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
```

`uv sync` installs the dev group from `uv.lock`. CI runs those commands on Python 3.10, 3.12, and 3.13. `pytest` already skips `@pytest.mark.live`. Branch coverage must stay at or above 90%.

| Command | What it does |
| --- | --- |
| `make dev` | `docker compose up --build` |
| `make test` | `uv run pytest` |
| `make lint` | ruff check, ruff format, and mypy |
| `make demo` | `docker compose -f compose.demo.yml up --build` |

## Common questions

**Why is health `degraded`?** Ollama is optional. Local health fails and Gemini can still be up.

**Why 401?** The header must equal `GATEWAY_API_KEY` from `.env`. An empty shell variable is not that value.

**Why 429 after a few chats?** Misses consume the daily bucket (default 5). Repeats are free.

**Why 502 when Gemini returns 4xx?** That failure is not hopped. The route still returns 502.

**Does `.env` `REDIS_URL` change Compose?** No. The `api` service always receives the Compose URL. Set `REDIS_URL` only when you run the process outside Compose.

**Where does the Gemini key go?** The `x-goog-api-key` header, not the query string.

## Changing the repository

Pull requests are squash-merged. The pull request title is the commit subject. Use Conventional Commits (`feat:`, `fix:`, `docs:`), a lowercase-initial subject, and no trailing period.

A pull request that changes behavior, setup, or public status updates `README.md` and the matching page among `docs/architecture.md`, `docs/api.md`, and `docs/operations.md` in that same pull request. Contributor workflow: [CONTRIBUTING](../CONTRIBUTING.md). Vulnerability reports: [SECURITY](../SECURITY.md).
