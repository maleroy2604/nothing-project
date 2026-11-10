from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.app.schema.quest import QuestRead


class GuideCreate(BaseModel):
    pass


class GuideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    board_column: Literal["backlog", "daily", "weekly", "in_progress"]
    quests: list[QuestRead]


class GuideUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    board_column: Literal["backlog", "daily", "weekly", "in_progress"] | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        if "board_column" in self.model_fields_set and self.board_column is None:
            raise ValueError("board_column cannot be null")
        return self
