from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.app.schema.step import StepCreate, StepRead

QuestStatus = Literal["not_started", "in_progress", "completed"]


class QuestCreate(BaseModel):
    guide_id: int = Field(gt=0)
    position: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    completion_criteria: str = Field(min_length=1)
    description: str = ""
    status: QuestStatus = "not_started"
    steps: list[StepCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_step_positions(self) -> Self:
        positions = [step.position for step in self.steps]
        if len(positions) != len(set(positions)):
            raise ValueError("Step positions must be unique within a quest")
        return self


class QuestUpdate(BaseModel):
    guide_id: int | None = Field(default=None, gt=0)
    position: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completion_criteria: str | None = Field(default=None, min_length=1)
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
    guide_id: int
    position: int
    title: str
    completion_criteria: str
    description: str
    status: QuestStatus
    steps: list[StepRead]
