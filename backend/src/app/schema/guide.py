from pydantic import BaseModel, ConfigDict

from src.app.schema.quest import QuestRead


class GuideCreate(BaseModel):
    pass


class GuideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quests: list[QuestRead]
