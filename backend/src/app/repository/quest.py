from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.model.quest import Quest
from src.app.schema.quest import QuestCreate, QuestUpdate


class QuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: QuestCreate) -> Quest:
        quest = Quest(**data.model_dump())
        self.session.add(quest)
        await self.session.commit()
        await self.session.refresh(quest)
        return quest

    async def get(self, quest_id: int) -> Quest | None:
        return await self.session.get(Quest, quest_id)

    async def list(self, offset: int = 0, limit: int = 100) -> list[Quest]:
        result = await self.session.scalars(
            select(Quest).order_by(Quest.id).offset(offset).limit(limit)
        )
        return list(result)

    async def update(self, quest: Quest, data: QuestUpdate) -> Quest:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(quest, field, value)
        await self.session.commit()
        await self.session.refresh(quest)
        return quest

    async def delete(self, quest: Quest) -> None:
        await self.session.delete(quest)
        await self.session.commit()
