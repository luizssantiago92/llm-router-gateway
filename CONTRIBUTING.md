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
uv sync --frozen
uv run ruff check app tests
uv run ruff format --check
uv run mypy app
uv export --frozen --no-emit-project | uv run pip-audit -r /dev/stdin --progress-spinner off --disable-pip
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
```

`uv sync` installs the `dev` dependency group. CI uses `uv.lock` and runs those commands on Python 3.10, 3.12, and 3.13. The coverage gate is 90% branch coverage.

`pytest` already skips `@pytest.mark.live` via `pyproject.toml` `addopts`.

## Agent governance

This repo uses [Retornatus](https://github.com/luizssantiago92/retornatus) Changes under [`.retornatus/`](.retornatus/config.toml). Spec Guardrails agent packs are not used here.

Retornatus is a CLI tool install, not an application dependency. The package requires Python 3.11+, and CI still syncs this project on Python 3.10, so it stays out of `pyproject.toml`. The pull-request job installs it itself.

```bash
uv tool install "retornatus==1.9.1"
retornatus doctor
```

Create a Change before the work (`retornatus change elicit`, then `retornatus change create`) and keep the Contract active. Record proof with `retornatus checks run` or `retornatus evidence run`, then `retornatus verify`. [`.github/workflows/retornatus.yml`](.github/workflows/retornatus.yml) runs `luizssantiago92/retornatus@v1` on pull requests. Dependabot diffs that only touch dependency manifests warn on the omission gate instead of failing. The ruff, format, mypy, pip-audit, pytest, and CodeQL jobs stay in place.

Cursor reads [`.cursor/rules/retornatus.mdc`](.cursor/rules/retornatus.mdc) and the hub skill at [`.cursor/skills/retornatus/SKILL.md`](.cursor/skills/retornatus/SKILL.md). The preset is `fastapi` (pytest, ruff, ruff format, mypy). `ruff check` lists `app` and `tests` because this repo has no `src/` tree.

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
