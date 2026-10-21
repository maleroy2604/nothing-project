from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.model.quest import Quest
from src.app.model.step import Step
from src.app.schema.step import StepCreate, StepUpdate


class StepRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, quest_id: int, data: StepCreate) -> Step:
        step = Step(quest_id=quest_id, **data.model_dump())
        self.session.add(step)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def get(self, quest_id: int, step_id: int) -> Step | None:
        result = await self.session.scalars(
            select(Step).where(Step.quest_id == quest_id, Step.id == step_id)
        )
        return result.one_or_none()

    async def list(self, quest_id: int) -> list[Step]:
        result = await self.session.scalars(
            select(Step)
            .where(Step.quest_id == quest_id)
            .order_by(Step.position, Step.id)
        )
        return list(result)

    async def quest_exists(self, quest_id: int) -> bool:
        return await self.session.get(Quest, quest_id) is not None

    async def update(self, step: Step, data: StepUpdate) -> Step:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(step, field, value)
        await self.session.commit()
        await self.session.refresh(step)
        return step

    async def delete(self, step: Step) -> None:
        await self.session.delete(step)
        await self.session.commit()
