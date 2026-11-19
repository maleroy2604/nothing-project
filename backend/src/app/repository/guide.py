from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.model.guide import Guide
from src.app.model.quest import Quest
from src.app.model.step import Step
from src.app.schema.guide_plan import GuidePlan
from src.app.service.guide_plan_mapper import quest_description


class GuideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self) -> Guide:
        guide = Guide()
        self.session.add(guide)
        await self.session.flush()
        guide.title = f"Guide {guide.id}"
        await self.session.commit()
        created_guide = await self.get(guide.id)
        if created_guide is None:
            raise RuntimeError("Guide disappeared after it was created")
        return created_guide

    async def create_generated(self, title: str, plan: GuidePlan) -> Guide:
        guide = Guide(
            title=title,
            quests=[
                Quest(
                    position=quest_index + 1,
                    title=quest.title,
                    description=quest_description(plan, quest_index),
                    completion_criteria="\n".join(quest.completion_criteria),
                    steps=[
                        Step(
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
        self.session.add(guide)
        await self.session.commit()
        created_guide = await self.get(guide.id)
        if created_guide is None:
            raise RuntimeError("Guide disappeared after it was created")
        return created_guide

    async def update(
        self,
        guide: Guide,
        title: str | None = None,
        board_column: str | None = None,
    ) -> Guide:
        if title is not None:
            guide.title = title
        if board_column is not None:
            guide.board_column = board_column
        await self.session.commit()
        await self.session.refresh(guide)
        return guide

    async def delete(self, guide: Guide) -> None:
        await self.session.delete(guide)
        await self.session.commit()

    async def get(self, guide_id: int) -> Guide | None:
        result = await self.session.scalars(
            select(Guide)
            .options(selectinload(Guide.quests))
            .where(Guide.id == guide_id)
        )
        return result.one_or_none()

    async def list(self, offset: int = 0, limit: int = 100) -> list[Guide]:
        result = await self.session.scalars(
            select(Guide)
            .options(selectinload(Guide.quests))
            .order_by(Guide.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result)
