from pydantic import BaseModel, Field


class QuestPlan(BaseModel):
    title: str

    description: str

    objectives: list[str] = Field(
        min_length=2,
        max_length=5,
    )

    completion_criteria: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    prerequisites: list[str] = Field(
        default_factory=list,
    )

    estimated_hours: int = Field(
        ge=1,
        le=100,
    )


class GuidePlan(BaseModel):
    title: str
    description: str
    learning_objectives: list[str]
    difficulty: str
    quests: list[QuestPlan] = Field(
        min_length=1,
        max_length=15,
    )
