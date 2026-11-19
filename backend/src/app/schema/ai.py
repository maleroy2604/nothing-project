from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from src.app.schema.guide import GuideRead


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    format: str | dict[str, Any] | None = None
    options: dict[str, Any] | None = None


class GuidePlanRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


class GuideGenerationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("title cannot be blank")
        return title


class GuideReviewRequest(BaseModel):
    original_request: str = Field(
        min_length=1,
        description="The user's request that the guide was created to satisfy.",
    )
    guide: GuideRead = Field(description="The generated guide to evaluate.")


class ChatResponse(BaseModel):
    model: str
    response: str
