from src.app.model.step import Step
from src.app.repository.step import StepRepository
from src.app.schema.step import StepCreate, StepUpdate


class StepNotFoundError(Exception):
    pass


class StepQuestNotFoundError(Exception):
    pass


class StepService:
    def __init__(self, repository: StepRepository) -> None:
        self.repository = repository

    async def create_step(self, quest_id: int, data: StepCreate) -> Step:
        await self._require_quest(quest_id)
        return await self.repository.create(quest_id, data)

    async def list_steps(self, quest_id: int) -> list[Step]:
        await self._require_quest(quest_id)
        return await self.repository.list(quest_id)

    async def update_step(
        self, quest_id: int, step_id: int, data: StepUpdate
    ) -> Step:
        step = await self._get_step(quest_id, step_id)
        return await self.repository.update(step, data)

    async def delete_step(self, quest_id: int, step_id: int) -> None:
        step = await self._get_step(quest_id, step_id)
        await self.repository.delete(step)

    async def _get_step(self, quest_id: int, step_id: int) -> Step:
        await self._require_quest(quest_id)
        step = await self.repository.get(quest_id, step_id)
        if step is None:
            raise StepNotFoundError(f"Step {step_id} was not found in quest {quest_id}")
        return step

    async def _require_quest(self, quest_id: int) -> None:
        if not await self.repository.quest_exists(quest_id):
            raise StepQuestNotFoundError(f"Quest {quest_id} was not found")
