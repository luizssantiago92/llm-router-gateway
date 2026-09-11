"""Prompt complexity evaluator (size or keyword match)."""

from __future__ import annotations

KEYWORDS = (
    "code",
    "algorithm",
    "implement",
    "debug",
    "function",
    "class",
    "step by step",
    "reason",
)


def classify(
    messages: list[dict[str, str]],
    word_threshold: int = 150,
) -> str:
    text = " ".join(str(item.get("content", "")) for item in messages)
    words = text.split()
    if len(words) > word_threshold:
        return "complex"
    lowered = text.lower()
    if any(keyword in lowered for keyword in KEYWORDS):
        return "complex"
    return "simple"
