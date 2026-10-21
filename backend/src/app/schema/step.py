from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StepCreate(BaseModel):
    position: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    description: str = ""


class StepUpdate(BaseModel):
    position: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_a_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Fields cannot be null")
        return self


class StepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quest_id: int
    position: int
    title: str
    description: str
