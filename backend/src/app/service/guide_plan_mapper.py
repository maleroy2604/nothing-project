from src.app.schema.guide import GuideRead
from src.app.schema.guide_plan import GuidePlan
from src.app.schema.quest import QuestRead
from src.app.schema.step import StepRead


def quest_description(plan: GuidePlan, quest_index: int) -> str:
    quest = plan.quests[quest_index]
    parts = [quest.description]
    if quest.prerequisites:
        parts.append("Prerequisites:\n" + "\n".join(quest.prerequisites))
    parts.append(f"Estimated effort: {quest.estimated_hours} hours")

    if quest_index == 0:
        parts.extend(
            [
                f"Guide overview: {plan.description}",
                f"Difficulty: {plan.difficulty}",
                "Guide learning objectives:\n"
                + "\n".join(plan.learning_objectives),
            ]
        )

    return "\n\n".join(part for part in parts if part)


def to_review_guide(title: str, plan: GuidePlan) -> GuideRead:
    return GuideRead(
        id=1,
        title=title,
        board_column="backlog",
        quests=[
            QuestRead(
                id=quest_index + 1,
                guide_id=1,
                position=quest_index + 1,
                title=quest.title,
                description=quest_description(plan, quest_index),
                completion_criteria="\n".join(quest.completion_criteria),
                status="not_started",
                steps=[
                    StepRead(
                        id=step_index + 1,
                        quest_id=quest_index + 1,
                        position=step_index + 1,
                        title=f"Objective {step_index + 1}",
                        description=objective,
                    )
                    for step_index, objective in enumerate(quest.objectives)
                ],
            )
            for quest_index, quest in enumerate(plan.quests)
        ],
    )
