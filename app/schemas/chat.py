from pydantic import BaseModel, model_validator


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 1.0
    max_tokens: int | None = None
    stream: bool = False

    @model_validator(mode="after")
    def reject_streaming(self) -> "ChatCompletionRequest":
        if self.stream:
            raise ValueError("streaming completions are not supported")
        return self


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str = "chatcmpl-gateway"
    object: str = "chat.completion"
    choices: list[ChatCompletionChoice]
    cached: bool
    latency_ms: float
    provider: str
