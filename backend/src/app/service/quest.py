from src.app.model.quest import Quest
from src.app.repository.quest import QuestRepository
from src.app.schema.quest import QuestCreate, QuestUpdate


class QuestNotFoundError(Exception):
    pass


class QuestService:
    def __init__(self, repository: QuestRepository) -> None:
        self.repository = repository

    async def create_quest(self, data: QuestCreate) -> Quest:
        return await self.repository.create(data)

    async def get_quest(self, quest_id: int) -> Quest:
        quest = await self.repository.get(quest_id)
        if quest is None:
            raise QuestNotFoundError(f"Quest {quest_id} was not found")
        return quest

    async def list_quests(self, offset: int = 0, limit: int = 100) -> list[Quest]:
        return await self.repository.list(offset=offset, limit=limit)

    async def update_quest(self, quest_id: int, data: QuestUpdate) -> Quest:
        quest = await self.get_quest(quest_id)
        return await self.repository.update(quest, data)

    async def delete_quest(self, quest_id: int) -> None:
        quest = await self.get_quest(quest_id)
        await self.repository.delete(quest)
