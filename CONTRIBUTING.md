# Contributing

Thanks for improving LLM Router Gateway.

Chat may be in any language. **Artifacts stay in English:** code, tests, comments, commits, PR titles/bodies, `README.md`, `docs/`, and `.specs/`.

## Use Spec Guardrails on the change

This repo already has [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) (`python-platform`). For anything beyond a typo:

```
/specify  →  /tasks  →  /loop  →  /verify
```

Keep `.specs/` as the source of truth for what you built and how you proved it. Do not re-ask **D-001–D-012**.

## Documentation on every significant PR (C-008 / C-009)

If the PR changes **product behavior, API, setup, architecture, or public status**, the **same PR** must:

1. Update root [`README.md`](README.md) so operators are not reading a lie.
2. Update matching pages under [`docs/guide/`](docs/guide/README.md) (add a page only when an existing one cannot hold the change; link it from the guide index).
3. Keep [`.specs/project/PROJECT.md`](.specs/project/PROJECT.md) and [`ROADMAP.md`](.specs/project/ROADMAP.md) current.

Skip the README only for purely internal diffs (for example a gate-script typo) where no operator-facing sentence went stale. **When in doubt, update the README.** Do not open a “docs follow-up” instead of documenting the change you just shipped.

Cursor rules: `.cursor/rules/pr-documentation.mdc` · `.cursor/rules/engineering-baseline.mdc`. Procedure: [docs/guide/Development.md](docs/guide/Development.md#documentation-on-every-pr).

## Basics

- Prefer small, focused diffs.
- Never commit secrets, API keys, or `.env`.
- Conventional Commits (`feat:`, `fix:`, `docs:`, …); subject lowercase-initial, no trailing period.

```bash
pip install -e ".[dev]"
pytest
python3 .specs/guardrails/scripts/check_commit.py --message "docs: explain quota refund"
```

`pytest` already skips `@pytest.mark.live` via `pyproject.toml` `addopts`.

## Layout

| Path | Role |
| --- | --- |
| `app/` | FastAPI gateway |
| `tests/` | pytest-asyncio + eval harness |
| `docs/guide/` | Human guides (Overview, Quick start, …) |
| `.specs/` | Specs, gates, session state |
| `README.md` | Product entry point |

## Out of scope

Do not grow streaming, production auth, RAG, paid OpenAI, or K8s here without owner `feature-init`. See [Limitations](docs/guide/Limitations.md) and [README Still open](README.md#still-open-agents-read-this).
