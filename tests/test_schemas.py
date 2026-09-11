from pydantic import ValidationError
import pytest

from app.schemas.chat import ChatCompletionRequest


def test_valid_chat_request_parses() -> None:
    body = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.2,
            "max_tokens": 64,
        }
    )
    assert body.messages[0].content == "hello"
    assert body.temperature == 0.2
    assert body.max_tokens == 64


def test_invalid_body_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate({"temperature": 0.2})


def test_stream_true_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "hello"}],
                "temperature": 0.2,
                "max_tokens": 16,
                "stream": True,
            }
        )
