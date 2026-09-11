from app.routing.evaluator import classify


def test_short_prompt_is_simple() -> None:
    assert classify([{"role": "user", "content": "hello there"}], word_threshold=150) == "simple"


def test_word_count_above_threshold_is_complex() -> None:
    text = " ".join(["word"] * 151)
    assert classify([{"role": "user", "content": text}], word_threshold=150) == "complex"


def test_keyword_match_is_complex_case_insensitive() -> None:
    assert classify([{"role": "user", "content": "Please DEBUG this"}], word_threshold=150) == "complex"
    assert classify([{"role": "user", "content": "explain step by step"}], word_threshold=150) == "complex"
