from src.app.schema.guide_plan import GuidePlan
from src.app.service.ai import AIService


class GuideGenerationService:
    def __init__(self, ai_service: AIService | None = None) -> None:
        self.ai_service = ai_service if ai_service is not None else AIService()

    async def generate(
        self,
        topic: str,
        *,
        review_feedback: str | None = None,
        previous_plan: GuidePlan | None = None,
    ) -> GuidePlan:
        return await self.ai_service.generate_guide_plan(
            topic,
            review_feedback=review_feedback,
            previous_plan=previous_plan,
        )
