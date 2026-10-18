from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

QuestStatus = Literal["not_started", "in_progress", "completed"]


class QuestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    status: QuestStatus = "not_started"


class QuestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    status: QuestStatus | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Fields cannot be null")
        return self


class QuestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: QuestStatus
