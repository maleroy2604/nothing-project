from src.app.model.guide import Guide
from src.app.repository.guide import GuideRepository


class GuideNotFoundError(Exception):
    pass


class GuideService:
    def __init__(self, repository: GuideRepository) -> None:
        self.repository = repository

    async def create_guide(self) -> Guide:
        return await self.repository.create()

    async def get_guide(self, guide_id: int) -> Guide:
        guide = await self.repository.get(guide_id)
        if guide is None:
            raise GuideNotFoundError(f"Guide {guide_id} was not found")
        return guide

    async def list_guides(self, offset: int = 0, limit: int = 100) -> list[Guide]:
        return await self.repository.list(offset=offset, limit=limit)
