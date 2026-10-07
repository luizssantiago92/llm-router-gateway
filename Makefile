.PHONY: dev test lint demo

dev:
	docker compose up --build

test:
	uv run pytest

lint:
	uv run ruff check app tests
	uv run ruff format --check
	uv run mypy

demo:
	docker compose -f compose.demo.yml up --build
