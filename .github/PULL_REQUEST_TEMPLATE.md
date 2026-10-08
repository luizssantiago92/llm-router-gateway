## Summary

<!-- What changed, and why. -->

## Test plan

- [ ] `uv run ruff check app tests`
- [ ] `uv run ruff format --check`
- [ ] `uv run mypy`
- [ ] `uv run pytest --cov --cov-report=term-missing --cov-fail-under=90`

## Notes

- This repository squash-merges. The pull request title is the commit subject (Conventional Commits, lowercase-initial, no trailing period).
- If behavior, setup, or public status changed, update `README.md` and the matching page among `docs/architecture.md`, `docs/api.md`, and `docs/operations.md` in this pull request.
- Do not paste API keys, tokens, or `.env` contents.
