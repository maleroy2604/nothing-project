from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.app.schema.quest import QuestRead


class GuideCreate(BaseModel):
    pass


class GuideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    quests: list[QuestRead]


class GuideUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_a_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self
