# Contributing

Thanks for improving LLM Router Gateway.

Chat may be in any language. **Artifacts stay in English:** code, tests, comments, commits, PR titles/bodies, `README.md`, and `docs/`.

## Documentation on every significant PR

If the PR changes **product behavior, the HTTP contract, setup, architecture, or public status**, the **same PR** must:

1. Update root [`README.md`](README.md) so operators are not reading a lie.
2. Update the matching page: [`docs/architecture.md`](docs/architecture.md), [`docs/api.md`](docs/api.md), or [`docs/operations.md`](docs/operations.md).

Skip the README only for purely internal diffs where no operator-facing sentence went stale. **When in doubt, update the README.** Do not open a follow-up instead of recording the change you just shipped.

Procedure: [docs/operations.md](docs/operations.md#changing-the-repository).

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

`uv sync` installs the `dev` dependency group. CI uses `uv.lock` and runs those commands on Python 3.10, 3.12, and 3.13. The coverage gate is 90% branch coverage. `make test` runs pytest, `make lint` runs ruff and mypy, `make dev` starts Compose, and `make demo` starts the zero-key compose file.

`pytest` already skips `@pytest.mark.live` via `pyproject.toml` `addopts`.

## Squash merges

Pull requests are squash-merged. The pull request title is the commit subject on `main`. Use Conventional Commits (`feat:`, `fix:`, `docs:`), a lowercase-initial subject, and no trailing period. Keep the branch diff focused so the squash commit stays one change.

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
| `docs/architecture.md` | System description |
| `docs/api.md` | HTTP contract |
| `docs/operations.md` | Run, configure, and test |
| `docs/history/` | Archived PRD, domain spec, and feature design |
| `docs/guide/` | Short pointers to the three pages above |
| `README.md` | Product entry point |
| `CHANGELOG.md` | Keep a Changelog record |

## Out of scope

Do not grow streaming, production auth, RAG, paid OpenAI, or Kubernetes here. See [Limitations](docs/architecture.md#limitations).
