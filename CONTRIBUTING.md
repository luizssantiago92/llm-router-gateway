# Contributing

Thanks for improving LLM Router Gateway.

Chat may be in any language. **Artifacts stay in English:** code, tests, comments, commits, PR titles/bodies, `README.md`, and `docs/`.

## Documentation on every significant PR

If the PR changes **product behavior, API, setup, architecture, or public status**, the **same PR** must:

1. Update root [`README.md`](README.md) so operators are not reading a lie.
2. Update matching pages under [`docs/guide/`](docs/guide/README.md) (add a page only when an existing one cannot hold the change; link it from the guide index).

Skip the README only for purely internal diffs where no operator-facing sentence went stale. **When in doubt, update the README.** Do not open a docs follow-up instead of documenting the change you just shipped.

Procedure: [docs/guide/Development.md](docs/guide/Development.md#documentation-on-every-pr).

## Basics

- Prefer small, focused diffs.
- Never commit secrets, API keys, or `.env`.
- Conventional Commits (`feat:`, `fix:`, `docs:`, …); subject lowercase-initial, no trailing period.

```bash
uv sync --frozen --all-extras
uv run ruff check app tests
uv run pytest
```

`pip install -e ".[dev]"` still works. CI uses `uv.lock`.

`pytest` already skips `@pytest.mark.live` via `pyproject.toml` `addopts`.

## Layout

| Path | Role |
| --- | --- |
| `app/` | FastAPI gateway |
| `tests/` | pytest-asyncio + eval harness |
| `docs/guide/` | Human guides (Overview, Quick start, …) |
| `docs/history/` | Archived PRD, domain spec, and feature design |
| `README.md` | Product entry point |

## Out of scope

Do not grow streaming, production auth, RAG, paid OpenAI, or Kubernetes here. See [Limitations](docs/guide/Limitations.md).
