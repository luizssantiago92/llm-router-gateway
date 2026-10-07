from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.settings import (
    MAX_MAX_TOKENS,
    MAX_MESSAGE_CHARS,
    MAX_MESSAGES,
    MAX_TEMPERATURE,
    MAX_TOTAL_MESSAGE_CHARS,
    MIN_MAX_TOKENS,
    MIN_TEMPERATURE,
    Settings,
)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_MESSAGES)
    temperature: float | None = Field(None, ge=MIN_TEMPERATURE, le=MAX_TEMPERATURE)
    max_tokens: int | None = Field(None, ge=MIN_MAX_TOKENS, le=MAX_MAX_TOKENS)
    stream: bool = False

    @model_validator(mode="after")
    def reject_streaming(self) -> "ChatCompletionRequest":
        if self.stream:
            raise ValueError("streaming completions are not supported")
        return self

    @model_validator(mode="after")
    def limit_total_characters(self) -> "ChatCompletionRequest":
        total = sum(len(message.content) for message in self.messages)
        if total > MAX_TOTAL_MESSAGE_CHARS:
            raise ValueError(
                f"combined message content exceeds {MAX_TOTAL_MESSAGE_CHARS} characters"
            )
        return self


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class Usage(BaseModel):
    """Provider-reported token counts. Null means the provider did not report it."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str | None = None
    choices: list[ChatCompletionChoice]
    usage: Usage
    cached: bool
    latency_ms: int
    provider: str


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


def error_payload(
    message: str,
    error_type: str,
    *,
    param: str | None = None,
    code: str | None = None,
) -> dict[str, object]:
    return ErrorEnvelope(
        error=ErrorDetail(message=message, type=error_type, param=param, code=code)
    ).model_dump()


def configured_limit_reason(body: ChatCompletionRequest, settings: Settings) -> str | None:
    """Return why ``body`` violates a tightened setting, if it does.

    Field bounds are the built-in ceiling. Settings can only make those
    ceilings smaller, and this check applies that tighter value.
    """
    if len(body.messages) > settings.max_messages:
        return "too many messages"
    for message in body.messages:
        if len(message.content) > settings.max_message_chars:
            return "message content exceeds the configured limit"
    total = sum(len(message.content) for message in body.messages)
    if total > settings.max_total_message_chars:
        return "combined message content exceeds the configured limit"
    if body.temperature is not None and not (
        settings.min_temperature <= body.temperature <= settings.max_temperature
    ):
        return "temperature is outside the configured range"
    if body.max_tokens is not None and not (
        settings.min_max_tokens <= body.max_tokens <= settings.max_max_tokens
    ):
        return "max_tokens is outside the configured range"
    return None
