"""Version 1.0.0 is the application version and the changelog heading."""

from pathlib import Path

from app import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_application_version_returns_1_0_0() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert __version__ == "1.0.0"
    assert 'version = "1.0.0"' in project


def test_changelog_returns_a_1_0_0_heading() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [1.0.0] - 2026-10-08" in text
    assert "## [0.1.0] - 2026-10-07" in text
    assert "85% branch-coverage gate" in text
