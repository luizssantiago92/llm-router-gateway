"""Recruiter front page: headings, badges, and the OpenAPI image size."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _page() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def _section(heading: str) -> str:
    text = _page()
    start = text.index(heading)
    rest = text[start + len(heading) :]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


def test_front_page_returns_a_one_minute_demo_heading() -> None:
    assert "## Try it in 1 minute" in _page()
    demo = _section("## Try it in 1 minute")
    assert "compose.demo.yml" in demo
    assert "scripts/demo.sh" in demo


def test_front_page_returns_an_engineering_decisions_heading() -> None:
    assert "## Engineering decisions" in _page()
    decisions = _section("## Engineering decisions")
    assert "exact match" in decisions
    assert "scrypt" in decisions


def test_swagger_image_returns_under_80_kilobytes() -> None:
    image = ROOT / "docs" / "assets" / "swagger.webp"
    data = image.read_bytes()
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WEBP"
    assert len(data) <= 80 * 1024
    assert "docs/assets/swagger.webp" in _page()


def test_cache_animation_is_a_webp() -> None:
    data = (ROOT / "docs" / "assets" / "cache.webp").read_bytes()
    assert data[:4] == b"RIFF"
    assert b"ANIM" in data
    assert "docs/assets/cache.webp" in _page()


def test_front_page_shows_badges_icon_and_mermaid() -> None:
    text = _page()
    assert "docs/assets/icon.png" in text
    assert "workflows/ci.yml/badge.svg" in text
    assert "workflows/codeql.yml/badge.svg" in text
    assert "license-MIT" in text
    assert "python-3.10" in text
    assert "```mermaid" in text
    assert (ROOT / "docs" / "assets" / "icon.svg").is_file()
    assert (ROOT / "docs" / "assets" / "icon.png").is_file()


def test_limitations_have_no_fixed_test_count() -> None:
    import re

    limitations = _section("## Limitations")
    assert "production chatbot" in limitations
    assert re.search(r"\d+\s+tests", limitations) is None
