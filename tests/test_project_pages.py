"""Canonical pages, changelog, and GitHub templates."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_root_changelog_returns_a_keep_a_changelog_heading() -> None:
    text = _text("CHANGELOG.md")
    assert "Keep a Changelog" in text
    assert "## [Unreleased]" in text
    assert "## [0.1.0] - 2026-10-07" in text
    assert "85% branch-coverage gate" in text


def test_architecture_page_returns_the_request_path() -> None:
    text = _text("docs/architecture.md")
    assert "POST /v1/chat/completions" in text
    assert "127.0.0.1:8000" in text
    assert "one hop" in text


def test_api_page_returns_chat_status_codes() -> None:
    text = _text("docs/api.md")
    assert "401" in text
    assert "413" in text
    assert "quota store unavailable" in text


def test_operations_page_returns_compose_commands() -> None:
    text = _text("docs/operations.md")
    assert "docker compose up --build" in text
    assert "make demo" in text
    assert "PROVIDER_MODE" in text


def test_contributing_returns_squash_uv_and_retornatus() -> None:
    text = _text("CONTRIBUTING.md").lower()
    assert "squash-merged" in text
    assert "uv sync --frozen" in text
    assert "retornatus" in text


def test_vulnerability_page_returns_the_private_reporting_address() -> None:
    text = _text("SECURITY.md")
    assert "https://github.com/luizssantiago92/llm-router-gateway/security/advisories/new" in text
    assert "127.0.0.1:8000" in text


def test_pull_request_template_returns_a_test_plan() -> None:
    text = _text(".github/PULL_REQUEST_TEMPLATE.md")
    assert "## Test plan" in text
    assert "uv run pytest" in text
    assert "squash-merges" in text


def test_bug_form_returns_a_required_description() -> None:
    text = _text(".github/ISSUE_TEMPLATE/bug_report.yml")
    assert "id: description" in text
    assert "required: true" in text
    assert 'labels: ["bug"]' in text


def test_issue_chooser_points_at_private_reporting() -> None:
    text = _text(".github/ISSUE_TEMPLATE/config.yml")
    assert "blank_issues_enabled: false" in text
    assert "/security/advisories/new" in text


def test_history_pages_remain() -> None:
    history = ROOT / "docs" / "history"
    assert (history / "domain-spec.md").is_file()
    assert (history / "design.md").is_file()
    assert (history / "PRD.pt-BR.md").is_file()


def test_guide_pages_point_at_the_canonical_pages() -> None:
    assert "../architecture.md" in _text("docs/guide/Architecture.md")
    assert "../api.md" in _text("docs/guide/API.md")
    assert "../operations.md" in _text("docs/guide/Quick-start.md")
